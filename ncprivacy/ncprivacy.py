from __future__ import annotations

import functools
import itertools
import pathlib
import plistlib
import subprocess
import types
import uuid as _uuid
from typing import (
    NamedTuple,
    Optional,
)

from . import utils

GLOB_PRIVATE = '_*'
_RECORD_FDATE = 'delivered_date'
_F_IDENTIFIER = 'identifier'
_F_APP_ID = 'app_id'


class App(NamedTuple):
    app_id: int
    identifier: str
    _table_name = 'app'


class RecordData(NamedTuple):
    app: Optional[str]
    titl: Optional[str]
    subt: Optional[str]
    body: Optional[str]


class Record(NamedTuple):
    rec_id: int
    app_id: int
    uuid: bytes
    data: bytes
    delivered_date: Optional[float]
    presented: Optional[int]
    _table_name = 'record'

    @property
    def uuid_(self):
        return _uuid.UUID(bytes=self.uuid)

    @property
    def data_(self):
        return plistlib.loads(self.data)

    @property
    def delivered_date_(self):
        delivered_date = self.delivered_date
        return (None if delivered_date is None else
                utils.osx_ts_to_dt(delivered_date))

    @functools.lru_cache(maxsize=1)
    def get_useful_data(self):
        data = self.data_
        req = data.get('req', {})
        return RecordData(
            app=data.get('app'),
            titl=req.get('titl'),
            subt=req.get('subt'),
            body=req.get('body'),
        )


NC_PRIVACY_TABLES = frozenset((
    Record._table_name,
    'delivered',
    'displayed',
    'requests',
    'snoozed',
))


def get_db_path():
    return pathlib.Path(
        subprocess.run(
            ('/usr/bin/getconf', 'DARWIN_USER_DIR'),
            stdout=subprocess.PIPE,
            check=True,
            text=True,
        ).stdout.rstrip(),
        'com.apple.notificationcenter/db2/db',
    ).resolve(strict=True)


def _precursor(fn=None, **conn_kw):
    if fn is None:
        return functools.partial(_precursor, **conn_kw)

    @functools.wraps(fn)
    def _wrapper(cursor, *args, **kw):
        if cursor is None:
            return utils.with_db_connection(fn, **conn_kw)(
                get_db_path(), *args, **kw)
        return fn(cursor, *args, **kw)
    return _wrapper


def _next(fn):
    @functools.wraps(fn)
    def _wrapper(*args, **kw):
        result = fn(*args, **kw)
        if isinstance(result, types.GeneratorType):
            it_result = next(result, None)
            for _ in result:  # for release
                pass
            return it_result
        return result
    return _wrapper


def _filter_glob(sep, fname, prefix, values):
    return f" {sep} ".join(
        itertools.repeat(f"{fname} {prefix} GLOB ?", len(values)))


def _make_filter(fname, include, exclude):
    sql = ""
    filters = []
    if include:
        filters.append(f"({_filter_glob('OR', fname, '', include)})")
    if exclude:
        filters.append(_filter_glob('AND', fname, 'NOT', exclude))
    if filters:
        sql = f" WHERE {' AND '.join(filters)}"
    return sql, [*include, *exclude]


def _app_ids_in(cursor, include, exclude):
    return "({app_ids})".format(app_ids=', '.join(
        str(app.app_id) for app in
        iter_apps(cursor, include=include, exclude=exclude)
    ))


@_precursor
def iter_apps(cursor, *, include=(), exclude=(GLOB_PRIVATE,)):
    filter_sql, params = _make_filter(_F_IDENTIFIER, include, exclude)
    return map(App._make, cursor.execute(f"""
        SELECT {', '.join(App._fields)} FROM {App._table_name} {filter_sql}
        """, params))


@_precursor
def iter_records(cursor, *, include=(), exclude=(GLOB_PRIVATE,),
                 start_dt=None, stop_dt=None):
    record_tname = Record._table_name
    record_fields = Record._fields
    sql = f"""
    SELECT {', '.join(f"{record_tname}.{field}" for field in record_fields)} 
    FROM {record_tname}
    """
    params = []
    if include or exclude:
        app_tname = App._table_name
        filter_sql, params = _make_filter(
            f"{app_tname}.{_F_IDENTIFIER}", include, exclude)
        sql += f"""
        JOIN {app_tname} 
        ON {record_tname}.{_F_APP_ID} = {app_tname}.{_F_APP_ID}
        {filter_sql}
        """
    elif start_dt is not None or stop_dt is not None:
        sql += " WHERE TRUE"
    fdate = _RECORD_FDATE
    assert fdate in record_fields
    for dt, op in ((start_dt, '>='), (stop_dt, '<=')):
        if dt is not None:
            sql += f" AND {record_tname}.{fdate} {op} ?"
            params.append(utils.dt_to_osx_ts(dt))
    return map(Record._make, cursor.execute(sql, params))


@_next
@_precursor(mode='rw')
def rm_privacy_records(cursor, *, include=(), exclude=(GLOB_PRIVATE,)):
    if not NC_PRIVACY_TABLES:
        return 0
    sql = "DELETE FROM {table}"
    if include or exclude:
        sql += (f" WHERE {_F_APP_ID} IN "
                f"{_app_ids_in(cursor, include, exclude)}")
    return sum(cursor.execute(sql.format(table=table)).rowcount for
               table in NC_PRIVACY_TABLES)


@_next
@_precursor
def count_privacy_records(cursor, *, include=(), exclude=(GLOB_PRIVATE,)):
    if not NC_PRIVACY_TABLES:
        return 0
    has_filter = bool(include or exclude)
    app_ids_in = _app_ids_in(cursor, include, exclude) if has_filter else ""
    f_app_id = _F_APP_ID
    queries = []
    for table in NC_PRIVACY_TABLES:
        sql = f"SELECT COUNT(*) FROM {table}"
        if has_filter:
            sql += f" WHERE {table}.{f_app_id} IN {app_ids_in}"
        queries.append(f"({sql})")
    return cursor.execute(
        f"SELECT ({' + '.join(queries)}) AS result").fetchone()[0]
