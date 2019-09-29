import contextlib
import datetime
import functools
import sqlite3

OSX_TS_UNIX_DIFF = 978307200


def with_db_connection(fn):
    @functools.wraps(fn)
    def _wrapper(db_path, *args, **kw):
        with contextlib.closing(sqlite3.connect(
            f'{db_path.resolve(strict=True).as_uri()}?mode=rw',
            uri=True,
        )) as conn, conn, contextlib.closing(conn.cursor()) as cur:
            return fn(cursor=cur, *args, **kw)
    return _wrapper


def osx_ts_to_unix_ts(ts):
    return ts + OSX_TS_UNIX_DIFF


def osx_ts_to_dt(ts):
    return datetime.datetime.fromtimestamp(osx_ts_to_unix_ts(ts))
