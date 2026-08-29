from fastapi_users import schemas


class BusinessRead(schemas.BaseUser[int]):
    name: str


class BusinessCreate(schemas.BaseUserCreate):
    name: str


class BusinessUpdate(schemas.BaseUserUpdate):
    name: str | None = None
