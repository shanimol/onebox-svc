import os
import json
from dotenv import dotenv_values, find_dotenv
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import traceable
from services.messages import messages as messages_repo
from dotenv import load_dotenv

bot = None 

async def getengine():
    msgs = await messages_repo.get_all_messages()
    serialized_data = [
            {
                **task.dict(),
                "date": task.created_at.isoformat(),
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
            }
            for task in msgs
        ]
    
    for d in serialized_data:
        d.pop("message_id", None)
    global bot
    if bot == None:
        bot = RAGChatBot(messages=serialized_data)
        return bot
    else:
        return bot
        
def get_environment_variable(key: str, default: str = "", value_type: type = str) -> any:
    """
    Get the environment variable value for the specified key.
    :param key: The key of the environment variable.
    :param default: The default value to return if the environment variable is not set.
    :param value_type: The type to cast the environment variable value to.
    :return: The casted value of the environment variable.
    """
    try:
        dotenv_path = find_dotenv()
        env_vars = dotenv_values(dotenv_path)

        os.environ.update(env_vars)

        env_value = os.getenv(key, default)

        if env_value is None or env_value == "":
            return default

        return value_type(env_value)
    except (ValueError, TypeError, Exception):
        return default

load_dotenv()
api_key = get_environment_variable("OPENAI_API_KEY")
qdrnt_api_key = get_environment_variable("QDRANT_API_KEY")
qdrnt_host = get_environment_variable("QDRNT_HOST")


