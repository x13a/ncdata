# ncprivacy

View saved macOS notifications and.. remove them.

## Installation
```sh
$ make install
```
or
```sh
$ brew tap x31a/tap https://bitbucket.org/x31a/homebrew-tap.git
$ brew install x31a/tap/ncprivacy
```

## Usage
```text
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
```
```text
usage: ncprivacy ls-records [-h] [--start-date ISO_DATETIME]
                            [--stop-date ISO_DATETIME] [--pattern REGEX]

optional arguments:
  -h, --help            show this help message and exit
  --start-date ISO_DATETIME
                        Start datetime by field `delivered_date`
  --stop-date ISO_DATETIME
                        Stop datetime by field `delivered_date`
  --pattern REGEX       Search match in [title, subtitle, body]
```

## Example

To list identifiers:
```sh
$ ncprivacy ls-apps
```

To dump all notifications as json:
```sh
$ ncprivacy --json ls-records > notifications.json
```

To list some notifications:
```sh
$ ncprivacy ls-records --start-date "2020-05-01"
```

To remove app notifications:
```sh
$ ncprivacy -i "identifier" rm
```

## Friends
+ [mac_apt](https://github.com/ydkhatri/mac_apt)
+ [MacForensics](https://github.com/ydkhatri/MacForensics)
+ [AuRevoir](https://github.com/objective-see/AuRevoir)
