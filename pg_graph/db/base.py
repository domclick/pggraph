"""
Copyright Ⓒ 2020 Sberbank Real Estate Centre LLC. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
import logging

import psycopg2
from psycopg2._psycopg import connection
from psycopg2.extras import DictCursor, LoggingConnection

from pg_graph.config import Config


def get_db_conn(config: Config, with_db: bool = True, with_schema: bool = False) -> connection:
    db_config_dict = config.db_config.as_dict().copy()
    if not with_db:
        db_config_dict.pop('dbname')
    if not with_schema:
        db_config_dict.pop('schema')

    conn = psycopg2.connect(**db_config_dict, cursor_factory=DictCursor, connection_factory=LoggingConnection)
    conn.initialize(logging.getLogger())

    return conn
