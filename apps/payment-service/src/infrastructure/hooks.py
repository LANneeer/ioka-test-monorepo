import time
from prometheus_client import Counter, Histogram
from typing import Any
from patterns.observability import ObservabilityHook
from patterns.message import Command, Event
from src.infrastructure.logging import audit_log, get_request_id, logging

log = logging.getLogger("obs")

CMD_CNT = Counter("bus_commands_total", "Commands processed", ["name","status"])
CMD_LAT = Histogram("bus_command_duration_seconds", "Command latency", ["name","status"])
EVT_CNT = Counter("bus_events_total", "Events processed", ["name","status"])
EVT_LAT = Histogram("bus_event_duration_seconds", "Event latency", ["name","status"])
UOW_CNT = Counter("uow_total", "UoW commits/rollbacks", ["action"])

class PromAuditHook(ObservabilityHook):
    def __init__(self) -> None:
        self._cmd_started_at: dict[int, float] = {}
        self._evt_started_at: dict[int, float] = {}

    async def on_command_start(self, cmd: Command) -> None:
        key = id(cmd); self._cmd_started_at[key] = time.perf_counter()
        name = type(cmd).__name__
        log.info("cmd.start", extra={"request_id": get_request_id(), "audit": {"type": "cmd.start", "name": name}})
        audit_log(action=f"cmd.{name}.start", actor_id=None, target=None, status="success", meta={})

    async def on_command_end(self, cmd: Command, result: Any | None) -> None:
        key = id(cmd); start = self._cmd_started_at.pop(key, time.perf_counter())
        dur = time.perf_counter() - start
        name = type(cmd).__name__
        CMD_CNT.labels(name, "ok").inc()
        CMD_LAT.labels(name, "ok").observe(dur)
        log.info("cmd.end", extra={"request_id": get_request_id(), "audit": {"type":"cmd.end","name": name, "duration": dur}})
        audit_log(action=f"cmd.{name}.end", actor_id=None, target=None, status="success", meta={"duration": dur})

    async def on_command_error(self, cmd: Command, err: BaseException) -> None:
        key = id(cmd); start = self._cmd_started_at.pop(key, time.perf_counter())
        dur = time.perf_counter() - start
        name = type(cmd).__name__
        CMD_CNT.labels(name, "error").inc()
        CMD_LAT.labels(name, "error").observe(dur)
        log.exception("cmd.error", extra={"request_id": get_request_id(), "audit": {"type":"cmd.error","name": name, "err": str(err)}})
        audit_log(action=f"cmd.{name}.error", actor_id=None, target=None, status="failed", meta={"err": str(err), "duration": dur})

    async def on_event_start(self, evt: Event) -> None:
        key = id(evt); self._evt_started_at[key] = time.perf_counter()
        name = type(evt).__name__
        log.info("evt.start", extra={"request_id": get_request_id(), "audit": {"type":"evt.start","name": name}})

    async def on_event_end(self, evt: Event) -> None:
        key = id(evt); start = self._evt_started_at.pop(key, time.perf_counter())
        dur = time.perf_counter() - start
        name = type(evt).__name__
        EVT_CNT.labels(name, "ok").inc()
        EVT_LAT.labels(name, "ok").observe(dur)
        log.info("evt.end", extra={"request_id": get_request_id(), "audit": {"type":"evt.end","name": name, "duration": dur}})

    async def on_event_error(self, evt: Event, err: BaseException) -> None:
        key = id(evt); start = self._evt_started_at.pop(key, time.perf_counter())
        dur = time.perf_counter() - start
        name = type(evt).__name__
        EVT_CNT.labels(name, "error").inc()
        EVT_LAT.labels(name, "error").observe(dur)
        log.exception("evt.error", extra={"request_id": get_request_id(), "audit": {"type":"evt.error","name": name, "err": str(err)}})

    async def on_uow_commit(self) -> None:
        UOW_CNT.labels("commit").inc()
        log.info("uow.commit", extra={"request_id": get_request_id(), "audit": {"type":"uow.commit"}})

    async def on_uow_rollback(self) -> None:
        UOW_CNT.labels("rollback").inc()
        log.info("uow.rollback", extra={"request_id": get_request_id(), "audit": {"type":"uow.rollback"}})
