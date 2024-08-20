from dataclasses import dataclass
from datetime import datetime

import config


@dataclass
class RemindObj:
    group: str
    old_zone: str
    new_zone: str
    remind_time: datetime
    change_time: datetime
    notify_now: bool

    def get_msg(self) -> str:
        return (
            f"{self.group} changes to {self.symbol(self.new_zone)}:\n"
            f"Zone is going to change from {self.old_zone} {self.symbol(self.old_zone)}"
            f"to {self.new_zone}  {self.symbol(self.new_zone)} at {self.change_time.strftime("%H:%M")}"
        )

    @staticmethod
    def symbol(zone: str) -> str:
        match zone:
            case config.BLACK_ZONE:
                return "🌚"
            case config.WHITE_ZONE:
                return "💡"
            case config.GREY_ZONE:
                return "🌥"
            case _:
                return ""
