"""
Copyright Ⓒ 2020 Sberbank Real Estate Centre LLC. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
from distutils.util import strtobool


def chunks(elems: list, step_size: int):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(elems), step_size):
        yield elems[i:i + step_size]


def arg_to_bool(value: str, default_value: bool = False) -> bool:
    return bool(strtobool(value or str(default_value)))
