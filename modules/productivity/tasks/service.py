from __future__ import annotations
class TaskService:
    def add(self, title: str, due: str = '') -> dict:
        raise NotImplementedError
    def list(self) -> list[dict]:
        raise NotImplementedError
    def complete(self, task_id: int) -> dict:
        raise NotImplementedError
class MockTaskService(TaskService):
    def __init__(self) -> None:
        self._t: list[dict] = []
        self._n = 0
    def add(self, title: str, due: str = '') -> dict:
        self._n += 1
        d = {'id': self._n, 'title': title, 'due': due, 'done': False}
        self._t.append(d)
        return d
    def list(self) -> list[dict]:
        return list(self._t)
    def complete(self, task_id: int) -> dict:
        for x in self._t:
            if x['id'] == task_id:
                x['done'] = True
                return x
        raise KeyError('task not found')
