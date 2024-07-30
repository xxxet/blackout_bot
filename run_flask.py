import argparse

from src.rest.hello import run_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--port", help="flask port")
    args = parser.parse_args()
    config = vars(args)
    run_server(int(str(config.get("port"))))
