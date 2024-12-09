# FastAPI EnableMatch-backend

This project is built using Python and requires Docker to run. It utilizes UVicorn as the ASGI server.

## Prerequisites

Docker installed on your system..

## Running the Project

Follow these steps to run the project:

## Clone the Repository:

```
git clone https://github.com/bballboy8/enablematch
cd project
```

1. Create virtual environment : virtualenv venv --python=python3.12
2. Install requirements : pip install -r requirements.txt
3. add .env: touch .env
4. Run the application: python app/application.py


Optional

## Build the Docker Image:

```
docker build -t project .
```

## Run the Docker Container:

```
docker run -d -p 80:80 project
```

This command will start the Docker container in detached mode, exposing port 80 of the container to port 80 on your local machine.

## Access the Application:

Once the container is running, you can access the application by opening your web browser and navigating to http://localhost

## Environment Variables

you should have app/.env file with all environment variable needed or you can set them

NAME: You can set this environment variable to customize the name displayed by the application. By default, it's set to "World".

```
docker run -d -p 80:80 -e NAME="Your Name" project
```

## Stopping the Application

To stop the running Docker container, you can use the following command:

```
docker stop $(docker ps -q --filter ancestor=project)
```

## Format code
```bash
ruff --output-format=github .  
```
