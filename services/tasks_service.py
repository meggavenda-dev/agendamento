from __future__ import annotations

from db import tasks


def create_task(payload: dict):
    return tasks.create(payload)


def complete_task(task_id: int):
    return tasks.update(task_id, {"status": "Concluída"})
