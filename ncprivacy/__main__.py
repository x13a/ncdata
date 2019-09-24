#!/usr/bin/env python3

import argparse
import functools
import json
import pathlib

import ncprivacy
import utils

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


def iter_records(*args, **kw):
    for record in ncprivacy.iter_records(*args, **kw):
        result = record._asdict()
        del result['data']
        data = record.data_
        req = data.get('req', {})
        result.update(
            uuid=str(record.uuid_),
            app=data.get('app'),
            titl=req.get('titl'),
            subt=req.get('subt'),
            body=req.get('body'),
        )
        yield result


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
    records_gen = iter_records(*args, **kw)
    if as_json:
        print(json_dumps(tuple(records_gen)))
    else:
        for num, record in enumerate(records_gen, start=1):
            if num == 1:
                print()
            print(f"#{num}")
            date = record['delivered_date']
            print("Delivered date: {date}".format(
                date=date if date is None else
                utils.convert_osx_ts_to_dt(date))
            )
            print(f"Application: {record['app']}")
            print(f"Title: {record['titl']}")
            print(f"Subtitle: {record['subt']}")
            print(f"Body: {record['body']}", end='\n\n')


@utils.with_db_connection
def rm_privacy_records(as_json, *args, **kw):
    print_rm(ncprivacy.rm_privacy_records(*args, **kw), as_json)


@utils.with_db_connection
def count_privacy_records(as_json, *args, **kw):
    print_count(ncprivacy.count_privacy_records(*args, **kw), as_json)


def parse_args(*args, **kw):
    parser = argparse.ArgumentParser(
        prog=ncprivacy.__name__,
        description=ncprivacy.__doc__,
    )
    parser.add_argument(
        '--version',
        action='version',
        version=ncprivacy.__version__,
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
        metavar='IDENTIFIER',
        default=[],
        help="Filter by identifiers",
    )
    group.add_argument(
        '-e',
        '--excludes',
        action='append',
        metavar='EXPR',
        default=[],
        help="Exclude by identifiers (SQL LIKE expr)",
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
        nsargs.excludes.append(ncprivacy.LIKE_PRIVATE)
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
