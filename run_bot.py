import argparse
import os

from src.tg.outage_bot import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bot params", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--token", help="Bot token")
    args = parser.parse_args()
    config = vars(args)
    token = str(config.get("token"))
    print("token param: " + token)
    if len(token) == 0:
        token = str(os.getenv("TOKEN"))
    print("token after getenv: " + token)
    main(token)
