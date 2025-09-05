import inspect
from collections import deque
from typing import Any, Callable, Deque, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple, Type, Union

from .message import MessageType, Command, Event
from .unit_of_work import AbstractUnitOfWork, AsyncAbstractUnitOfWork


EventHandler = Callable[..., Any]
CommandHandler = Callable[..., Any]


class MessageBus:
    def __init__(
        self,
        *,
        uow: AbstractUnitOfWork,
        event_handlers: Mapping[Type[Event], Sequence[EventHandler]] | None = None,
        command_handlers: Mapping[Type[Command], CommandHandler] | None = None,
        dependencies: Mapping[str, Any] | None = None,
        raise_on_error: bool = False,
    ) -> None:
        self.uow = uow
        self.event_handlers: Dict[Type[Event], List[EventHandler]] = {
            **{k: list(v) for k, v in (event_handlers or {}).items()}
        }
        self.command_handlers: Dict[Type[Command], CommandHandler] = {
            **(command_handlers or {})
        }
        self.dependencies: Dict[str, Any] = {"uow": self.uow, **(dependencies or {})}
        self.raise_on_error = raise_on_error

    def register_event_handler(self, event_type: Type[Event], handler: EventHandler) -> None:
        self.event_handlers.setdefault(event_type, []).append(handler)

    def register_command_handler(self, command_type: Type[Command], handler: CommandHandler) -> None:
        self.command_handlers[command_type] = handler

    def handle(self, message: MessageType) -> List[Any]:
        results: List[Any] = []
        queue: Deque[MessageType] = deque([message])

        while queue:
            msg = queue.popleft()
            if isinstance(msg, Event):
                self._handle_event(msg, queue)
            elif isinstance(msg, Command):
                result = self._handle_command(msg, queue)
                results.append(result)
            else:
                if self.raise_on_error:
                    raise TypeError(f"Unsupported message type: {type(msg)}")
            for evt in self.uow.collect_new_events():
                queue.append(evt)
        return results

    def _handle_event(self, event: Event, queue: Deque[MessageType]) -> None:
        handlers = self.event_handlers.get(type(event), [])
        for handler in handlers:
            try:
                handler(**self._build_kwargs(handler, event))
            except Exception:
                if self.raise_on_error:
                    raise

    def _handle_command(self, command: Command, queue: Deque[MessageType]) -> Any:
        handler = self.command_handlers.get(type(command))
        if handler is None:
            if self.raise_on_error:
                raise KeyError(f"No command handler registered for {type(command)}")
            return None
        try:
            return handler(**self._build_kwargs(handler, command))
        except Exception:
            if self.raise_on_error:
                raise
            return None

    def _build_kwargs(self, func: Callable[..., Any], message: MessageType) -> Dict[str, Any]:
        sig = inspect.signature(func)
        kwargs: Dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if name in self.dependencies:
                kwargs[name] = self.dependencies[name]
            else:
                kwargs[name] = message
        return kwargs


class AsyncMessageBus:
    def __init__(
        self,
        *,
        uow: AsyncAbstractUnitOfWork,
        event_handlers: Mapping[Type[Event], Sequence[EventHandler]] | None = None,
        command_handlers: Mapping[Type[Command], Sequence[CommandHandler]] | None = None,
        dependencies: Mapping[str, Any] | None = None,
        raise_on_error: bool = False
    ) -> None:
        self.uow = uow
        self.event_handlers = {**{k: list(v) for k, v in (event_handlers or {}).items()}}
        self.command_handlers = {**(command_handlers or {})}
        self.dependencies = {"uow": self.uow, **(dependencies or {})}
        self.raise_on_error = raise_on_error

    async def handle(self, message: MessageType) -> List[Any]:
        results: List[Any] = []
        queue: Deque[MessageType] = deque([message])
        
        while queue:
            msg = queue.popleft()
            if isinstance(msg, Event):
                await self._handle_event(msg)
            elif isinstance(msg, Command):
                result = self._handle_command(msg)
                results.append(result)
            else:
                if self.raise_on_error:
                    raise TypeError(f"Unsupported message type: {type(msg)}")
            for evt in self.uow.collect_new_events():
                queue.append(evt)

    async def _awaitable(self, func: Callable, **kwargs):
        val = func(**kwargs)
        if inspect.isawaitable(val):
            return await val
        return val

    async def _build_kwargs(self, func: Callable[..., Any], message: MessageType) -> Dict[str, Any]:
        sig = inspect.signature(func)
        kwargs: Dict[str, Any] = {}
        for name, param in sig.parameters.items():
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue
            if name in self.dependencies:
                kwargs[name] = self.dependencies.get(name)
            else:
                kwargs[name] = message
        return kwargs

    async def _handle_event(self, event: Event) -> None:
        for handler in self.event_handlers.get(type(event), []):
            try:
                await self._awaitable(handler, **self._build_kwargs(handler, event))
            except Exception:
                if self.raise_on_error:
                    raise
                return None

    async def _handle_command(self, command: Command) -> None:
        handler = self.command_handlers.get(type(command))
        if not handler:
            if self.raise_on_error:
                raise KeyError(f"No command handler registered for {type(command)}")
            return None
        try:
            return await self._awaitable(handler, **self._build_kwargs(handler, command))
        except Exception:
            if self.raise_on_error:
                raise
            return None
