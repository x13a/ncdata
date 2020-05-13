import argparse
import datetime
import functools
import itertools
import json
import pathlib
import re

from . import (
    __doc__ as lib_doc,
    __name__ as lib_name,
    __version__ as lib_version,
    ncprivacy,
    utils,
)

json_dumps = functools.partial(json.dumps, indent=2)


def pprint_table(rows, *, fields=()):
    rows = tuple(rows)
    if not rows:
        return
    width_rows = rows
    if fields:
        assert len(fields) == len(rows[0])
        width_rows = itertools.chain([fields], width_rows)
    widths = [
        max(map(len, column)) for column in
        zip(*(map(str, row) for row in width_rows))
    ]
    sep_tmpl = ' {sep} '
    column_sep = sep_tmpl.format(sep='|')
    delimiter_sep = sep_tmpl.format(sep='+')
    delimiter = '{sep}{row}{sep}'.format(
        sep=delimiter_sep,
        row=delimiter_sep.join(
            '-' * widths[idx] for idx in range(len(fields or rows[0]))),
    )
    row_tmpl = f'{column_sep}{{row}}{column_sep}'
    print(delimiter)
    if fields:
        print(row_tmpl.format(row=column_sep.join(
            f'{field.upper():{widths[idx]}}'
            for idx, field in enumerate(fields)
        )))
        print(delimiter)
    for row in rows:
        print(row_tmpl.format(row=column_sep.join(
            f'{val:{widths[idx]}}' for idx, val in enumerate(row)
        )))
    print(delimiter)


def record_to_dict(record):
    delivered_date = record.delivered_date
    result = record._asdict()
    result.update(
        uuid=str(record.uuid_),
        data=record.get_useful_data()._asdict(),
        delivered_date=(None if delivered_date is None else
                        utils.osx_ts_to_unix_ts(delivered_date)),
    )
    return result


def records_filter(pattern):
    def _fn(record):
        data = record.get_useful_data()
        for value in (data.titl, data.subt, data.body):
            if value is not None and re.search(pattern, value) is not None:
                return True
        return False
    return _fn


@utils.with_db_connection
def ls_apps(as_json, *args, **kw):
    apps_gen = ncprivacy.iter_apps(*args, **kw)
    (
        print(json_dumps([app._asdict() for app in apps_gen]))
        if as_json else
        pprint_table(apps_gen, fields=ncprivacy.App._fields)
    )


@utils.with_db_connection
def ls_records(as_json, pattern, *args, **kw):
    records_gen = ncprivacy.iter_records(*args, **kw)
    if pattern is not None:
        records_gen = filter(records_filter(pattern), records_gen)
    if as_json:
        print(json_dumps(tuple(map(record_to_dict, records_gen))))
    else:
        try:
            first_rec = next(records_gen)
        except StopIteration:
            return
        print()
        for num, record in enumerate(
            itertools.chain([first_rec], records_gen),
            start=1,
        ):
            print(f"#{num}")
            print(f"delivered: {record.delivered_date_ or ''}")
            data = record.get_useful_data()
            print(f" bundleid: {data.app  or ''}")
            print(f"    title: {data.titl or ''}")
            print(f" subtitle: {data.subt or ''}")
            print(f"     body: {data.body or ''}", end='\n\n')


@utils.with_db_connection
def rm(as_json, *args, **kw):
    result = ncprivacy.rm_privacy_records(*args, **kw)
    print(result if as_json else f"Deleted: {result}")


@utils.with_db_connection
def count(as_json, *args, **kw):
    print(ncprivacy.count_privacy_records(*args, **kw))


def dt_type(s):
    return datetime.datetime.fromisoformat(s)


def parse_args(*args, **kw):
    parser = argparse.ArgumentParser(prog=lib_name, description=lib_doc)
    parser.add_argument(
        '-V',
        '--version',
        action='version',
        version=lib_version,
    )
    group = parser.add_argument_group('base arguments')
    group.add_argument(
        '--database',
        type=pathlib.Path,
        metavar='PATH',
        dest='db_path',
        help="Custom database path",
    )
    glob_metavar = 'GLOB'
    group.add_argument(
        '-i',
        '--include',
        action='append',
        metavar=glob_metavar,
        default=[],
        help="Filter by identifiers",
    )
    group.add_argument(
        '-e',
        '--exclude',
        action='append',
        metavar=glob_metavar,
        default=[],
        help="Exclude by identifiers",
    )
    group.add_argument(
        '--not-exclude-private',
        action='store_false',
        dest='exclude_private',
        help="Do not exclude identifiers startswith underscore",
    )
    group.add_argument(
        '--json',
        action='store_true',
        dest='as_json',
        help="JSON output",
    )
    subparsers = parser.add_subparsers(required=True, dest='command')
    subparsers.add_parser(
        'ls-apps',
        help=f"List identifier records from table "
             f"`{ncprivacy.App._table_name}`",
    ).set_defaults(fn=ls_apps)
    records = subparsers.add_parser(
        'ls-records',
        help=f"List notification records from table "
             f"`{ncprivacy.Record._table_name}`",
    )
    dt_metavar = "ISO_DATETIME"
    fdate = ncprivacy.RECORD_FDATE
    records.add_argument(
        '--start-date',
        type=dt_type,
        metavar=dt_metavar,
        dest='start_dt',
        help=f"Start datetime by field `{fdate}`",
    )
    records.add_argument(
        '--stop-date',
        type=dt_type,
        metavar=dt_metavar,
        dest='stop_dt',
        help=f"Stop datetime by field `{fdate}`",
    )
    records.add_argument(
        '--search',
        metavar='REGEX',
        dest='pattern',
        help="Search match in [title, subtitle, body]",
    )
    records.set_defaults(fn=ls_records)
    nc_privacy_tables = ', '.join(sorted(ncprivacy.NC_PRIVACY_TABLES))
    subparsers.add_parser(
        'rm',
        help=f"Delete records from tables [{nc_privacy_tables}]",
    ).set_defaults(fn=rm)
    subparsers.add_parser(
        'count',
        help=f"Count records from tables [{nc_privacy_tables}]",
    ).set_defaults(fn=count)
    return parser.parse_args(*args, **kw)


def main(argv=None):
    nsargs = parse_args(argv)
    if nsargs.db_path is None:
        nsargs.db_path = ncprivacy.get_db_path()
    if nsargs.exclude_private:
        nsargs.exclude.append(ncprivacy.GLOB_PRIVATE)
    fn = nsargs.fn
    for arg in (
        'exclude_private',
        'fn',
        'command',  # issue29298
    ):
        delattr(nsargs, arg)
    fn(**vars(nsargs))


if __name__ == '__main__':
    main()
