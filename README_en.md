# PgGraph
PostgreSQL tables dependency resolving utility.

Main functions:
- Recursive archiving/deletion of rows with the specified Primary Keys in given table
- List foreign-key dependencies for the specified table (referencing tables and tables referenced by current)
- List links to rows with the specified Primary Keys from other tables

## Configuration file - config.ini
Before using utility, you need to create a configuration file on you local machine:
```ini
[db]
host = localhost
port = 5432
user = postgres
password = postgres
dbname = postgres
schema = public ; Optional, default value specified

[archive]       ; Optional section, default values specified
is_debug = false
chunk_size = 1000
max_depth = 20
to_archive = true
archive_suffix = 'archive'
```

## Code Structure
- **core** - main functionality
    - **db** - functions and classes for working with the DB
        - archiver.py - tables archiving functionality
        - build_references.py - building a graph of dependencies between tables
    - **utils** - helper functions and classes
    - api.py - api class (PgGraphApi)
    - config.py - config file parsing
  

## Run Commands
You can run utility commands from the console, also you can work with it from code or interactive shells, such as IPython / JupyterLab.

### Run From Console

#### Console Parameters
Positional Args:
- action - требуемое действие: archive_table, get_table_references или get_rows_references

Named Args:
- --config_path - путь к конфиг-файлу
- --table - таблица с которой нужно совершить действие
- --ids - список id через запятую, пример - 1,2,3 (необязательный параметр) 
- --log_path - путь к папке для логов (необязательный параметр, по умолчанию - None)
- --log_level - уровень логирования (необязательный параметр, по умолчанию - INFO) 

```shell script
$ pggraph -h
usage: pggraph action [-h] --table TABLE [--ids IDS] [--config_path CONFIG_PATH]
positional arguments:
  action        required action: archive_table, get_table_references, get_rows_references

optional arguments:
  -h, --help                    show this help message and exit
  --table TABLE                 table name
  --ids IDS                     primary key ids, separated by comma, e.g. 1,2,3
  --config_path CONFIG_PATH     path to config.ini
  --log_path LOG_PATH           path to log dir
  --log_level LOG_LEVEL         log level (debug, info, error)
```

#### Command examples

Archivation of table
```shell script
$ pggraph archive_table --config_path config.hw.local.ini --table flights --ids 1,2,3
2020-06-20 19:27:44 INFO: flights - START
2020-06-20 19:27:44 INFO: flights - start archive_recursive 3 rows (depth=0)
2020-06-20 19:27:44 INFO:       START ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:       ticket_flights - start archive_recursive 3 rows (depth=1)
2020-06-20 19:27:44 INFO:               START ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:               boarding_passes - start archive_recursive 3 rows (depth=2)
2020-06-20 19:27:44 INFO:                       START ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:                       END ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:               boarding_passes - archive_by_ids 3 rows by ticket_no, flight_id
2020-06-20 19:27:44 INFO:               boarding_passes - start archive_recursive 3 rows (depth=2)
2020-06-20 19:27:44 INFO:                       START ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:                       END ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:               boarding_passes - archive_by_ids 3 rows by ticket_no, flight_id
2020-06-20 19:27:44 INFO:               boarding_passes - start archive_recursive 3 rows (depth=2)
2020-06-20 19:27:44 INFO:                       START ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:                       END ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:               boarding_passes - archive_by_ids 3 rows by ticket_no, flight_id
2020-06-20 19:27:44 INFO:               boarding_passes - start archive_recursive 3 rows (depth=2)
2020-06-20 19:27:44 INFO:                       START ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:                       END ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:               boarding_passes - archive_by_ids 3 rows by ticket_no, flight_id
2020-06-20 19:27:44 INFO:               END ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO:       ticket_flights - archive_by_ids 3 rows by ticket_no, flight_id
2020-06-20 19:27:44 INFO:       END ARCHIVE REFERRING TABLES
2020-06-20 19:27:44 INFO: flights - archive_by_ids 3 rows by id
2020-06-20 19:27:44 INFO: flights - END
```

