# ncprivacy

View saved macOS notifications and.. remove them all.

## Installation
```sh
$ make
$ make install
```
or
```sh
$ brew tap x31a/tap https://bitbucket.org/x31a/homebrew-tap.git
$ brew install x31a/tap/ncprivacy
```

## Usage
```text
usage: ncprivacy [-h] [--version] [--db-path DB_PATH] [-i EXPR] [-e EXPR]
                 [--not-exclude-private] [--json]
                 {ls-apps,ls-records,rm,count} ...

MacOS Notification Center Privacy

positional arguments:
  {ls-apps,ls-records,rm,count}
    ls-apps             List identifier records from table `app`
    ls-records          List notification records from table `record`
    rm                  Delete records from tables [displayed, delivered,
                        snoozed, record, requests]
    count               Count records from tables [displayed, delivered,
                        snoozed, record, requests]

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

common arguments:
  --db-path DB_PATH     Custom database path
  -i EXPR, --include EXPR
                        Filter by identifiers (SQL GLOB expr)
  -e EXPR, --exclude EXPR
                        Exclude by identifiers (SQL GLOB expr)
  --not-exclude-private
                        Do not exclude identifiers startswith underscore
  --json                JSON output
```

## Example

To list identifiers:
```sh
$ ncprivacy ls-apps
```

To list notifications:
```sh
$ ncprivacy ls-records
```

To remove app notifications:
```sh
$ ncprivacy -i ru.keepcoder.telegram rm
```

## Friends
+ [mac_apt](https://github.com/ydkhatri/mac_apt)
+ [MacForensics](https://github.com/ydkhatri/MacForensics)
+ [AuRevoir](https://github.com/objective-see/AuRevoir)
