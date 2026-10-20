from __future__ import annotations
class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list] = {}
        self.log: list[dict] = []
    def subscribe(self, topic: str, fn) -> None:
        self._subs.setdefault(topic, []).append(fn)
    def publish(self, topic: str, payload: dict) -> None:
        self.log.append({'topic': topic, 'payload': payload})
        for fn in self._subs.get(topic, []):
            fn(payload)
