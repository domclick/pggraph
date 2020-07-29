"""
Copyright Ⓒ 2020 "Sberbank Real Estate Center" Limited Liability Company. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
import pytest

from pggraph.config import Config
from pggraph.db.base import get_db_conn


@pytest.fixture(scope="session", autouse=True)
def test_db():
    """
    This fixture will be executed once in the entire suite, independently of the filters you use
    running pytest. It will create the test_db at the beginning and droping the table at the end
    of all tests.
    """
    config = Config('config.test.ini')
    _create_db(config)
    _clear_tables(config)
    _fill_db(config)
    yield
    _drop_db(config)


def _create_db(config):
    connection = get_db_conn(config, with_db=False)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE {config.db_config.dbname};")
    except Exception as error:
        if not hasattr(error, "pgerror") or "already exists" not in error.pgerror:
            raise error
        print("Database '%s' already exists.", config.db_config.dbname)
    finally:
        connection.close()


def _kill_connections(config):
    connection = get_db_conn(config)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s;",
                (config.db_config.dbname, )
            )
    except Exception as err:
        print('error while kill conns', err)


def _drop_db(config):
    connection = get_db_conn(config, with_db=False)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"DROP DATABASE {config.db_config.dbname};")
    finally:
        connection.close()


def _clear_tables(config):
    connection = get_db_conn(config)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                DROP TABLE IF EXISTS publisher CASCADE;
                DROP TABLE IF EXISTS publisher_archive CASCADE;
                DROP TABLE IF EXISTS book CASCADE;
                DROP TABLE IF EXISTS book_archive CASCADE;
                DROP TABLE IF EXISTS author CASCADE;
                DROP TABLE IF EXISTS author_archive CASCADE;
                DROP TABLE IF EXISTS author_book CASCADE;
                DROP TABLE IF EXISTS author_book_archive CASCADE;
            """)
    except Exception as error:
        if not hasattr(error, "pgerror") or "does not exist" not in error.pgerror:
            raise error
        print("Database '%s' does not exist.", config.db_config.dbname)
    finally:
        connection.close()


def _fill_db(config):
    connection = get_db_conn(config)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS publisher (
                    id serial PRIMARY KEY,
                    name text NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS book (
                    id serial PRIMARY KEY,
                    name text NOT NULL,
                    publisher_id integer REFERENCES publisher (id)
                );
                
                CREATE TABLE IF NOT EXISTS author (
                    id serial PRIMARY KEY,
                    fio text NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS author_book (
                    author_id integer REFERENCES author (id),
                    book_id integer REFERENCES book (id),
                    PRIMARY KEY (author_id, book_id)
                );
                
                INSERT INTO publisher (id, name) VALUES (1, 'O Reilly'), (2, 'Packt'), (3, 'Bloomsbury');
                INSERT INTO book (id, name, publisher_id) VALUES 
                    (1, 'High Performance Python', 1), 
                    (2, 'Kubernetes: Up and Running', 1), 
                    (3, 'Python Machine Learning', 2),
                    (4, 'Harry Potter and the Philosophers Stone', 3),
                    (5, 'Harry Potter and the Chamber of Secrets', 3);
                INSERT INTO author (id, fio) VALUES 
                    (1, 'Ian Ozsvald'), (2, 'Micha Gorelick'), 
                    (3, 'Brendan Burns'), (4, 'Joe Beda'),
                    (5, 'Sebastian Raschka'), (6, 'Vahid Mirjalili'),
                    (7, 'J.K. Rowling');
                INSERT INTO author_book (author_id, book_id) VALUES 
                    (1, 1), (2, 1), 
                    (3, 2), (4, 2), 
                    (5, 3), (6, 3), 
                    (7, 4), (7, 5);
            """)
    finally:
        connection.close()
