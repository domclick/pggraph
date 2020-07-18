"""
Copyright Ⓒ 2020 "Sberbank Real Estate Center" Limited Liability Company. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
from pg_graph.api import PgGraphApi
from pg_graph.db.base import get_db_conn
from pg_graph.utils.classes.foreign_key import ForeignKey


def test_get_table_references():
    api = PgGraphApi(config_path='config.test.ini')

    publisher_refs = api.get_table_references('publisher')
    assert publisher_refs == {
        'in_refs': {'book': [ForeignKey(pk_main='id', pk_ref='id', fk_ref='publisher_id')]}, 'out_refs': {}
    }

    author_book_refs = api.get_table_references('author_book')
    assert author_book_refs == {
        'in_refs': {},
        'out_refs': {
            'book': [ForeignKey(pk_main='id', pk_ref='author_id, book_id', fk_ref='book_id')],
            'author': [ForeignKey(pk_main='id', pk_ref='author_id, book_id', fk_ref='author_id')]
        }
    }


def test_get_rows_references():
    api = PgGraphApi(config_path='config.test.ini')

    publisher_refs = api.get_rows_references('publisher', [1, 2])
    assert publisher_refs == {
        1: {'book': {'publisher_id': [{'id': 1, 'publisher_id': 1}, {'id': 2, 'publisher_id': 1}]}},
        2: {'book': {'publisher_id': [{'id': 3, 'publisher_id': 2}]}}
    }

    author_refs = api.get_rows_references('author', [1, 2])
    assert author_refs == {
        1: {'author_book': {'author_id': [{'author_id': 1, 'book_id': 1}]}},
        2: {'author_book': {'author_id': [{'author_id': 2, 'book_id': 1}]}}
    }


def test_archive_table():
    api = PgGraphApi(config_path='config.test.ini')

    api.archive_table('publisher', [1, 2])
    conn = get_db_conn(api.config)
    with conn.cursor() as cursor:
        cursor.execute('SELECT author_id, book_id FROM author_book;')
        ab_rows = [dict(row) for row in cursor.fetchall()]

        cursor.execute('SELECT author_id, book_id FROM author_book_archive;')
        ab_archive_rows = [dict(row) for row in cursor.fetchall()]

        cursor.execute('SELECT id FROM book;')
        book_rows = [dict(row) for row in cursor.fetchall()]

        cursor.execute('SELECT id FROM book_archive;')
        book_archive_rows = [dict(row) for row in cursor.fetchall()]

        cursor.execute('SELECT id FROM publisher;')
        pub_rows = [dict(row) for row in cursor.fetchall()]

        cursor.execute('SELECT id FROM publisher_archive;')
        pub_archive_rows = [dict(row) for row in cursor.fetchall()]

    conn.close()

    assert ab_rows == [{'author_id': 7, 'book_id': 4}, {'author_id': 7, 'book_id': 5}]
    assert ab_archive_rows == [
        {'author_id': 1, 'book_id': 1}, {'author_id': 2, 'book_id': 1}, {'author_id': 3, 'book_id': 2},
        {'author_id': 4, 'book_id': 2}, {'author_id': 5, 'book_id': 3}, {'author_id': 6, 'book_id': 3}
    ]

    assert book_rows == [{'id': 4}, {'id': 5}]
    assert book_archive_rows == [{'id': 1}, {'id': 2}, {'id': 3}]

    assert pub_rows == [{'id': 3}]
    assert pub_archive_rows == [{'id': 1}, {'id': 2}]
