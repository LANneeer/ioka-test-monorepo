from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from patterns.repository import AbstractRepository
from src.infrastructure.users.orm import UserORM
from src.domains.users.model import User, Role
from datetime import datetime, timezone


class SqlAlchemyAsyncUserRepository(AbstractRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__()
        self.session = session

    def _add(self, aggregate: User) -> None:
        self.session.add(self._to_orm(aggregate))

    def _get(self, reference: UUID) -> Optional[User]:
        raise NotImplementedError("Use async method 'get_async'")

    async def save(self, aggregate: User) -> User:
        now = datetime.now(timezone.utc)

        orm_obj: Optional[UserORM] = await self.session.get(UserORM, aggregate.id)

        if orm_obj is None:
            orm_obj = self._to_orm(aggregate)
            if orm_obj.created_at is None:
                orm_obj.created_at = now
            orm_obj.updated_at = now
            self.session.add(orm_obj)
        else:
            orm_obj.email = aggregate.email
            orm_obj.username = aggregate.username
            orm_obj.password_hash = getattr(aggregate, "_password_hash")
            orm_obj.role = aggregate.role.value if hasattr(aggregate.role, "value") else aggregate.role
            orm_obj.locale = aggregate.locale
            orm_obj.is_active = aggregate.is_active
            orm_obj.updated_at = now

        return self._to_domain(orm_obj)

    async def get_async(self, user_id: UUID) -> Optional[User]:
        row = await self.session.get(UserORM, user_id)
        return self._to_domain(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        res = await self.session.execute(select(UserORM).where(UserORM.email == email))
        row = res.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_by_username(self, username: str) -> Optional[User]:
        res = await self.session.execute(select(UserORM).where(UserORM.username == username))
        row = res.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def list_users(self, skip: int = 0, limit: int = 50) -> list[User]:
        res = await self.session.execute(
            select(UserORM).order_by(UserORM.created_at.desc()).offset(skip).limit(limit)
        )
        rows: Sequence[UserORM] = res.scalars().all()
        return [self._to_domain(r) for r in rows]

    async def remove(self, user_id: UUID) -> None:
        await self.session.execute(delete(UserORM).where(UserORM.id == user_id))

    @staticmethod
    def _to_domain(row: UserORM) -> User:
        return User.restore(
            user_id=row.id,
            email=row.email,
            username=row.username,
            password_hash=row.password_hash,
            role=Role(row.role.value if hasattr(row.role, "value") else row.role),
            locale=row.locale,
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_orm(agg: User) -> UserORM:
        return UserORM(
            id=agg.id,
            email=agg.email,
            username=agg.username,
            password_hash=getattr(agg, "_password_hash"),
            role=agg.role.value,
            locale=agg.locale,
            is_active=agg.is_active,
            created_at=agg.created_at,
            updated_at=agg.updated_at,
        )
