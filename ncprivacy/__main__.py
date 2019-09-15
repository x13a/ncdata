#!/usr/bin/env python3

import argparse
import pathlib

import ncprivacy
import utils


def pprint_table(rows, fields):
    if not rows:
        return
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


@utils.with_db_connection
def ls_apps(*args, **kw):
    pprint_table(tuple(ncprivacy.iter_apps(*args, **kw)),
                 ncprivacy.App._fields)


@utils.with_db_connection
def rm_apps(*args, **kw):
    print(f"Deleted: {ncprivacy.rm_apps(*args, **kw)}")


@utils.with_db_connection
def ls_records(*args, **kw):
    for num, record in enumerate(ncprivacy.iter_records(*args, **kw), start=1):
        if num == 1:
            print()
        print(f"#{num}")
        print(f"Delivered date: {record.delivered_date_}")
        data = record.data_
        print(f"Application: {data.get('app')}")
        req = data.get('req', {})
        print(f"Title: {req.get('titl')}")
        print(f"Subtitle: {req.get('subt')}")
        print(f"Body: {req.get('body')}", end='\n\n')


@utils.with_db_connection
def rm_privacy_records(*args, **kw):
    print(f"Deleted: {ncprivacy.rm_privacy_records(*args, **kw)}")


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
        help="Append identifier for filter query",
    )
    group.add_argument(
        '--not-skip-private',
        action='store_false',
        dest='skip_private',
        help="Do not skip private identifiers (startswith underscore)",
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
        'ls-records',
        help=f"List notification records from table "
             f"<{ncprivacy.Record._table_name}>",
    ).set_defaults(fn=ls_records)
    subparsers.add_parser(
        'rm-privacy-records',
        help=f"Delete records from tables "
             f"<{', '.join(ncprivacy.NC_PRIVACY_TABLES)}>",
    ).set_defaults(fn=rm_privacy_records)
    return parser.parse_args(*args, **kw)


def main(argv=None):
    nsargs = parse_args(argv)
    if nsargs.db_path is None:
        nsargs.db_path = ncprivacy.get_db_path()
    fn = nsargs.fn
    del nsargs.fn
    del nsargs.command  # issue29298
    fn(**vars(nsargs))


if __name__ == '__main__':
    main()
