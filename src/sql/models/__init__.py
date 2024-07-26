from sqlalchemy import String
from typing_extensions import Annotated
from sqlalchemy.orm import DeclarativeBase

str50 = Annotated[str, 50]


# declarative base with a type-level override, using a type that is
# expected to be used in multiple places
class Base(DeclarativeBase):
    type_annotation_map = {
        str50: String(50),
    }
