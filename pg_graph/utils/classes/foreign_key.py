"""
Copyright Ⓒ 2020 "Sberbank Real Estate Center" Limited Liability Company. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
from dataclasses import dataclass


@dataclass
class ForeignKey:
    pk_main: str    # Primary Key
    pk_ref: str     # referring table Primary Key
    fk_ref: str     # referring table Foreign Key
