from uuid import UUID

from src.dto.commands import RegisterUser, UpdateUserProfile, PromoteToAdmin
from src.infrastructure.unit_of_work import InMemoryUnitOfWork
from src.bootstrap.settings import bootstrap


class PrintNotifier:
    def send(self, *, channel: str, message: str) -> None:
        print(f"[NOTIFY:{channel}] {message}")


class PrintPublisher:
    def publish(self, topic: str, payload: dict) -> None:
        print(f"[PUBLISH:{topic}] {payload}")


def main() -> None:
    uow = InMemoryUnitOfWork()
    bus = bootstrap(uow, notifier=PrintNotifier(), publisher=PrintPublisher())

    [user_id] = bus.handle(RegisterUser(email="a@example.com", username="alice", password_hash="hash123"))
    assert isinstance(user_id, UUID)

    bus.handle(UpdateUserProfile(user_id=user_id, new_username="alice2"))

    bus.handle(PromoteToAdmin(user_id=user_id))

    user = uow.users.get(user_id)
    print("User state:", user.username, user.role.value, user.is_active)


if __name__ == "__main__":
    main()
