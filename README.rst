ncdata
======

View saved macOS notifications and.. remove them.

- `Patrick Wardle <https://objective-see.com/blog/blog_0x2E.html>`_
- `Kinga Kieczkowska <https://kieczkowska.com/2020/05/20/macos-notifications-forensics/>`_

.. code:: text

    Starting from macOS Big Sur, Apple stopped to store years of notifications
    and now the database is limited to one week, after that period notifications
    will be automatically deleted.

Installation
------------

.. code:: sh

    $ make install

Usage
-----

.. code:: text

    usage: ncdata [-h] [-V] [--database PATH] [-i GLOB] [-e GLOB] [--not-exclude-private] [--json] {ls-apps,ls-records,rm,count} ...

    MacOS Notification Center Data

    positional arguments:
      {ls-apps,ls-records,rm,count}
        ls-apps             List identifier records from table `app`
        ls-records          List notification records from table `record`
        rm                  Delete records from tables [delivered, displayed, record, requests, snoozed]
        count               Count records from tables [delivered, displayed, record, requests, snoozed]

    optional arguments:
      -h, --help            show this help message and exit
      -V, --version         show program's version number and exit

    base arguments:
      --database PATH       Custom database path
      -i GLOB, --include GLOB
                            Filter by identifiers
      -e GLOB, --exclude GLOB
                            Exclude by identifiers
      --not-exclude-private
                            Do not exclude identifiers startswith underscore
      --json                JSON output

.. code:: text

    usage: ncdata ls-records [-h] [--start-date ISO_DATETIME] [--stop-date ISO_DATETIME] [--search REGEX]

    optional arguments:
      -h, --help            show this help message and exit
      --start-date ISO_DATETIME
                            Start datetime by field `delivered_date`
      --stop-date ISO_DATETIME
                            Stop datetime by field `delivered_date`
      --search REGEX        Search match in [title, subtitle, body]

Example
-------

To list identifiers:

.. code:: sh

    $ ncdata ls-apps

To dump all notifications as json:

.. code:: sh

    $ ncdata --json ls-records > notifications.json

To list some notifications:

.. code:: sh

    $ ncdata ls-records --start-date "2020-05-01"

To remove app notifications:

.. code:: sh

    $ ncdata -i "some.app.identifier" rm

Library
-------

.. code:: python

    import sqlite3

    import ncdata

    # Use `None` as cursor for one time access
    cur = None

    for app in ncdata.iter_apps(cur):
        print(f"app_id:     {app.app_id}")
        print(f"identifier: {app.identifier}")

    # Do manual connection for multiple access
    conn = sqlite3.connect(ncdata.get_db_path())
    cur = conn.cursor()

    for record in ncdata.iter_records(cur):
        print(f"delivered: {record.delivered_date_ or ''}")
        data = record.get_useful_data()
        print(f" bundleid: {data.app  or ''}")
        print(f"    title: {data.titl or ''}")
        print(f" subtitle: {data.subt or ''}")
        print(f"     body: {data.body or ''}")

    identifier = 'some.app.identifier'
    assert (ncdata.count_all_records(cur, include=[identifier]) ==
            ncdata.rm_all_records(cur, include=[identifier]))

    cur.close()
    # After `rm_all_records` call, don't forget to commit
    conn.commit()
    conn.close()

Friends
-------

- `mac_apt <https://github.com/ydkhatri/mac_apt>`_
- `MacForensics <https://github.com/ydkhatri/MacForensics>`_
- `AuRevoir <https://github.com/objective-see/AuRevoir>`_
