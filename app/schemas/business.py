import uuid

from fastapi_users import schemas


class BusinessRead(schemas.BaseUser[uuid.UUID]):
    name: str


class BusinessCreate(schemas.BaseUserCreate):
    name: str


class BusinessUpdate(schemas.BaseUserUpdate):
    name: str | None = None
