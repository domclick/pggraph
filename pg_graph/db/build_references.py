"""
Copyright Ⓒ 2020 Sberbank Real Estate Centre LLC. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
import logging
from collections import OrderedDict
from typing import Set, Dict, List

from psycopg2._psycopg import connection

from pg_graph.config import Config, DBConfig
from pg_graph.utils.classes.foreign_key import ForeignKey
from pg_graph.db.base import get_db_conn


def build_references(config: Config, conn: connection = None) -> Dict[str, dict]:
    """
    Build a tables dependency graph

    Algorithm:
    1) Get all table names
    2) Get all Foreign Keys
    3) Build a tables dependency graph (references dict)
        For each table:
            For each child table:
                build dependency graph recursive

    Result:
    {
        'references': {
            'table_a': {
                'table_b': {
                    'references': [{'pk_ref': 'id', 'fk_ref': 'table_b_id'}]
                    'ref_tables': {
                        'table_c': {
                            'table_a': {},
                            'table_b': {}
                        },
                        ...
                    }
                },
                'table_c': {...}
            },
            'table_b': {...}
        },
        'primary_keys': {
            'table_a': 'id',
            'table_b': 'id',
            'table_c': 'id'
        }
    }
    """

    references = {}
    primary_keys = {}

    if not conn:
        conn = get_db_conn(config)

    try:
        tables = get_all_tables(conn, config.db_config)
        foreign_keys = get_all_fk(conn, config.db_config)

        for table in tables:
            references[table['table_name']] = {}

        for fk in foreign_keys:
            if not fk['ref_table'] in references[fk['main_table']]:
                references[fk['main_table']][fk['ref_table']] = {
                    'ref_tables': {},
                    'references': []
                }

            table_references = references[fk['main_table']][fk['ref_table']]['references']
            table_references.append(ForeignKey(
                pk_main=fk['main_table_column'],
                pk_ref=fk['ref_pk_columns'],
                fk_ref=fk['ref_fk_column'],
            ))

            primary_keys[fk['main_table']] = fk['main_table_column']

        if references:
            references = OrderedDict(sorted(references.items(), key=lambda row: len(row[1]), reverse=True))

        for parent, refs in references.items():
            for ref, ref_data in refs.items():
                visited = {parent, ref}
                ref_childs = ref_data['ref_tables']
                recursive_build(ref, ref_childs, references, visited)
    finally:
        conn.close()

    result = {
        'references': references,
        'primary_keys': primary_keys
    }
    return result


def recursive_build(parent_table: str,
                    parent_childs: dict,
                    references: Dict[str, dict],
                    visited: Set[str] = None,
                    depth: int = 1) -> Dict[str, dict]:
    if visited is None:
        visited = set()

    visited.add(parent_table)

    tabs = '*' * depth
    logging.debug(f'{tabs}{parent_table} start build')
    for ref_table in references[parent_table]:
        new_visited = visited.copy()
        if ref_table in visited:
            parent_childs[ref_table] = 'САМ НА СЕБЯ' if ref_table == parent_table else 'РЕКУРСИЯ'
            logging.debug(f'{tabs}*{ref_table} {parent_childs[ref_table]} - {visited}')

            continue

        parent_childs[ref_table] = {}
        parent_childs[ref_table] = recursive_build(
            ref_table, parent_childs[ref_table], references, new_visited, depth + 1
        )

    if parent_childs:
        parent_childs = OrderedDict(sorted(
            parent_childs.items(), key=lambda ref: len(ref[1]), reverse=True
        ))

    return parent_childs


def get_all_tables(conn, db_config: DBConfig) -> List[dict]:
    query = "SELECT * FROM information_schema.tables WHERE table_schema = %(schema)s"

    with conn.cursor() as curs:
        curs.execute(query.strip(), {'schema': db_config.schema})
        result = curs.fetchall()

    base_tables = [dict(row) for row in result if row['table_type'] == 'BASE TABLE']
    return base_tables


def get_all_fk(conn, db_config: DBConfig) -> List[dict]:
    query = """
        WITH contraints_columns_table AS (
            SELECT table_name,
                   constraint_catalog,
                   constraint_schema,
                   constraint_name,
                   constraint_type,
                   string_agg(distinct column_name, ', ') as column_name
            FROM (
              SELECT ccu_in.table_name,
                     ccu_in.constraint_catalog,
                     ccu_in.constraint_schema,
                     ccu_in.constraint_name,
                     tc_in.constraint_type,
                     kcu.column_name
                FROM information_schema.constraint_column_usage ccu_in
                INNER JOIN information_schema.table_constraints tc_in
                          ON ccu_in.constraint_name = tc_in.constraint_name
                              AND ccu_in.constraint_schema = tc_in.constraint_schema
                              AND ccu_in.constraint_catalog = tc_in.constraint_catalog
                INNER JOIN information_schema.key_column_usage kcu
                          ON ccu_in.constraint_name = kcu.constraint_name
                              AND ccu_in.constraint_schema = kcu.constraint_schema
                              AND ccu_in.constraint_catalog = kcu.constraint_catalog
              WHERE ccu_in.constraint_schema = %(schema)s
              ORDER BY ccu_in.constraint_catalog, ccu_in.constraint_schema, ccu_in.constraint_name,
                       kcu.ordinal_position
            ) as subq
            GROUP BY table_name, constraint_catalog, constraint_schema, constraint_name, constraint_type
        )
        SELECT
            ccu.table_name AS main_table,
            ccu.column_name AS main_table_column,
            tc.table_name AS ref_table,
            pk_table.column_name AS ref_pk_columns,
            kcu.column_name AS ref_fk_column
        
        FROM information_schema.table_constraints tc
        
        LEFT JOIN (
            select ccu_in.constraint_catalog, ccu_in.constraint_schema, ccu_in.constraint_name,
                   cct.table_name, cct.column_name
            FROM contraints_columns_table cct
            INNER JOIN information_schema.constraint_column_usage ccu_in
                ON ccu_in.table_catalog = cct.constraint_catalog
                AND ccu_in.table_schema = cct.constraint_schema
                AND ccu_in.table_name = cct.table_name
            WHERE lower(cct.constraint_type) in ('primary key')
        ) ccu ON tc.constraint_catalog = ccu.constraint_catalog
            AND tc.constraint_schema = ccu.constraint_schema
            AND tc.constraint_name = ccu.constraint_name
        
        LEFT JOIN (
            select * FROM contraints_columns_table cct
            WHERE lower(cct.constraint_type) in ('foreign key')
        ) kcu ON tc.constraint_catalog = kcu.constraint_catalog
            AND tc.constraint_schema = kcu.constraint_schema
            AND tc.constraint_name = kcu.constraint_name
        
        LEFT JOIN (
            select * FROM contraints_columns_table cct
            WHERE lower(cct.constraint_type) in ('primary key')
        ) pk_table ON pk_table.table_name = tc.table_name
        
        WHERE lower(tc.constraint_type) in ('foreign key') AND tc.constraint_schema = %(schema)s
        GROUP BY ccu.table_name, ccu.column_name, pk_table.column_name, tc.table_name, kcu.column_name
        ORDER BY ccu.table_name, tc.table_name;
    """

    with conn.cursor() as curs:
        curs.execute(query.strip(), {'schema': db_config.schema})
        result = curs.fetchall()

    foreign_keys = [dict(row) for row in result]
    return foreign_keys
