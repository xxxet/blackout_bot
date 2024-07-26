import argparse

from src.tg.outage_bot import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bot params", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # parser.add_argument("--group", help="Group table path")
    parser.add_argument("--token", help="Bot token")
    args = parser.parse_args()
    config = vars(args)
    main(config.get("token"))
