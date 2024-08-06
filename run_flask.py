import os

from src.rest.hello import run_server

if __name__ == "__main__":
    port = str(os.getenv("PORT"))
    run_server(int(port))
