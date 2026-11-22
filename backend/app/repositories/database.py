
"""SQL Server connection foundation for the SMS Group 05 Flask backend.

The Repository layer owns database connectivity. Controllers and React must
never contain SQL Server credentials or construct connection strings.
"""

from dataclasses import dataclass
from pathlib import Path
import os

import pyodbc
from dotenv import load_dotenv


# Resolve backend/.env regardless of the terminal's working directory.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=_BACKEND_DIR / ".env", override=False)


class DatabaseConfigurationError(RuntimeError):
    """Missing or invalid local configuration (not a SQL query error)."""


def _read_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default

    normalized = raw.strip().lower()

    if normalized in {"true", "yes", "1"}:
        return True

    if normalized in {"false", "no", "0"}:
        return False

    raise DatabaseConfigurationError(
        f"{name} must be true/false, yes/no or 1/0."
    )


def _odbc_quote(value: str) -> str:
    """Protect one connection-string value, including semicolons in passwords."""
    return "{" + value.replace("}", "}}") + "}"


@dataclass(frozen=True, repr=False)
class DatabaseSettings:
    server: str
    database: str
    driver: str
    auth_mode: str
    username: str | None
    password: str | None
    encrypt: bool
    trust_server_certificate: bool
    timeout: int

    @classmethod
    def from_environment(cls) -> "DatabaseSettings":
        server = os.getenv("DB_SERVER", "").strip()
        database = os.getenv("DB_DATABASE", "").strip()
        driver = os.getenv(
            "DB_DRIVER",
            "ODBC Driver 18 for SQL Server"
        ).strip()
        auth_mode = os.getenv(
            "DB_AUTH_MODE", "windows"
        ).strip().lower()

        username = os.getenv("DB_USERNAME", "").strip() or None
        password = os.getenv("DB_PASSWORD", "") or None

        if not server:
            raise DatabaseConfigurationError(
                "DB_SERVER is required in backend/.env."
            )

        if not database:
            raise DatabaseConfigurationError(
                "DB_DATABASE is required in backend/.env."
            )

        if not driver:
            raise DatabaseConfigurationError(
                "DB_DRIVER cannot be empty."
            )

        if auth_mode not in {"windows", "sql"}:
            raise DatabaseConfigurationError(
                "DB_AUTH_MODE must be 'windows' or 'sql'."
            )

        if auth_mode == "sql" and (not username or not password):
            raise DatabaseConfigurationError(
                "DB_USERNAME and DB_PASSWORD are required "
                "for SQL authentication."
            )

        raw_timeout = os.getenv("DB_TIMEOUT", "5").strip()

        try:
            timeout = int(raw_timeout)
        except ValueError as exc:
            raise DatabaseConfigurationError(
                "DB_TIMEOUT must be an integer."
            ) from exc

        if not 1 <= timeout <= 15:
            raise DatabaseConfigurationError(
                "DB_TIMEOUT must be between 1 and 15 seconds."
            )

        return cls(
            server=server,
            database=database,
            driver=driver,
            auth_mode=auth_mode,
            username=username,
            password=password,
            encrypt=_read_bool("DB_ENCRYPT", True),
            trust_server_certificate=_read_bool(
                "DB_TRUST_SERVER_CERTIFICATE", False
            ),
            timeout=timeout,
        )

    def connection_string(self) -> str:
        parts = [
            f"DRIVER={_odbc_quote(self.driver)}",
            f"SERVER={_odbc_quote(self.server)}",
            f"DATABASE={_odbc_quote(self.database)}",
            "Encrypt=yes" if self.encrypt else "Encrypt=no",
            (
                "TrustServerCertificate=yes"
                if self.trust_server_certificate
                else "TrustServerCertificate=no"
            ),
            "APP=SMS_Group05_Flask",
        ]

        if self.auth_mode == "windows":
            parts.append("Trusted_Connection=yes")
        else:
            parts.append(
                f"UID={_odbc_quote(self.username)}"
            )
            parts.append(
                f"PWD={_odbc_quote(self.password)}"
            )

        return ";".join(parts) + ";"


def get_connection() -> pyodbc.Connection:
    """Open a real SQL Server connection; caller must close it.

    The default transaction mode is explicit (autocommit=False).
    Database writes will use commit/rollback in later steps.
    """
    settings = DatabaseSettings.from_environment()

    installed_drivers = pyodbc.drivers()

    if settings.driver not in installed_drivers:
        raise DatabaseConfigurationError(
            f"ODBC driver '{settings.driver}' "
            "is not installed or available to Python."
        )

    return pyodbc.connect(
        settings.connection_string(),
        timeout=settings.timeout,
        autocommit=False,
    )
