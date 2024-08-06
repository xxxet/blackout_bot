import argparse
import os

from src.rest.hello import run_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--port", help="flask port")
    args = parser.parse_args()
    config = vars(args)
    port = str(config.get("port"))
    if len(port) == 0:
        port = str(os.getenv("PORT"))
    run_server(int(port))
