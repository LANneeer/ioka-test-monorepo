from typing import Protocol, Union


class Message(Protocol):
    pass


class Command(Message):
    pass

class Event(Message):
    pass

MessageType = Union[Command, Event]
