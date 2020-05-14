import contextlib
import datetime
import functools
import sqlite3
import types

OSX_TS_UNIX_DIFF = (datetime.date(2001, 1, 1) -
                    datetime.date(1970, 1, 1)).total_seconds()


def with_db_connection(fn):
    @functools.wraps(fn)
    def _wrapper(db_path, *args, **kw):
        with contextlib.closing(sqlite3.connect(
            f'{db_path.resolve(strict=True).as_uri()}?mode=rw',
            uri=True,
        )) as conn, conn, contextlib.closing(conn.cursor()) as cur:
            result = fn(cursor=cur, *args, **kw)
            if isinstance(result, (types.GeneratorType, map, filter)):
                yield from result
            else:
                yield result
    return _wrapper


def unix_ts_to_osx_ts(ts):
    return ts - OSX_TS_UNIX_DIFF


def osx_ts_to_unix_ts(ts):
    return ts + OSX_TS_UNIX_DIFF


def dt_to_osx_ts(dt):
    return unix_ts_to_osx_ts(dt.timestamp())


def osx_ts_to_dt(ts):
    return datetime.datetime.fromtimestamp(osx_ts_to_unix_ts(ts))
