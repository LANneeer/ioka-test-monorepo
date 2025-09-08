import hashlib
from typing import Annotated
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException, status, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from src.gateway.schemas.users import UserCreateDTO, UserReadDTO, UserUpdateDTO, PasswordChangeDTO
from src.dto.commands import RegisterUser, UpdateUserProfile, ChangeUserPassword, ActivateUser, DeactivateUser, PromoteToAdmin
from src.bootstrap.async_settings import bootstrap_async
from src.infrastructure.async_unit_of_work import AsyncUnitOfWork
from src.infrastructure.hooks import PromAuditHook
from src.infrastructure.middleware import IdempotencyMiddleware, MetricsMiddleware, prom_endpoint
from src.cli.error import install_exception_handlers
from src.config import settings

app = FastAPI(
    title="User Service (async)",
    servers=[{"url": "/api/users"}]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.add_middleware(IdempotencyMiddleware)
if settings.PROM_ENABLED:
    app.add_middleware(MetricsMiddleware)
install_exception_handlers(app)

async def get_uow():
    async with AsyncUnitOfWork() as uow:
        yield uow

def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()


@app.get("/metrics")
def metrics():
    data, content_type = prom_endpoint()
    return Response(content=data, media_type=content_type)


@app.get("/users", response_model=list[UserReadDTO])
async def list_users(
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items = await uow.users.list_users(skip=skip, limit=limit)
    return [
        UserReadDTO(
            id=u.id, email=u.email, username=u.username,
            role=u.role.value, locale=u.locale, is_active=u.is_active
        )
        for u in items
    ]

@app.post("/users", response_model=UserReadDTO, status_code=status.HTTP_201_CREATED)
async def register_user(
    dto: UserCreateDTO,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook) 
    results = await bus.handle(RegisterUser(
        email=dto.email, username=dto.username,
        password_hash=hash_password(dto.password), locale=dto.locale
    ))
    user_id = results[0]
    user = await uow.users.get_async(user_id)
    if not user:
        raise HTTPException(status_code=500, detail="User not persisted")
    return UserReadDTO(
        id=user.id, email=user.email, username=user.username,
        role=user.role.value, locale=user.locale, is_active=user.is_active
    )

@app.get("/users/{user_id}", response_model=UserReadDTO)
async def get_user(
    user_id: UUID,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    user = await uow.users.get_async(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserReadDTO(
        id=user.id, email=user.email, username=user.username,
        role=user.role.value, locale=user.locale, is_active=user.is_active
    )

@app.patch("/users/{user_id}", response_model=UserReadDTO)
async def update_user(
    user_id: UUID,
    dto: UserUpdateDTO,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook) 
    await bus.handle(UpdateUserProfile(user_id=user_id, new_username=dto.username, new_locale=dto.locale))
    user = await uow.users.get_async(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserReadDTO(
        id=user.id, email=user.email, username=user.username,
        role=user.role.value, locale=user.locale, is_active=user.is_active
    )

@app.post("/users/{user_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user_id: UUID,
    dto: PasswordChangeDTO,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook) 
    await bus.handle(ChangeUserPassword(user_id=user_id, new_password_hash=hash_password(dto.password)))
    return None

@app.post("/users/{user_id}/activate", status_code=status.HTTP_204_NO_CONTENT)
async def activate_user(
    user_id: UUID,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook) 
    await bus.handle(ActivateUser(user_id=user_id))
    return None

@app.post("/users/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook) 
    await bus.handle(DeactivateUser(user_id=user_id))
    return None

@app.post("/users/{user_id}/promote", status_code=status.HTTP_204_NO_CONTENT)
async def promote_user(
    user_id: UUID,
    uow: Annotated[AsyncUnitOfWork, Depends(get_uow)],
):
    hook = PromAuditHook()
    bus = bootstrap_async(uow, hook=hook) 
    await bus.handle(PromoteToAdmin(user_id=user_id))
    return None