List foreign-key dependencies for the specified table
```shell script
$ pggraph get_table_references --config_path config.hw.local.ini --table flights
{'in_refs': {'ticket_flights': [ForeignKey(pk_main='flight_id', pk_ref='ticket_no, flight_id', fk_ref='flight_id')]},
 'out_refs': {'aircrafts': [ForeignKey(pk_main='aircraft_code', pk_ref='flight_id', fk_ref='aircraft_code')],
              'airports': [ForeignKey(pk_main='airport_code', pk_ref='flight_id', fk_ref='arrival_airport'),
                           ForeignKey(pk_main='airport_code', pk_ref='flight_id', fk_ref='departure_airport')]}}
```

List links to rows with the specified Primary Keys from other tables
```shell script
$ pggraph get_rows_references --config_path config.hw.local.ini --table flights --ids 1,2,3
{1: {'ticket_flights': {'flight_id': [{'flight_id': 1,
                                       'ticket_no': '0005432816945'},
                                      {'flight_id': 1,
                                       'ticket_no': '0005432816941'}]}},
 2: {'ticket_flights': {'flight_id': [{'flight_id': 2,
                                       'ticket_no': '0005433101832'},
                                      {'flight_id': 2,
                                       'ticket_no': '0005433101864'},
                                      {'flight_id': 2,
                                       'ticket_no': '0005432919715'}]}},
 3: {'ticket_flights': {'flight_id': [{'flight_id': 3,
                                       'ticket_no': '0005432817560'},
                                      {'flight_id': 3,
                                       'ticket_no': '0005432817568'},
                                      {'flight_id': 3,
                                       'ticket_no': '0005432817559'}]}}}
```

