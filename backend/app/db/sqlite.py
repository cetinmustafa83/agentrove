from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine


def _set_foreign_keys_pragma(dbapi_connection: Any, _: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def enable_foreign_keys(engine: Engine) -> None:
    # SQLite ignores FK constraints unless PRAGMA foreign_keys=ON is set per
    # connection — required for ondelete CASCADE / SET NULL to be enforced.
    event.listen(engine, "connect", _set_foreign_keys_pragma)
