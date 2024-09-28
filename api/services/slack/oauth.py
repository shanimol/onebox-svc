import os
import secrets
from slack_sdk.oauth import AuthorizeUrlGenerator
from slack_sdk import WebClient
from utils.consts import (
    SLACK_CLIENT_ID,
    SLACK_CLIENT_SECRET,
    SLACK_REDIRECT_URI,
    SLACK_BOT_TOKEN,
)
from datetime import datetime
from services.user import user as user_repo
from services.messages import messages as message_repo

def slack_oauth():
    # Step 1: Create a Slack app at https://api.slack.com/apps and get Client ID, Secret
    state = secrets.token_urlsafe(16)

    # Step 2: Generate Authorization URL
    auth_url_generator = AuthorizeUrlGenerator(
        client_id=SLACK_CLIENT_ID,
        user_scopes=[
            "im:read",
            "im:history",
            "mpim:read",
            "mpim:history",
            "groups:read",
            "groups:history",
            "channels:read",
            "channels:history",
        ],
        scopes=[
            "channels:read",
            "chat:write",
            "groups:read",
            "im:read",
            "im:history",
            "mpim:read",
            "mpim:history",
            "users.profile:read",
            "users:read",
            "users:read.email",
        ],
        redirect_uri=SLACK_REDIRECT_URI,
    )

    # Generate URL and state for authentication
    authorization_url = auth_url_generator.generate(state=state)
    return authorization_url


async def slack_redirect(code, state):
    client = WebClient(token=SLACK_BOT_TOKEN)
    conversation_id = None

    result = client.oauth_v2_access(
        client_id=SLACK_CLIENT_ID, client_secret=SLACK_CLIENT_SECRET, code=code
    )
    user_slack_id = result.get("authed_user").get("id")
    access_token = result.get("authed_user").get("access_token")

    user_client = WebClient(token=access_token)

    im_list = []
    mpim_list = []
    private_channel_list = []
    public_channel_list = []

    for result in user_client.conversations_list(types="im", limit=5):
        if conversation_id is not None:
            break
        for channel in result["channels"]:
            if channel.get("is_archived") == False:
                im_list.append(
                    {"channel_id": channel["id"], "user_id": channel["user"]}
                )

    for result in user_client.conversations_list(types="mpim", limit=5):
        if conversation_id is not None:
            break
        for channel in result["channels"]:
            if channel.get("is_archived") == False:
                mpim_list.append(
                    {"channel_id": channel["id"], "user_id": channel["creator"]}
                )

    for result in user_client.conversations_list(types="private_channel", limit=5):
        if conversation_id is not None:
            break
        for channel in result["channels"]:
            if channel.get("is_archived") == False:
                private_channel_list.append({"channel_id": channel["id"]})

    # for result in user_client.conversations_list(types="public_channel", limit=5):
    #     if conversation_id is not None:
    #         break
    #     for channel in result["channels"]:
    #         if channel.get("is_archived") == False:
    #             public_channel_list.append({"channel_id": channel["id"]})

    user_slack_ids = []
    user_slack_ids.append(user_slack_id)
    mpimRes = {}
    imRes = {}
    privateRes = {}

    for mpim in mpim_list:
        result = user_client.conversations_history(channel=mpim["channel_id"], limit=90)
        mpimRes[mpim["channel_id"]] = result
        for conversation in result["messages"]:
            user = conversation.get("user", "")
            if user == "":
                continue
            user_slack_ids.append(user)

    for im in im_list:
        result = user_client.conversations_history(channel=im["channel_id"], limit=90)
        imRes[im["channel_id"]] = result
        for conversation in result["messages"]:
            user = conversation.get("user", "")
            if user == "":
                continue
            user_slack_ids.append(user)

    for private_channel in private_channel_list:
        result = user_client.conversations_history(
            channel=private_channel["channel_id"], limit=90
        )
        privateRes[private_channel["channel_id"]] = result
        for conversation in result["messages"]:
            user = conversation.get("user", "")
            if user == "":
                continue
            user_slack_ids.append(user)

    users = await user_repo.bulk_get_user_by_slack_id(user_slack_ids)

    userSlackMap = {}

    for user in users:
        userSlackMap[user.slack_id] = user.id

    db_input = []
    for mpim in mpim_list:
        result = mpimRes[mpim["channel_id"]]
        mpim_data = {}
        for conversation in result["messages"]:
            sender_id = userSlackMap.get(conversation["user"], "")
            reciever_id = userSlackMap.get(user_slack_id, "")
            if sender_id == "" or reciever_id == "":
                continue
            mpim_data["channel_id"] = mpim["channel_id"]
            mpim_data["sender_id"] = userSlackMap.get(conversation["user"])
            mpim_data["body"] = conversation["text"]
            mpim_data["user_id"] = userSlackMap[user_slack_id]
            mpim_data["date"] = datetime.now()
            mpim_data["message_id"] = conversation["client_msg_id"]
            mpim_data["source"] = "SLACK"
            db_input.append(mpim_data)

    for im in im_list:
        result = imRes[im["channel_id"]]
        im_data = {}
        for conversation in result["messages"]:
            print(conversation)
            sender_id = userSlackMap.get(conversation.get("user", ""), "")
            reciever_id = userSlackMap.get(user_slack_id, "")
            message_id = conversation.get("client_msg_id", "")
            if sender_id == "" or reciever_id == "" or message_id == "":
                continue
            im_data["channel_id"] = im["channel_id"]
            im_data["sender_id"] = userSlackMap.get(conversation["user"])
            im_data["body"] = conversation["text"]
            im_data["user_id"] = userSlackMap[user_slack_id]
            im_data["date"] = datetime.now()
            im_data["message_id"] = message_id
            im_data["source"] = "SLACK"
            db_input.append(im_data)

    for private_channel in private_channel_list:
        result = privateRes[private_channel["channel_id"]]
        im_data = {}
        for conversation in result["messages"]:
            sender_id = userSlackMap.get(conversation.get("user", ""), "")
            reciever_id = userSlackMap.get(user_slack_id, "")
            message_id = conversation.get("client_msg_id", "")
            if sender_id == "" or reciever_id == "" or message_id == "":
                continue
            im_data["channel_id"] = private_channel["channel_id"]
            im_data["sender_id"] = userSlackMap.get(conversation["user"])
            im_data["body"] = conversation["text"]
            im_data["user_id"] = userSlackMap[user_slack_id]
            im_data["date"] = datetime.now()
            im_data["message_id"] = message_id
            im_data["source"] = "SLACK"
            db_input.append(im_data)

    
    result = await message_repo.create_message(db_input)
    print(result)
    # result = client.conversations_history(
    #     channel="D07PZTNKHNC",
    #     inclusive=True,
    #     oldest="1610144875.000600",
    #     limit=1
    # )

    # # message = result["messages"][0]
    # # Print message text
    # print(result["messages"])
