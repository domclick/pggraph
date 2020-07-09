"""
Copyright Ⓒ 2020 Sberbank Real Estate Centre LLC. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
from enum import Enum


class ActionEnum(Enum):
    archive_table = 'archive_table'
    get_table_references = 'get_table_references'
    get_rows_references = 'get_rows_references'

    @classmethod
    def list_values(cls):
        return [k.value for k in cls]
