from abc import ABC
from typing import List, Iterable
from .message import Event


class AbstractAggregate(ABC):
    def __init__(self) -> None:
        self.events: List[Event] = []

    def _record_event(self, event: Event) -> None:
        self.events.append(event)

    def pull_events(self) -> Iterable[Event]:
        event_tpl = tuple(self.events)
        self.events.clear()
        return event_tpl
