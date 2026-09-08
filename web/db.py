"""Подключение витрины к MySQL.

Модуль намеренно самодостаточный: витрина не зависит от кода парсера,
поэтому её можно развернуть отдельно, имея только дамп данных.
"""

import os
from contextlib import contextmanager
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

DB = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "velostok"),
    "charset": "utf8mb4",
}


def connect():
    return pymysql.connect(**DB, cursorclass=DictCursor, autocommit=True)


@contextmanager
def cursor(conn):
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()
