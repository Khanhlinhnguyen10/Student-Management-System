
"""Non-destructive SQL Server COMMIT/ROLLBACK integration smoke test.

Uses a CONNECTION-LOCAL #temporary table. No permanent SMS business data
or stored procedures are changed. Run: python check_transaction.py
"""

import sys
import pyodbc

from app.repositories.database import (
    DatabaseConfigurationError,
    get_connection,
)


def main() -> int:
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Commit DDL so the temp table survives the next rollback.
        cursor.execute(
            "CREATE TABLE #SMS_TransactionProbe "
            "(probeId INT NOT NULL PRIMARY KEY)"
        )
        conn.commit()

        # A rollback must remove the attempted write.
        cursor.execute(
            "INSERT INTO #SMS_TransactionProbe (probeId) VALUES (?)",
            1,
        )
        conn.rollback()

        after_rollback = cursor.execute(
            "SELECT COUNT(*) FROM #SMS_TransactionProbe"
        ).fetchone()[0]
        conn.rollback()

        # A commit must preserve the write for this connection.
        cursor.execute(
            "INSERT INTO #SMS_TransactionProbe (probeId) VALUES (?)",
            2,
        )
        conn.commit()

        after_commit = cursor.execute(
            "SELECT COUNT(*) FROM #SMS_TransactionProbe"
        ).fetchone()[0]
        conn.rollback()

        print(
            "=== SMS Group 05: SQL Server Transaction smoke test ==="
        )
        print(
            f"Rows after ROLLBACK: {after_rollback} (expected 0)"
        )
        print(
            f"Rows after COMMIT:   {after_commit} (expected 1)"
        )

        if after_rollback != 0 or after_commit != 1:
            print(
                "FAILED: Transaction behavior "
                "does not match expectations."
            )
            return 1

        print(
            "SUCCESS: COMMIT and ROLLBACK behave "
            "correctly on SQL Server."
        )
        print(
            "Only a session-local temporary table was used."
        )

        return 0

    except (
        DatabaseConfigurationError,
        pyodbc.Error,
    ) as exc:
        print(
            f"TRANSACTION CHECK FAILED: {exc}",
            file=sys.stderr,
        )
        return 1

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
