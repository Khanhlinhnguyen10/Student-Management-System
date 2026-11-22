
"""One-connection transaction boundary for SQL Server repositories.

write=True: commit only when the entire with block succeeds.
write=False: rollback after read queries to end the transaction cleanly.

This layer never starts a nested SQL transaction. A stored procedure that
manages its own transaction must be integrated with that behavior in mind.
"""

from contextlib import contextmanager
import logging
from typing import Any, Callable, Iterator

from app.repositories.database import get_connection

logger = logging.getLogger(__name__)


@contextmanager
def connection_scope(
    *,
    write: bool = False,
    connection_factory: Callable[[], Any] | None = None,
) -> Iterator[Any]:
    """Yield a connection and always close it afterwards.

    write=False is a Python convention, NOT a SQL Server permission boundary.
    A read-only repository must still issue SELECT-only queries. All write
    permissions and actor authorization must be enforced separately.
    """
    if type(write) is not bool:
        raise ValueError("write must be True or False.")

    factory = connection_factory if connection_factory is not None else get_connection
    conn = factory()

    try:
        yield conn
        if write:
            conn.commit()
        else:
            conn.rollback()
    except BaseException:
        try:
            conn.rollback()
        except Exception:
            logger.exception("SQL Server transaction rollback failed.")
        raise
    finally:
        conn.close()
