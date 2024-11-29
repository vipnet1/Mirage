import asyncio
import logging


class TaskManager:
    tasks_queue: dict[str, list[str]] = {}

    @staticmethod
    async def wait_for_turn(group: str, name: str) -> None:
        if group not in TaskManager.tasks_queue:
            TaskManager.tasks_queue[group] = []

        TaskManager.tasks_queue[group].append(name)
        while True:
            if TaskManager.tasks_queue[group][0] == name:
                logging.info('Task Manager - can execute task "%s"', name)
                return

            await asyncio.sleep(1)

    @staticmethod
    def finish_turn(group: str) -> None:
        TaskManager.tasks_queue[group].pop(0)
