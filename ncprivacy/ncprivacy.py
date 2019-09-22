"""
MacOS Notification Center Privacy
"""

from __future__ import annotations

__version__ = '0.0.2'

import functools
import itertools
import pathlib
import plistlib
import shutil
import subprocess
import uuid as _uuid
from typing import (
    NamedTuple,
    Optional,
)

import utils

LIKE_PRIVATE = '\\_%'
F_IDENTIFIER = 'identifier'
F_APP_ID = 'app_id'


class App(NamedTuple):
    app_id: int
    identifier: str
    _table_name = 'app'


class Record(NamedTuple):
    rec_id: int
    app_id: int
    uuid: bytes
    data: bytes
    delivered_date: Optional[float]
    presented: Optional[int]
    _table_name = 'record'

    @property
    @functools.lru_cache(maxsize=1)
    def uuid_(self):
        return _uuid.UUID(bytes=self.uuid)

    @property
    @functools.lru_cache(maxsize=1)
    def data_(self):
        return plistlib.loads(self.data)

    @property
    @functools.lru_cache(maxsize=1)
    def delivered_date_(self):
        return (None if self.delivered_date is None else
                utils.convert_osx_ts_to_dt(self.delivered_date))


NC_PRIVACY_TABLES = {
    Record._table_name,
    'delivered',
    'displayed',
    'requests',
    'snoozed',
}


def get_db_path():
    cmd = 'getconf'
    getconf_path = shutil.which(cmd)
    if getconf_path is None:
        raise FileNotFoundError(f"{cmd} not found")
    result = pathlib.Path(
        subprocess.run(
            (getconf_path, 'DARWIN_USER_DIR'),
            stdout=subprocess.PIPE,
            check=True,
            text=True,
        ).stdout.rstrip(),
        'com.apple.notificationcenter',
        'db2',
        'db',
    )
    if not result.exists():
        raise FileNotFoundError(f"{result} not found")
    return result


def _sql_in_vals(fname, vals):
    return f"{fname} IN ({', '.join(itertools.repeat('?', len(vals)))})"


def _make_filter(fname, identifiers, excludes):
    sql = ""
    where_exprs = []
    if identifiers:
        where_exprs.append(_sql_in_vals(fname, identifiers))
    if excludes:
        where_exprs.append(' AND '.join(itertools.repeat(
            f"NOT {fname} LIKE ? ESCAPE '\\'",
            len(excludes),
        )))
    if where_exprs:
        sql += f" WHERE {' AND '.join(where_exprs)}"
    return sql, list(identifiers) + list(excludes)


def iter_apps(cursor, *, identifiers=(), excludes=(LIKE_PRIVATE,)):
    filter_sql, params = _make_filter(F_IDENTIFIER, identifiers, excludes)
    yield from map(App._make, cursor.execute(f"""
        SELECT {', '.join(App._fields)} FROM {App._table_name} {filter_sql}
        """, params))


def rm_apps(cursor, *, identifiers=(), excludes=(LIKE_PRIVATE,)):
    filter_sql, params = _make_filter(F_IDENTIFIER, identifiers, excludes)
    return cursor.execute(f"DELETE FROM {App._table_name} {filter_sql}",
                          params).rowcount


def count_apps(cursor, *, identifiers=(), excludes=(LIKE_PRIVATE,)):
    filter_sql, params = _make_filter(F_IDENTIFIER, identifiers, excludes)
    return cursor.execute(f"""
        SELECT COUNT(*) FROM {App._table_name} {filter_sql}
        """, params).fetchone()[0]


def iter_records(cursor, *, identifiers=(), excludes=(LIKE_PRIVATE,)):
    record_tname = Record._table_name
    sql = f"""
    SELECT {', '.join(f'{record_tname}.{field}' for field in Record._fields)} 
    FROM {record_tname}
    """
    params = []
    if identifiers or excludes:
        app_tname = App._table_name
        filter_sql, params = _make_filter(
            f'{app_tname}.{F_IDENTIFIER}', identifiers, excludes)
        sql += f"""
        JOIN {app_tname} ON {record_tname}.{F_APP_ID} = {app_tname}.{F_APP_ID}
        {filter_sql}
        """
    yield from map(Record._make, cursor.execute(sql, params))


def rm_privacy_records(cursor, *, identifiers=(), excludes=(LIKE_PRIVATE,)):
    sql = "DELETE FROM {table}"
    app_ids = []
    if identifiers or excludes:
        app_ids = [
            app.app_id for app in
            iter_apps(
                cursor,
                identifiers=identifiers,
                excludes=excludes,
            )
        ]
        sql += f" WHERE {_sql_in_vals(F_APP_ID, app_ids)}"
    return sum(cursor.execute(sql.format(table=table), app_ids).rowcount for
               table in NC_PRIVACY_TABLES)


def count_privacy_records(cursor, *, identifiers=(), excludes=(LIKE_PRIVATE,)):
    sql = "SELECT ({query}) AS result"
    app_ids = [
        app.app_id for app in
        iter_apps(
            cursor,
            identifiers=identifiers,
            excludes=excludes,
        )
    ] if identifiers or excludes else []
    has_app_ids = bool(app_ids)
    queries = []
    for table in NC_PRIVACY_TABLES:
        sub_sql = f"SELECT COUNT(*) FROM {table}"
        if has_app_ids:
            sub_sql += f" WHERE {_sql_in_vals(f'{table}.{F_APP_ID}', app_ids)}"
        queries.append(f"({sub_sql})")
    return cursor.execute(sql.format(query=' + '.join(queries)),
                          app_ids * len(queries)).fetchone()[0]
