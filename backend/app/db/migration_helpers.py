from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

_SQLITE_UUID_EXPR = (
    "lower(hex(randomblob(4))) || '-' || "
    "lower(hex(randomblob(2))) || '-4' || "
    "substr(lower(hex(randomblob(2))),2) || '-' || "
    "substr('89ab', abs(random()) % 4 + 1, 1) || "
    "substr(lower(hex(randomblob(2))),2) || '-' || "
    "lower(hex(randomblob(6)))"
)


def uuid_server_default() -> TextClause:
    return text(f"({_SQLITE_UUID_EXPR})")


def now_server_default() -> TextClause:
    return text("CURRENT_TIMESTAMP")
