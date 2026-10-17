"""Check nodestream/.env and try one Neo4j login. Prints no secrets."""

import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

KEYS = ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD")
ENV_PATH = Path(__file__).with_name(".env")
CONNECT_TIMEOUT = 5


def file_values(text: str) -> dict[str, str]:
    values = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value
    return values


def shell_values(path: Path) -> tuple[dict[str, str] | None, str]:
    code = "import os; print('\\n'.join(os.environ.get(k, '') for k in %r))" % (KEYS,)
    proc = subprocess.run(
        ["/bin/sh", "-c", 'set -a; . "$1"; set +a; exec "$2" -c "$3"', "sh", str(path), sys.executable, code],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None, proc.stderr.strip() or "shell could not read .env"
    lines = proc.stdout.splitlines()
    if len(lines) != len(KEYS):
        return None, "shell export did not return every Neo4j variable"
    return dict(zip(KEYS, lines)), ""


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def report_settings(raw: dict[str, str], sent: dict[str, str]) -> list[str]:
    problems = []
    for key in KEYS:
        if key not in raw:
            problems.append(f"{key} is missing from .env")
            continue
        literal = unquote(raw[key])
        value = sent[key]
        if value == "":
            if literal.strip():
                problems.append(f"{key} is empty after the shell reads .env")
            else:
                problems.append(f"{key} is empty")
            continue
        if key == "NEO4J_PASSWORD":
            print(f"{key} is set ({len(value)} characters)")
        else:
            print(f"{key}={value}")
        if value != value.strip():
            problems.append(f"{key} has leading or trailing whitespace")
        if raw[key] != literal and value == literal:
            print(f"{key} quotes were removed when the file was read")
        elif value != literal:
            problems.append(
                f"{key} changes when the shell reads .env "
                "(quote the value, or remove $ # and spaces)"
            )
    return problems


def check_tcp(uri: str) -> str | None:
    parsed = urlparse(uri)
    if parsed.scheme not in {"bolt", "neo4j", "bolt+s", "neo4j+s", "bolt+ssc", "neo4j+ssc"}:
        return f"NEO4J_URI scheme {parsed.scheme!r} is not a Bolt URI"
    host = parsed.hostname
    port = parsed.port or 7687
    if not host:
        return f"NEO4J_URI {uri!r} has no host"
    try:
        with socket.create_connection((host, port), CONNECT_TIMEOUT):
            return None
    except OSError as exc:
        return f"cannot reach {host}:{port} ({exc.strerror or exc})"


def check_login(uri: str, username: str, password: str) -> str | None:
    try:
        from neo4j import GraphDatabase
        from neo4j.exceptions import AuthError, Neo4jError, ServiceUnavailable
    except ImportError:
        return "neo4j driver is not installed; run make install"

    driver = GraphDatabase.driver(
        uri,
        auth=(username, password),
        connection_timeout=CONNECT_TIMEOUT,
        max_transaction_retry_time=0,
    )

    def once() -> str | None:
        try:
            driver.verify_connectivity()
            with driver.session(database="neo4j") as session:
                session.run("RETURN 1").consume()
        except AuthError:
            return f"authentication failed for user {username!r}; Neo4j rejected the password in .env"
        except ServiceUnavailable as exc:
            detail = str(exc).splitlines()[0]
            return f"Bolt handshake failed: {detail}"
        except Neo4jError as exc:
            if (exc.code or "").endswith("AuthenticationRateLimit"):
                return "rate-limit"
            return f"connected, then Neo4j returned {exc.code or exc}"
        return None

    try:
        result = once()
        if result == "rate-limit":
            print("Neo4j is temporarily blocking logins after earlier failures; retrying in 5s")
            time.sleep(5)
            result = once()
            if result == "rate-limit":
                return "Neo4j is still blocking logins. Wait a minute, then run make validate again"
        return result
    finally:
        driver.close()


def main() -> int:
    if not ENV_PATH.is_file():
        print("missing .env; run make setup and set NEO4J_PASSWORD")
        return 1
    raw = file_values(ENV_PATH.read_text())
    sent, error = shell_values(ENV_PATH)
    if sent is None:
        print(error)
        return 1
    problems = report_settings(raw, sent)
    if problems:
        for problem in problems:
            print(problem)
        return 1

    reach = check_tcp(sent["NEO4J_URI"])
    if reach:
        print(reach)
        return 1
    print(f"{sent['NEO4J_URI']} is accepting connections")

    login = check_login(sent["NEO4J_URI"], sent["NEO4J_USERNAME"], sent["NEO4J_PASSWORD"])
    if login:
        print(login)
        return 1
    print("logged in and queried database neo4j")
    return 0


if __name__ == "__main__":
    sys.exit(main())
