ncprivacy
=========

View saved macOS notifications and.. remove them.

- `Patrick Wardle <https://objective-see.com/blog/blog_0x2E.html>`_
- `Kinga Kieczkowska <https://kieczkowska.com/2020/05/20/macos-notifications-forensics/>`_

Installation
------------

.. code:: sh

    $ make install

or

.. code:: sh

    $ brew tap x31a/tap https://bitbucket.org/x31a/homebrew-tap.git
    $ brew install x31a/tap/ncprivacy

Usage
-----

.. code:: text

    usage: ncprivacy [-h] [-V] [--database PATH] [-i GLOB] [-e GLOB]
                     [--not-exclude-private] [--json]
                     {ls-apps,ls-records,rm,count} ...

    MacOS Notification Center Privacy

    positional arguments:
      {ls-apps,ls-records,rm,count}
        ls-apps             List identifier records from table `app`
        ls-records          List notification records from table `record`
        rm                  Delete records from tables [delivered, displayed,
                            record, requests, snoozed]
        count               Count records from tables [delivered, displayed,
                            record, requests, snoozed]

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

    usage: ncprivacy ls-records [-h] [--start-date ISO_DATETIME]
                                [--stop-date ISO_DATETIME] [--search REGEX]

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

    $ ncprivacy ls-apps

To dump all notifications as json:

.. code:: sh

    $ ncprivacy --json ls-records > notifications.json

To list some notifications:

.. code:: sh

    $ ncprivacy ls-records --start-date "2020-05-01"

To remove app notifications:

.. code:: sh

    $ ncprivacy -i "some.app.identifier" rm

Library
-------

.. code:: python

    import sqlite3

    from ncprivacy import ncprivacy

    # Use `None` as cursor for one time access
    cur = None

    for app in ncprivacy.iter_apps(cur):
        print(f"app_id:     {app.app_id}")
        print(f"identifier: {app.identifier}")

    # Do manual connection for multiple access
    conn = sqlite3.connect(ncprivacy.get_db_path())
    cur = conn.cursor()

    for record in ncprivacy.iter_records(cur):
        print(f"delivered: {record.delivered_date_ or ''}")
        data = record.get_useful_data()
        print(f" bundleid: {data.app  or ''}")
        print(f"    title: {data.titl or ''}")
        print(f" subtitle: {data.subt or ''}")
        print(f"     body: {data.body or ''}")

    identifier = 'some.app.identifier'
    assert (ncprivacy.count_privacy_records(cur, include=[identifier]) ==
            ncprivacy.rm_privacy_records(cur, include=[identifier]))

    cur.close()
    # After `rm_privacy_records` call, don't forget to commit
    conn.commit()
    conn.close()

Friends
-------

- `mac_apt <https://github.com/ydkhatri/mac_apt>`_
- `MacForensics <https://github.com/ydkhatri/MacForensics>`_
- `AuRevoir <https://github.com/objective-see/AuRevoir>`_
