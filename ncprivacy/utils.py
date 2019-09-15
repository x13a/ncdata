from __future__ import annotations

import datetime
import functools
import pathlib
import sqlite3

MAC_OS_TS_DIFF = 978307200


def with_db_connection(fn):
    @functools.wraps(fn)
    def _wrapper(db_path: pathlib.Path, *args, **kw):
        with sqlite3.connect(
            f'{db_path.resolve().as_uri()}?mode=rw',
            uri=True,
        ) as conn:
            result = fn(conn.cursor(), *args, **kw)
            if conn.in_transaction:
                conn.commit()
            return result
    return _wrapper


def convert_mac_os_ts_to_dt(ts):
    return datetime.datetime.fromtimestamp(ts + MAC_OS_TS_DIFF)
