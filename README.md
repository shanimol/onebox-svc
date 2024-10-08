### Prerequisites and Setup

Before starting with the setup process, ensure that you have the following prerequisites installed on your system:

1. **[Git](https://git-scm.com/)**
2. **[Python](https://www.python.org/)**
3. **[PIP](https://pypi.org/project/pip/)**
4. **[Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)**
5. **venv ([Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html#introduction))**

#### Installation Steps:

1. **Create Parent Folder:**
   Create a parent folder where all the project files will be stored.

2. **Clone boilerplate Repository:**
   Clone the boilerplate repository from GitHub into the parent folder using the following command:
   ```
   https://github.com/reenphygeorge/fastapi-boilerplate.git
   ```


3. **Setup Python Virtual Environment:**
   - Install the venv module (Python Virtual Environment) into the parent folder:
     ```
     python -m venv env
     ```
   - Activate the virtual environment:
     - For Linux/Mac:
       ```
       source env/bin/activate
       ```
     - For Windows:
       ```
       .\env\Scripts\activate
       ```

4. **Navigate to API Folder:**
   - Open your terminal or command prompt.
   - Use the `cd` command to navigate into the API folder within the cloned repository:
     ```
     cd fastapi-boilerplate/api
     ```


5. **Install Python Requirements:**
   - Ensure that the virtual environment is active.
   - Install the required Python packages and dependencies listed in `requirements.txt`:
     ```
     pip install -r requirements.txt
     ```

6. **Start Docker Containers:**
   - Ensure Docker and Docker Compose are installed and running.
   - Navigate back to the parent folder.
   - Start the Docker containers using Docker Compose:
     ```
     docker compose up
     ```
   - This command will start the PostgreSQL database, Redis, and the admin panel NocoDB.

7. **Setup Database Structure:**
   - Once the Docker containers are running, open a new terminal window/tab.
   - Navigate back to the `api` directory within the cloned repository.
   - Run the following command to setup the database structure:
     ```
     prisma migrate dev --schema=prisma/schema.prisma
     ```

8. **Start API Server:**
   - Now that the Docker containers and database structure are set up, start the API server:
     ```
     uvicorn main:app --reload
     ```

With the API server and UI running, you can now start using the service for your video analysis needs.