### Run from iPython interactive shell
Archivation of table
```python
>>> from pg_graph.main import setup_logging
>>> setup_logging(log_level='DEBUG')
>>> from pg_graph.api import PgGraphApi
>>> api = PgGraphApi('config.hw.local.ini')
>>> api.archive_table('flights', [4,5])
2020-06-20 23:12:08 INFO: flights - START
2020-06-20 23:12:08 INFO: flights - start archive_recursive 2 rows (depth=0)
2020-06-20 23:12:08 INFO: 	START ARCHIVE REFERRING TABLES
2020-06-20 23:12:08 DEBUG: 	ticket_flights - ForeignKey(pk_main='flight_id', pk_ref='flight_id, ticket_no', fk_ref='flight_id')
2020-06-20 23:12:08 DEBUG: 	SQL('SELECT flight_id, ticket_no FROM bookings.ticket_flights WHERE (flight_id) IN (%s, %s)')
2020-06-20 23:12:08 INFO: 	ticket_flights - start archive_recursive 30 rows (depth=1)
2020-06-20 23:12:08 INFO: 		START ARCHIVE REFERRING TABLES
2020-06-20 23:12:08 DEBUG: 		boarding_passes - ForeignKey(pk_main='flight_id, ticket_no', pk_ref='flight_id, ticket_no', fk_ref='flight_id, ticket_no')
2020-06-20 23:12:08 INFO: 		boarding_passes - archive_by_fk 30 rows by ForeignKey(pk_main='flight_id, ticket_no', pk_ref='flight_id, ticket_no', fk_ref='flight_id, ticket_no')
2020-06-20 23:12:08 DEBUG: 		SQL('CREATE TABLE IF NOT EXISTS bookings.boarding_passes_archive (LIKE bookings.boarding_passes)')
2020-06-20 23:12:08 DEBUG: 		DELETE FROM boarding_passes by FK flight_id, ticket_no - 30 rows
2020-06-20 23:12:08 INFO: 		END ARCHIVE REFERRING TABLES
2020-06-20 23:12:08 INFO: 	ticket_flights - archive_by_ids 30 rows by flight_id, ticket_no
2020-06-20 23:12:08 DEBUG: 	SQL('CREATE TABLE IF NOT EXISTS bookings.ticket_flights_archive (LIKE bookings.ticket_flights)')
2020-06-20 23:12:08 DEBUG: 	DELETE FROM ticket_flights by flight_id, ticket_no - 30 rows
2020-06-20 23:12:08 DEBUG: 	INSERT INTO ticket_flights_archive - 30 rows
2020-06-20 23:12:08 INFO: 	ticket_flights - start archive_recursive 30 rows (depth=1)
2020-06-20 23:12:08 INFO: 		START ARCHIVE REFERRING TABLES
2020-06-20 23:12:08 DEBUG: 		boarding_passes - ForeignKey(pk_main='flight_id, ticket_no', pk_ref='flight_id, ticket_no', fk_ref='flight_id, ticket_no')
2020-06-20 23:12:08 INFO: 		boarding_passes - archive_by_fk 30 rows by ForeignKey(pk_main='flight_id, ticket_no', pk_ref='flight_id, ticket_no', fk_ref='flight_id, ticket_no')
2020-06-20 23:12:08 DEBUG: 		SQL('CREATE TABLE IF NOT EXISTS bookings.boarding_passes_archive (LIKE bookings.boarding_passes)')
2020-06-20 23:12:08 DEBUG: 		DELETE FROM boarding_passes by FK flight_id, ticket_no - 30 rows
2020-06-20 23:12:08 INFO: 		END ARCHIVE REFERRING TABLES
2020-06-20 23:12:08 INFO: 	ticket_flights - archive_by_ids 30 rows by flight_id, ticket_no
2020-06-20 23:12:08 DEBUG: 	SQL('CREATE TABLE IF NOT EXISTS bookings.ticket_flights_archive (LIKE bookings.ticket_flights)')
2020-06-20 23:12:08 DEBUG: 	DELETE FROM ticket_flights by flight_id, ticket_no - 30 rows
2020-06-20 23:12:08 DEBUG: 	INSERT INTO ticket_flights_archive - 30 rows
2020-06-20 23:12:08 INFO: 	ticket_flights - start archive_recursive 30 rows (depth=1)
2020-06-20 23:12:08 INFO: 		START ARCHIVE REFERRING TABLES
2020-06-20 23:12:08 DEBUG: 		boarding_passes - ForeignKey(pk_main='flight_id, ticket_no', pk_ref='flight_id, ticket_no', fk_ref='flight_id, ticket_no')
2020-06-20 23:12:08 INFO: 		boarding_passes - archive_by_fk 30 rows by ForeignKey(pk_main='flight_id, ticket_no', pk_ref='flight_id, ticket_no', fk_ref='flight_id, ticket_no')
2020-06-20 23:12:08 DEBUG: 		SQL('CREATE TABLE IF NOT EXISTS bookings.boarding_passes_archive (LIKE bookings.boarding_passes)')
2020-06-20 23:12:08 DEBUG: 		DELETE FROM boarding_passes by FK flight_id, ticket_no - 30 rows
2020-06-20 23:12:08 INFO: 		END ARCHIVE REFERRING TABLES
2020-06-20 23:12:08 INFO: 	ticket_flights - archive_by_ids 30 rows by flight_id, ticket_no
2020-06-20 23:12:08 DEBUG: 	SQL('CREATE TABLE IF NOT EXISTS bookings.ticket_flights_archive (LIKE bookings.ticket_flights)')
2020-06-20 23:12:08 DEBUG: 	DELETE FROM ticket_flights by flight_id, ticket_no - 30 rows
2020-06-20 23:12:08 DEBUG: 	INSERT INTO ticket_flights_archive - 30 rows
2020-06-20 23:12:08 INFO: 	ticket_flights - start archive_recursive 3 rows (depth=1)
2020-06-20 23:12:08 INFO: 		START ARCHIVE REFERRING TABLES
2020-06-20 23:12:08 DEBUG: 		boarding_passes - ForeignKey(pk_main='flight_id, ticket_no', pk_ref='flight_id, ticket_no', fk_ref='flight_id, ticket_no')
2020-06-20 23:12:08 INFO: 		boarding_passes - archive_by_fk 3 rows by ForeignKey(pk_main='flight_id, ticket_no', pk_ref='flight_id, ticket_no', fk_ref='flight_id, ticket_no')
2020-06-20 23:12:08 DEBUG: 		SQL('CREATE TABLE IF NOT EXISTS bookings.boarding_passes_archive (LIKE bookings.boarding_passes)')
2020-06-20 23:12:08 DEBUG: 		DELETE FROM boarding_passes by FK flight_id, ticket_no - 3 rows
2020-06-20 23:12:08 INFO: 		END ARCHIVE REFERRING TABLES
2020-06-20 23:12:08 INFO: 	ticket_flights - archive_by_ids 3 rows by flight_id, ticket_no
2020-06-20 23:12:08 DEBUG: 	SQL('CREATE TABLE IF NOT EXISTS bookings.ticket_flights_archive (LIKE bookings.ticket_flights)')
2020-06-20 23:12:08 DEBUG: 	DELETE FROM ticket_flights by flight_id, ticket_no - 3 rows
2020-06-20 23:12:08 DEBUG: 	INSERT INTO ticket_flights_archive - 3 rows
2020-06-20 23:12:08 INFO: 	END ARCHIVE REFERRING TABLES
2020-06-20 23:12:08 INFO: flights - archive_by_ids 2 rows by flight_id
2020-06-20 23:12:09 DEBUG: SQL('CREATE TABLE IF NOT EXISTS bookings.flights_archive (LIKE bookings.flights)')
2020-06-20 23:12:09 DEBUG: DELETE FROM flights by flight_id - 2 rows
2020-06-20 23:12:09 DEBUG: INSERT INTO flights_archive - 2 rows
2020-06-20 23:12:09 INFO: flights - END
```

