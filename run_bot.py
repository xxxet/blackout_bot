import os

from src.tg.outage_bot import main

if __name__ == "__main__":
    token = str(os.getenv("TOKEN"))
    main(token)
