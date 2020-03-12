import argparse
import functools
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


def pprint_table(rows, fields):
    if not rows:
        return
    assert len(rows[0]) == len(fields)
    align_vals = [
        max(len(max(column_vals, key=len)), len(fields[idx]))
        for idx, column_vals in
        enumerate(zip(*(map(str, row) for row in rows)))
    ]
    delimiter = ' | '
    line_tmpl = f'{delimiter}{{line}}{delimiter}'
    print(line_tmpl.format(line=delimiter.join(
        f'{field.upper():{align_vals[idx]}}' for
        idx, field in enumerate(fields)
    )))
    for row in rows:
        print(line_tmpl.format(line=delimiter.join(
            f'{val:{align_vals[idx]}}' for idx, val in enumerate(row)
        )))


def print_rm(result, as_json):
    print(json_dumps(result) if as_json else f"Deleted: {result}")


def print_count(result, as_json):
    print(json_dumps(result) if as_json else result)


def record_to_json(record):
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
        pprint_table(tuple(apps_gen), ncprivacy.App._fields)
    )


@utils.with_db_connection
def rm_apps(as_json, *args, **kw):
    print_rm(ncprivacy.rm_apps(*args, **kw), as_json)


@utils.with_db_connection
def count_apps(as_json, *args, **kw):
    print_count(ncprivacy.count_apps(*args, **kw), as_json)


@utils.with_db_connection
def ls_records(as_json, *args, **kw):
    records_gen = ncprivacy.iter_records(*args, **kw)
    if as_json:
        print(json_dumps(tuple(map(record_to_json, records_gen))))
    else:
        for num, record in enumerate(records_gen, start=1):
            if num == 1:
                print()
            print(f"#{num}")
            print(f"Delivered date: {record.delivered_date_}")
            data = record.get_useful_data()
            print(f"Application: {data.app}")
            print(f"Title: {data.titl}")
            print(f"Subtitle: {data.subt}")
            print(f"Body: {data.body}", end='\n\n')


@utils.with_db_connection
def rm_privacy_records(as_json, *args, **kw):
    print_rm(ncprivacy.rm_privacy_records(*args, **kw), as_json)


@utils.with_db_connection
def count_privacy_records(as_json, *args, **kw):
    print_count(ncprivacy.count_privacy_records(*args, **kw), as_json)


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
        '--identifiers',
        action='append',
        metavar='EXPR',
        default=[],
        help="Filter by identifiers (SQL GLOB expr)",
    )
    group.add_argument(
        '-e',
        '--excludes',
        action='append',
        metavar='EXPR',
        default=[],
        help="Exclude by identifiers (SQL GLOB expr)",
    )
    group.add_argument(
        '--not-skip-private',
        action='store_false',
        dest='skip_private',
        help="Do not skip private identifiers (startswith underscore)",
    )
    group.add_argument(
        '--json',
        action='store_true',
        dest='as_json',
        help="JSON output",
    )
    subparsers = parser.add_subparsers(required=True, dest='command')
    app_tname = ncprivacy.App._table_name
    subparsers.add_parser(
        'ls-apps',
        help=f"List identifier records from table <{app_tname}>",
    ).set_defaults(fn=ls_apps)
    subparsers.add_parser(
        'rm-apps',
        help=f"Delete app records from table <{app_tname}> (app_deleted "
             f"trigger will cleanup other tables related to them)",
    ).set_defaults(fn=rm_apps)
    subparsers.add_parser(
        'count-apps',
        help=f"Count app records from table <{app_tname}>",
    ).set_defaults(fn=count_apps)
    subparsers.add_parser(
        'ls-records',
        help=f"List notification records from table "
             f"<{ncprivacy.Record._table_name}>",
    ).set_defaults(fn=ls_records)
    nc_privacy_tables = ', '.join(ncprivacy.NC_PRIVACY_TABLES)
    subparsers.add_parser(
        'rm-privacy-records',
        help=f"Delete records from tables <{nc_privacy_tables}>",
    ).set_defaults(fn=rm_privacy_records)
    subparsers.add_parser(
        'count-privacy-records',
        help=f"Count records from tables <{nc_privacy_tables}>",
    ).set_defaults(fn=count_privacy_records)
    return parser.parse_args(*args, **kw)


def main(argv=None):
    nsargs = parse_args(argv)
    if nsargs.db_path is None:
        nsargs.db_path = ncprivacy.get_db_path()
    if nsargs.skip_private:
        nsargs.excludes.append(ncprivacy.GLOB_PRIVATE)
    fn = nsargs.fn
    for arg in (
        'skip_private',
        'fn',
        'command',  # issue29298
    ):
        delattr(nsargs, arg)
    fn(**vars(nsargs))


if __name__ == '__main__':
    main()
