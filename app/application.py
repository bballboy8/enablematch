##prospect_app
import uvicorn
import os


def app(scope, receive, send):
    ...


if __name__ == "__main__":
    uvicorn.run(
        "main:project",
        host= "localhost",
        port= int(os.environ.get("PORT", 8006 )),
        reload=True,
        log_level="info",
        env_file=".env",
    )
