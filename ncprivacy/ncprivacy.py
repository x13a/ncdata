"""
MacOS Notification Center Privacy
"""

from __future__ import annotations

__version__ = '0.0.1'

import functools
import itertools
import pathlib
import plistlib
import shutil
import subprocess
import typing
import uuid

import utils


class NCPrivacyError(Exception):
    pass


class App(typing.NamedTuple):
    app_id: int
    identifier: str
    _table_name = 'app'


class Record(typing.NamedTuple):
    rec_id: int
    app_id: int
    uuid: bytes
    data: bytes
    delivered_date: typing.Optional[float]
    _table_name = 'record'

    @property
    @functools.lru_cache(maxsize=1)
    def uuid_(self):
        return uuid.UUID(bytes=self.uuid)

    @property
    @functools.lru_cache(maxsize=1)
    def data_(self):
        return plistlib.loads(self.data)

    @property
    @functools.lru_cache(maxsize=1)
    def delivered_date_(self):
        return (None if self.delivered_date is None else
                utils.convert_mac_os_ts_to_dt(self.delivered_date))


NC_PRIVACY_TABLES = {
    Record._table_name,
    'delivered',
    'displayed',
    'requests',
    'snoozed',
}


def get_db_path() -> pathlib.Path:
    cmd = 'getconf'
    getconf_path = shutil.which(cmd)
    if getconf_path is None:
        raise NCPrivacyError(f"{cmd} not found")
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
        raise NCPrivacyError(f"{result} not found")
    return result


def _sql_in_vals(fname, vals):
    return f"{fname} IN ({', '.join(itertools.repeat('?', len(vals)))})"


def _sql_filter(fname, identifiers, skip_private):
    sql = ""
    where_exprs = []
    if identifiers:
        where_exprs.append(_sql_in_vals(fname, identifiers))
    if skip_private:
        where_exprs.append(f"NOT {fname} GLOB '_*'")
    if where_exprs:
        sql += f" WHERE {' AND '.join(where_exprs)}"
    return sql


def iter_apps(cursor, *, identifiers=(), skip_private=True):
    yield from map(App._make, cursor.execute(f"""
        SELECT {', '.join(App._fields)} FROM {App._table_name}
        {_sql_filter('identifier', identifiers, skip_private)}
        """, identifiers))


def rm_apps(cursor, *, identifiers=(), skip_private=True):
    return cursor.execute(f"""
        DELETE FROM {App._table_name}
        {_sql_filter('identifier', identifiers, skip_private)}
        """, identifiers).rowcount


def iter_records(cursor, *, identifiers=(), skip_private=True):
    record_tname = Record._table_name
    sql = f"""
    SELECT {', '.join(f'{record_tname}.{field}' for field in Record._fields)} 
    FROM {record_tname}
    """
    if identifiers or skip_private:
        app_tname = App._table_name
        app_id_fname = 'app_id'
        sql += f"""
        JOIN {app_tname} 
        ON {record_tname}.{app_id_fname} = {app_tname}.{app_id_fname}
        {_sql_filter(f'{app_tname}.identifier', identifiers, skip_private)}
        """
    yield from map(Record._make, cursor.execute(sql, identifiers))


def rm_privacy_records(cursor, *, identifiers=(), skip_private=True):
    sql = "DELETE FROM {table}"
    app_ids = []
    if identifiers or skip_private:
        app_ids = [
            app.app_id for app in
            iter_apps(
                cursor,
                identifiers=identifiers,
                skip_private=skip_private,
            )
        ]
        sql += f" WHERE {_sql_in_vals('app_id', app_ids)}"
    return sum(cursor.execute(sql.format(table=table), app_ids).rowcount for
               table in NC_PRIVACY_TABLES)