# Define a class for the chatbot with RAG-based memory
class RAGChatBot:
    def __init__(self, messages):
        # Load OpenAI API key from environment variables
        self.api_key = api_key
        self.llm = ChatOpenAI(openai_api_key=self.api_key, temperature=0.5, model="gpt-4o-mini")
        
        QDRANT_HOST = qdrnt_host  # Replace with your remote Qdrant IP or URL
        QDRANT_PORT = 6333  # Default port for Qdrant
        QDRANT_API_KEY = qdrnt_api_key  # Optional, needed if using Qdrant Cloud

        # Initialize Qdrant client for remote connection (with or without an API key)
        self.qdrant_client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            api_key=QDRANT_API_KEY  # Only needed if using Qdrant Cloud or secured instance
        )

        # Create a Qdrant collection (only need to run once)
        self.qdrant_client.recreate_collection(
            collection_name="my_collection",
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)  # Vector size for text-embedding-ada-002 is 1536
)
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
        
        self.data = messages
        
        chunks = self.create_vector_store(self.data)
        
        self.vector_store = Qdrant(
            client=self.qdrant_client,
            collection_name="my_collection",
            embeddings=self.embeddings
        )

        # Store the chunks in Qdrant
        self.vector_store.add_texts(texts=chunks)
        
        # Convert email data to FAISS-compatible format
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        # Setup a ConversationalRetrievalChain for question-answering
        self.retrieval_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(),
            memory=self.memory
        )

    def split_large_text(self, text, chunk_size=1000, chunk_overlap=200):
        """
        Split a large text into smaller chunks using RecursiveCharacterTextSplitter.
        Adjust chunk_size and chunk_overlap for optimal splitting.
        """
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return text_splitter.split_text(text)

    def create_vector_store(self, data):
        string_data = json.dumps(data)
        chunks = self.split_large_text(string_data)

        return chunks


    @traceable
    def ask_question(self, question):
        chat_template = ChatPromptTemplate.from_messages(
            [
                ("system", """
                                You are a retrieval-based assistant with access to meeting transcripts, mail threads, and Slack messages. Your task is to retrieve information strictly from the provided context. You are NOT allowed to generate new content on your own.

                                The user will provide queries such as searching for conversations by date, context, or person, summarizing meetings, or listing important points from conversations.

                                Respond according to the following rules:
                                1. **Strictly use the context from the retrieved information** (RAG data). Do NOT create any content that is not in the context.
                                2. Always return the output in **JSON format** in curly braces with no other extra data with the following keys:
                                - `result`: The main result based strictly on the retrieved context. This could be a summary, search result, or important points.
                                - `message_id`: If the user is searching for a conversation and the retrieved context contains a relevant `message_id`, include it here. Otherwise, do not add this key.

                                3. If the query is about a conversation (search by date, context, or person), return the most relevant conversation from the context with the corresponding `message_id` if available.
                                4. If the query is about summarizing a meeting or listing important points, summarize based strictly on the retrieved context.
                                5. Always ensure the result is factual and derived strictly from the given context.
                                6. Return detailed information and use bullet points where necessary if the user prompt requires a detailed response.
                                7. If the question is out of context or if you are unclear about a response, DO NOT generate new content. Instead let the user know about the lack of context in a polite manner.
                                8. If the user asks to prep them or provide summary, fetch details from context and give them a detailed result with relevant data
                                
                                Example output:
                                (
                                    "result": "The most relevant conversation happened on March 2nd, 2023.",
                                    "message_id": "1234567890"
                                )

                                
                                Context: {context}
                                """),
                ("human", "{user_input}"),
            ]
        )
        
        # Retrieve relevant context (documents) from FAISS using the retrieval chain
        retrieval_result = self.retrieval_chain({"question": question})

        # Extract the relevant context based on the structure
        if "answer" in retrieval_result:
            # If the answer field contains the relevant context
            context = retrieval_result["answer"]
        elif "chat_history" in retrieval_result:
            # If chat history is relevant, extract the last AIMessage (if needed)
            context = retrieval_result["chat_history"][-1].content
        else:
            context = "No relevant context found."
        
            # Format the custom prompt with the retrieved context and user input
        messages = chat_template.format_messages(context=context, user_input=question)
    
        # Use the LLM to generate a response based on the formatted prompt
        response = self.llm(messages)
        return response

    @traceable
    def generate_action_points(self, input):
            chat_template = ChatPromptTemplate.from_messages(
                [
                    ("system", """
                                    You are a task extraction assistant with access to multiple messages or emails. Your role is to extract concise and relevant action points from these messages. You must follow the strict rules below and format your output accordingly.

                                    **Rules**:
                                    1. **Strictly use the provided context** (retrieved messages or emails). Do NOT generate additional content that is not directly available in the context.
                                    2. For each message or email, extract any relevant **action points** and provide them in a concise format.
                                    3. **Include any date information** associated with the action points if available.
                                    4. Assign an integer priority to each action point or message based on the provided context. Each message must be assigned an **integer priority**, between 1 and 10 where 1 is the highest priority and 10 is the lowest priority and decreases with higher integer values.
                                        - **Tone of the message**: Detect if the tone of the message indicates urgency (e.g., use of words like "urgent," "ASAP," "immediately").
                                        - **Urgency**: Keywords such as "deadline," "today," "by the end of the day" should increase the priority of the message.
                                    5. The result must be strictly in **JSON format** in curly braces with no other extra data. Each action point must include the following non-nullable keys:
                                    - `"message_id"`: The ID of the message or email from which the action point was extracted.
                                    - `"action_point"`: The action point itself, described concisely.
                                    - `"assigner"`: The person who assigned the task, which corresponds to the sender of the message or email.
                                    - `"priority"`: Use tone and urgency in the message to define an integer priority.
                                    6. Nullable fields:
                                    - `"summary"`: The summary of the message IF ONLY the message is over 100 characters long.

                                    7. The response should contain one JSON object per action point extracted from the input.

                                    8. Each JSON objects whould be comma seporated and should be enclosed in a list.

                                    9. The output should ALWAYS be a valid JSON string.
                                    
                                    Example output:
                                    (
                                        "action_point": "Update todo list for migration.",
                                        "message_id": "1234567890"
                                        "assigner": "John Doe"
                                        "priority": 1
                                    )                                 

                                    """),
                    ("human", "{user_input}"),
                ]
            )        
            
            # Format the custom prompt with the retrieved context and user input
            messages = chat_template.format_messages(user_input=input)
        
            # Use the LLM to generate a response based on the formatted prompt
            response = self.llm(messages)
            return response

    @traceable        
    def define_priority(self, input):
        chat_template = ChatPromptTemplate.from_messages(
            [
                ("system", """
                                You are a priority assignment assistant. Your task is to assign an integer priority to each action point or message based on the provided context. 

                                **Attributes to consider**:
                                1. **Time difference**: Calculate the time difference between the sender’s message and the user’s current query. More recent messages may have higher priority.
                                2. **Frequency of messages**: If the sender has sent multiple messages within a short period, it might indicate a higher priority.
                                3. **Tone of the message**: Detect if the tone of the message indicates urgency (e.g., use of words like "urgent," "ASAP," "immediately").
                                4. **Urgency**: Keywords such as "deadline," "today," "by the end of the day" should increase the priority of the message.

                                **Rules**:
                                1. Each message must be assigned an **integer priority**, where 1 is the highest priority and decreases with higher integer values. Generate integer priority for each element in sequential order only
                                2. The result must be strictly in **JSON format** in curly braces with no other extra data. Each entry must include:
                                    - `"message_id"`: The unique identifier of the message.
                                    - `"action_point"`: A brief description of the action point or task extracted from the message.
                                    - `"priority"`: An integer priority value.
                                    
                                Example output:
                                (
                                    "action_point": "Update todo list for migration.",
                                    "message_id": "1234567890"
                                    "priority": 1
                                ) 
                                
                                Context: {context}
                                """),
                ("human", "{user_input}"),
            ]
        )
        
            # Retrieve relevant context (documents) from FAISS using the retrieval chain
        retrieval_result = self.retrieval_chain({"question": input})

        # Extract the relevant context based on the structure
        if "answer" in retrieval_result:
            # If the answer field contains the relevant context
            context = retrieval_result["answer"]
        elif "chat_history" in retrieval_result:
            # If chat history is relevant, extract the last AIMessage (if needed)
            context = retrieval_result["chat_history"][-1].content
        else:
            context = "No relevant context found."
        
        # Format the custom prompt with the retrieved context and user input
        messages = chat_template.format_messages(context=context, user_input=input)
    
        # Use the LLM to generate a response based on the formatted prompt
        response = self.llm(messages)
        return response
    
    @traceable        
    def summarize_message(self, input):
        chat_template = ChatPromptTemplate.from_messages(
            [
                ("system", """
                                You are a message summarizer with access to multiple messages or emails. Your role is to extract concise and relevant summary points from these messages. You must follow the strict rules below and format your output accordingly.

                                **Rules**:
                                1. **Strictly use the provided context** (retrieved messages or emails). Do NOT generate additional content that is not directly available in the context.
                                2. For each message or email, extract a relevant summary and provide them in a concise format no more than one sentence.
                                3. The result must be strictly in **JSON format** in curly braces with no other extra data. Each entry must include the following non-nullable keys:
                                - `"message_id"`: The ID of the message or email from which the action point was extracted.
                                - `"summary"`: The summary of the message in no more than 50 characters

                                5. The response should contain one JSON object per summary extracted from the input.
                                
                                Example output:
                                (.",
                                    "message_id": "1234567890"
                                    "summary": "John Invited you to a sales meeting
                                ) 
                                """),
                ("human", "{user_input}"),
            ]
        )
        
        # Retrieve relevant context (documents) from FAISS using the retrieval chain
        # Format the custom prompt with the retrieved context and user input
        messages = chat_template.format_messages(user_input=input)
    
        # Use the LLM to generate a response based on the formatted prompt
        response = self.llm(messages)
        return response
