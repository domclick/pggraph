"""
Copyright Ⓒ 2020 "Sberbank Real Estate Center" Limited Liability Company. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
import logging
from typing import List

from psycopg2._json import Json
from psycopg2._psycopg import connection
from psycopg2.extras import execute_values, DictCursor
from psycopg2.sql import SQL

from pg_graph.config import Config
from pg_graph.utils.classes.foreign_key import ForeignKey

TAB_SYMBOL = '\t'


class Archiver:
    conn: connection
    config: Config
    current_depth: int
    references: dict

    def __init__(self, conn: connection, references: dict, config: Config):
        self.conn = conn
        self.config = config
        self.current_depth = 0
        self.references = references

    def archive_recursive(self, table_name: str, rows: List[dict], pk_cols: str = 'id'):
        """
        Recursive archiving/clearing table
        Algorithm:
            - For each dependency of the table (ref_table)
                - For each Foreign Key, referencing to the main table
                    If dependent table doesn't have its own dependencies
                        archive the table by Foreign Keys and move on to the next dependency
                    If dependent table has its own dependencies
                        archive rows, using archive_recursive
            - After archiving all the dependencies, archive the main table

        :param table_name: name of the table to be archived
        :param rows: list of archived row IDs
        :param pk_cols: Primary Key columns
        """
        tabs = TAB_SYMBOL*self.current_depth

        logging.info(f'{tabs}{table_name} - start archive_recursive {len(rows)} rows (depth={self.current_depth})')

        if self.current_depth >= self.config.archiver_config.max_depth:
            logging.info(f'{tabs}{table_name} - MAX_DEPTH exceeded (depth={self.current_depth})')
            return

        if not rows:
            logging.info(f'{tabs}{table_name} - EMPTY rows - return')
            return

        tabs = tabs + TAB_SYMBOL
        self.current_depth += 1

        logging.info(f'{tabs}START ARCHIVE REFERRING TABLES')

        for ref_table, ref_data in self.references[table_name].items():
            for ref_fk in ref_data['references']:
                logging.debug(f'{tabs}{ref_table} - {ref_fk}')

                if self.config.archiver_config.is_debug:
                    self.archive_recursive(ref_table, rows, ref_fk.pk_ref)
                    continue

                if not self.references.get(ref_table):
                    self.archive_by_fk(ref_table, ref_fk, fk_rows=rows)
                    continue

                with self.conn.cursor(cursor_factory=DictCursor) as cursor:
                    self.select_rows_by_fk(cursor, table_name=ref_table, fk=ref_fk, rows=rows, tabs=tabs)
                    ref_rows_chunk = cursor.fetchmany(size=self.config.archiver_config.chunk_size)
                    while ref_rows_chunk:
                        self.archive_recursive(ref_table, ref_rows_chunk, ref_fk.pk_ref)
                        ref_rows_chunk = cursor.fetchmany(size=self.config.archiver_config.chunk_size)

        logging.info(f'{tabs}END ARCHIVE REFERRING TABLES')

        self.current_depth -= 1
        self.archive_by_ids(table_name=table_name, pk_columns=pk_cols, row_pks=rows)

    def archive_by_fk(self, table_name: str, fk: ForeignKey, fk_rows: List[dict]):
        """
        Archiving a table with the specified foreign keys

        :param table_name: name of the table to be archived
        :param fk: ForeignKey object
        :param fk_rows: foreign key values to be archived
        """
        tabs = TAB_SYMBOL*self.current_depth
        logging.info(f'{tabs}{table_name} - archive_by_fk {len(fk_rows)} rows by {fk}')

        if self.config.archiver_config.is_debug:
            return

        total_archived_rows = 0
        with self.conn:  # транзакция
            if self.config.archiver_config.to_archive:
                archive_table_name = self.create_archive_table(table_name, tabs=tabs)

            with self.conn.cursor(cursor_factory=DictCursor) as cursor:
                self.delete_rows_by_fk(cursor, table_name=table_name, fk=fk, fk_rows=fk_rows, tabs=tabs)

                if self.config.archiver_config.to_archive:
                    rows_chunk = cursor.fetchmany(size=self.config.archiver_config.chunk_size)
                    while rows_chunk:
                        total_archived_rows += len(rows_chunk)
                        self.insert_rows(archive_table_name=archive_table_name, values=rows_chunk, tabs=tabs)
                        rows_chunk = cursor.fetchmany(size=self.config.archiver_config.chunk_size)

        return total_archived_rows

    def archive_by_ids(self, table_name: str, pk_columns: str, row_pks: List[dict]):
        """
        Archiving a table with the specified primary keys

        :param table_name: name of the table to be archived
        :param pk_columns: primary key columns
        :param row_pks: primary keys values to be archived
        """
        tabs = TAB_SYMBOL*self.current_depth
        logging.info(f'{tabs}{table_name} - archive_by_ids {len(row_pks)} rows by {pk_columns}')

        if self.config.archiver_config.is_debug:
            return

        total_archived_rows = 0
        with self.conn:  # транзакция
            if self.config.archiver_config.to_archive:
                archive_table_name = self.create_archive_table(table_name, tabs=tabs)

            with self.conn.cursor(cursor_factory=DictCursor) as cursor:
                self.delete_rows_by_ids(cursor, table_name=table_name, pk_columns=pk_columns, rows=row_pks, tabs=tabs)

                if self.config.archiver_config.to_archive:
                    rows_chunk = cursor.fetchmany(size=self.config.archiver_config.chunk_size)
                    while rows_chunk:
                        total_archived_rows += len(rows_chunk)
                        self.insert_rows(archive_table_name=archive_table_name, values=rows_chunk, tabs=tabs)
                        rows_chunk = cursor.fetchmany(size=self.config.archiver_config.chunk_size)

        return total_archived_rows

    def create_archive_table(self, table_name: str, tabs: str) -> str:
        new_table_name = f"{table_name}_{self.config.archiver_config.archive_suffix}"
        query = SQL(
            f"CREATE TABLE IF NOT EXISTS {self.config.db_config.schema}.{new_table_name} "
            f"(LIKE {self.config.db_config.schema}.{table_name})"
        )

        with self.conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(query)

        logging.debug(f"{tabs}{query}")

        return new_table_name

    def insert_rows(self, archive_table_name: str, values: List[dict], tabs: str):
        column_names = ', '.join(values[0].keys())
        query = SQL(f'INSERT INTO {self.config.db_config.schema}.{archive_table_name} ({column_names}) VALUES %s')

        # Convert dict to json
        for row in values:
            for col_name, col_val in row.items():
                if isinstance(col_val, dict):
                    row[col_name] = Json(col_val)

        logging.debug(f"{tabs}INSERT INTO {archive_table_name} - {len(values)} rows")
        with self.conn.cursor(cursor_factory=DictCursor) as cursor:
            execute_values(cursor, query, values)

    def delete_rows_by_fk(self, cursor, table_name: str, fk: ForeignKey, fk_rows: List, tabs: str):
        pk_cols = fk.pk_main.split(', ')
        row_ids = [tuple(row[pk] for pk in pk_cols) for row in fk_rows]
        in_s = ', '.join('%s' for _ in range(len(fk_rows)))

        query = SQL(
            f"DELETE FROM {self.config.db_config.schema}.{table_name} WHERE ({fk.fk_ref}) IN ({in_s}) RETURNING *"
        )

        logging.debug(f"{tabs}DELETE FROM {table_name} by FK {fk.fk_ref} - {len(fk_rows)} rows")
        cursor.execute(query, row_ids)

    def delete_rows_by_ids(self, cursor, table_name: str, pk_columns: str, rows: List[dict], tabs: str):
        pk_cols = [pk.strip() for pk in pk_columns.split(',')]
        row_ids = [tuple(row[pk] for pk in pk_cols) for row in rows]
        in_s = ', '.join('%s' for _ in range(len(rows)))

        query = SQL(
            f"DELETE FROM {self.config.db_config.schema}.{table_name} "
            f"WHERE ({pk_columns}) IN ({in_s}) RETURNING *"
        )

        logging.debug(f"{tabs}DELETE FROM {table_name} by {pk_columns} - {len(rows)} rows")
        cursor.execute(query, row_ids)

    def select_rows_by_fk(self, cursor, table_name: str, fk: ForeignKey, rows: List[dict], tabs: str):
        pk_cols = fk.pk_main.split(', ')
        row_ids = [tuple(row[pk] for pk in pk_cols) for row in rows]
        in_s = ', '.join('%s' for _ in range(len(rows)))

        query = SQL(
            f"SELECT {fk.pk_ref} FROM {self.config.db_config.schema}.{table_name} "
            f"WHERE ({fk.fk_ref}) IN ({in_s})"
        )

        logging.debug(f"{tabs}{query}"[:100])
        cursor.execute(query, row_ids)
