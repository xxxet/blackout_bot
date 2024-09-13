from datetime import datetime
from typing import Optional, Union, Any

from telegram._utils.types import JSONDict
from telegram.ext._utils.types import JobCallback, CCT


class Job:
    def __init__(self, next_run_time: Union[float, datetime]):
        self.next_run_time = next_run_time


class MockBot:
    sent_messages: list[Any] = []

    async def send_message(self, chat_id: int, text: str) -> None:
        self.sent_messages.append({"chat_id": chat_id, "text": text})


class MockContext:
    def __init__(self, bot: MockBot):
        self.bot = bot
        self.job_queue = MockJobQueue(bot)


class MockJob:
    def __init__(
        self,
        name: Optional[str],
        data: Optional[object],
        chat_id: Optional[int],
        when: Union[float, datetime],
    ):
        self.removed = False
        self.job = Job(when)
        self.name = name
        self.data = data
        self.chat_id = chat_id

    def schedule_removal(self) -> None:
        self.removed = True


class MockJobQueue:
    def __init__(self, bot: MockBot):
        self.bot = bot
        self.jobs: list[MockJob] = []

    def run_once(
        self,
        callback: JobCallback[CCT],
        when: Union[float, datetime],
        data: Optional[object] = None,
        name: Optional[str] = None,
        chat_id: Optional[int] = None,
        user_id: Optional[int] = None,
        job_kwargs: Optional[JSONDict] = None,
    ) -> MockJob:
        job = MockJob(name=name, data=data, when=when, chat_id=chat_id)
        self.jobs.append(job)
        return job

    def get_jobs_by_name(self, name: str) -> list[MockJob]:
        return list(filter(lambda job: job.name == name, self.jobs))
