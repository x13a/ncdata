import argparse
import functools
import itertools
import json
import pathlib

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
    sep_tmpl = ' {} '
    column_sep = sep_tmpl.format('|')
    delimiter_sep = sep_tmpl.format('+')
    delimiter = '{delimiter_sep}{row}{delimiter_sep}'.format(
        row=delimiter_sep.join(
            '-' * widths[idx] for idx in range(len(fields or rows[0]))
        ),
        delimiter_sep=delimiter_sep,
    )
    row_tmpl = f'{column_sep}{{row}}{column_sep}'
    print(delimiter)
    if fields:
        print(row_tmpl.format(row=column_sep.join(
            f'{field.upper():{widths[idx]}}'
            for idx, field in enumerate(fields)
        )))
        if len(rows) > 1:
            print(delimiter)
    for row in rows:
        print(row_tmpl.format(row=column_sep.join(
            f'{val:{widths[idx]}}' for idx, val in enumerate(row)
        )))
    print(delimiter)


def record_to_dict(record):
    result = record._asdict()
    result.update(
        uuid=str(record.uuid_),
        data=record.get_useful_data()._asdict(),
    )
    return result


@utils.with_db_connection
def ls_apps(as_json, *args, **kw):
    apps_gen = ncprivacy.iter_apps(*args, **kw)
    (
        print(json_dumps([app._asdict() for app in apps_gen]))
        if as_json else
        pprint_table(apps_gen, fields=ncprivacy.App._fields)
    )


@utils.with_db_connection
def ls_records(as_json, *args, **kw):
    records_gen = ncprivacy.iter_records(*args, **kw)
    if as_json:
        print(json_dumps(tuple(map(record_to_dict, records_gen))))
    else:
        first_rec = next(records_gen, None)
        if first_rec is None:
            return
        print()
        for num, record in enumerate(
            itertools.chain([first_rec], records_gen),
            start=1,
        ):
            print(f"#{num}")
            print(f"Delivered: {record.delivered_date_ or ''}")
            data = record.get_useful_data()
            print(f"Bundle ID: {data.app  or ''}")
            print(f"    Title: {data.titl or ''}")
            print(f" Subtitle: {data.subt or ''}")
            print(f"     Body: {data.body or ''}", end='\n\n')


@utils.with_db_connection
def rm(as_json, *args, **kw):
    result = ncprivacy.rm_privacy_records(*args, **kw)
    print(result if as_json else f"Deleted: {result}")


@utils.with_db_connection
def count(as_json, *args, **kw):
    print(ncprivacy.count_privacy_records(*args, **kw))


def parse_args(*args, **kw):
    parser = argparse.ArgumentParser(
        prog=lib_name,
        description=lib_doc,
    )
    parser.add_argument(
        '--version',
        action='version',
        version=lib_version,
    )
    group = parser.add_argument_group('common arguments')
    group.add_argument(
        '--db-path',
        type=pathlib.Path,
        help="Custom database path",
    )
    group.add_argument(
        '-i',
        '--include',
        action='append',
        metavar='EXPR',
        default=[],
        help="Filter by identifiers (SQL GLOB expr)",
    )
    group.add_argument(
        '-e',
        '--exclude',
        action='append',
        metavar='EXPR',
        default=[],
        help="Exclude by identifiers (SQL GLOB expr)",
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
    subparsers.add_parser(
        'ls-records',
        help=f"List notification records from table "
             f"`{ncprivacy.Record._table_name}`",
    ).set_defaults(fn=ls_records)
    nc_privacy_tables = ', '.join(ncprivacy.NC_PRIVACY_TABLES)
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
