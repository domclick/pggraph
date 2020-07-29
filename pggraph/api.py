"""
Copyright Ⓒ 2020 "Sberbank Real Estate Center" Limited Liability Company. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
import logging
from argparse import Namespace
from typing import List, Dict

from psycopg2.extras import DictCursor
from psycopg2.sql import SQL

from pggraph.db import build_references as br
from pggraph.config import Config
from pggraph.db.archiver import Archiver
from pggraph.db.base import get_db_conn
from pggraph.utils.action_enum import ActionEnum
from pggraph.utils.funcs import chunks


class PgGraphApi:
    config: Config
    references: Dict[str, dict]
    primary_keys: Dict[str, str]

    def __init__(self, config_path: str = None, config: Config = None):
        if config_path:
            self.config = Config(config_path)
        elif config:
            self.config = config
        else:
            raise ValueError('config or config_path should be set')

        result = br.build_references(config=self.config)
        self.references = result['references']
        self.primary_keys = result['primary_keys']

    def run_action(self, args: Namespace):
        if args.action == ActionEnum.archive_table:
            return self.archive_table(args.table, ids=args.ids)
        elif args.action == ActionEnum.get_rows_references:
            return self.get_rows_references(args.table, ids=args.ids)
        elif args.action == ActionEnum.get_table_references:
            return self.get_table_references(args.table)
        else:
            raise NotImplementedError(f'Unknown action {args.action}')

    def archive_table(self, table_name, ids: List[int]):
        """
        Recursive iterative archiving / deleting rows by %ids% from %table_name% table and related tables.
        pk_column - %table_name% primary key
        """
        conn = get_db_conn(self.config)

        try:
            logging.info(f'{table_name} - START')

            pk_column = self.primary_keys.get(table_name)
            if not pk_column:
                raise KeyError(f'Primary key for table {table_name} not found')

            archiver = Archiver(conn, self.references, self.config)
            rows = [{pk_column: id_} for id_ in ids]

            for rows_chunk in chunks(rows, self.config.archiver_config.chunk_size):
                archiver.archive_recursive(table_name, rows_chunk, pk_column)

            logging.info(f'{table_name} - END')
        finally:
            conn.close()

    def get_table_references(self, table_name: str):
        """
        Get table references:
         - referencing tables (in_refs)
         - tables referenced by current (out_refs)

        Result (table_name = table_a):
        {
            'in_refs': {
                'table_b': [ForeignKey(pk_main='id', pk_ref='id', fk_ref='table_a_id')],
                'table_c': [ForeignKey(pk_main='id', pk_ref='id', fk_ref='a_id')]
            },
            'out_refs': {
                'table_d': [ForeignKey(pk_main='id', pk_ref='id', fk_ref='d_id')],
                'table_e': [ForeignKey(pk_main='id', pk_ref='id', fk_ref='table_e_id')],
            }
        }
        """
        if table_name not in self.references:
            raise KeyError(f'Table {table_name} not found')

        in_refs = {}
        for ref_table_name, ref_table_data in self.references[table_name].items():
            in_refs[ref_table_name] = ref_table_data['references']

        out_refs = {}
        for ref_table_name, table_refs in self.references.items():
            if table_name == ref_table_name:
                continue

            ref_to_table = table_refs.get(table_name)
            if ref_to_table:
                out_refs[ref_table_name] = ref_to_table['references']

        return {'in_refs': in_refs, 'out_refs': out_refs}

    def get_rows_references(self, table_name: str, ids: List[int]):
        """
        Get dictionary of links to %ids% rows in %table_name% table from other tables

        Result (table_name = table_a, ids = [1, 5, 6]):
        {
            1: {
                'table_b': {'table_a_id': [1, 4, 6]},
                'table_c': {'a_id': [29]},
            },
            5: {
                'table_b': {'table_a_id': []},
                'table_c': {'a_id': [12, 13]},
            },
            6: {
                'table_b': {'table_a_id': []},
                'table_c': {'a_id': []},
            }
        }
        """
        if table_name not in self.references:
            raise KeyError(f'Table {table_name} not found')

        rows_refs = {id_: {} for id_ in ids}
        s_in = ', '.join('%s' for _ in ids)
        conn = get_db_conn(self.config)
        try:
            for ref_table_name, ref_table_data in self.references[table_name].items():
                for ref_tables in rows_refs.values():
                    ref_tables[ref_table_name] = {fk.fk_ref: [] for fk in ref_table_data['references']}

                for fk in ref_table_data['references']:
                    query = SQL(
                        f"SELECT {fk.pk_ref}, {fk.fk_ref} "
                        f"FROM {self.config.db_config.schema}.{ref_table_name} "
                        f"WHERE {fk.fk_ref} IN ({s_in})"
                    )
                    with conn.cursor(cursor_factory=DictCursor) as curs:
                        curs.execute(query, ids)
                        result = curs.fetchall()
                        rows = [dict(row) for row in result]

                    for row in rows:
                        tmp = rows_refs[row[fk.fk_ref]][ref_table_name][fk.fk_ref]
                        tmp.append(row)
        finally:
            conn.close()

        return rows_refs
