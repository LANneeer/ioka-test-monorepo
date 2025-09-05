from abc import ABC, abstractmethod
from typing import Generic, Optional, Set, TypeVar, Any

from .aggregator import AbstractAggregate

T = TypeVar("T", bound=AbstractAggregate)


class AbstractRepository(Generic[T], ABC):
    def __init__(self) -> None:
        self.seen: Set[T] = set()

    def add(self, aggregate: T) -> None:
        self._add(aggregate)
        self.seen.add(aggregate)

    def get(self, reference: Any) -> Optional[T]:
        agg = self._get(reference)
        if agg:
            self.seen.add(agg)
        return agg

    @abstractmethod
    def _add(self, aggregate: T) -> None:
        raise NotImplementedError

    @abstractmethod
    def _get(self, reference: Any) -> Optional[T]:
        raise NotImplementedError