List foreign-key dependencies for the specified table
```python
>>> from pg_graph.api import PgGraphApi
>>> from pprint import pprint
>>> api = PgGraphApi('config.hw.local.ini')
>>> res = api.get_table_references('flights')
>>> pprint(res)
{'in_refs': {'ticket_flights': [ForeignKey(pk_main='flight_id', pk_ref='flight_id, ticket_no', fk_ref='flight_id')]},
 'out_refs': {'aircrafts': [ForeignKey(pk_main='aircraft_code', pk_ref='flight_id', fk_ref='aircraft_code')],
              'airports': [ForeignKey(pk_main='airport_code', pk_ref='flight_id', fk_ref='arrival_airport'),
                           ForeignKey(pk_main='airport_code', pk_ref='flight_id', fk_ref='departure_airport')]}}
```

List links to rows with the specified Primary Keys from other tables
```python
>>> from pg_graph.api import PgGraphApi
>>> from pprint import pprint
>>> api = PgGraphApi('config.hw.local.ini')
>>> rows = api.get_rows_references('flights', [1,2,3])
>>> pprint(rows)
{1: {'ticket_flights': {'flight_id': [{'flight_id': 1,
                                       'ticket_no': '0005432816945'},
                                      {'flight_id': 1,
                                       'ticket_no': '0005432816941'}]}},
 2: {'ticket_flights': {'flight_id': [{'flight_id': 2,
                                       'ticket_no': '0005433101832'},
                                      {'flight_id': 2,
                                       'ticket_no': '0005433101864'},
                                      {'flight_id': 2,
                                       'ticket_no': '0005432919715'}]}},
 3: {'ticket_flights': {'flight_id': [{'flight_id': 3,
                                       'ticket_no': '0005432817560'},
                                      {'flight_id': 3,
                                       'ticket_no': '0005432817568'},
                                      {'flight_id': 3,
                                       'ticket_no': '0005432817559'}]}}}
```

## Author
- [Borzov Oleg](https://github.com/olegborzov) (Author)

## License
2020, Copyright Ⓒ, «Sberbank real estate center» Limited Liability Company.

MIT license.
