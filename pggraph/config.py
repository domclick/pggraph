"""
Copyright Ⓒ 2020 "Sberbank Real Estate Center" Limited Liability Company. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
from configparser import ConfigParser
from dataclasses import dataclass

from pggraph.utils.classes.base import BaseConfig
from pggraph.utils.funcs import arg_to_bool


class Config:
    db_config: "DBConfig"
    archiver_config: "ArchiverConfig"

    def __init__(self, config_path: str = None, config_data: dict = None):
        if config_data:
            self.from_dict(config_data)
        elif config_path:
            self.from_ini(config_path)
        else:
            raise ValueError('config_path or config_data should be set')

    def from_ini(self, config_path: str):
        config = ConfigParser()
        config.read(config_path)
        self.db_config = DBConfig.from_config(config, 'db')
        self.archiver_config = ArchiverConfig.from_config(config, 'archive')

    def from_dict(self, config_data: dict):
        if not isinstance(config_data, dict):
            raise ValueError(f'config_data has incorrect type {config_data.__class__.__name__} (should be dict)')

        if 'db' in config_data:
            self.db_config = DBConfig.from_dict(config_data['db'])
        else:
            raise KeyError('config_data should contain db settings')

        self.archiver_config = ArchiverConfig.from_dict(config_data.get('archive', {}))


@dataclass
class DBConfig(BaseConfig):
    host: str
    port: int
    user: str
    password: str
    dbname: str
    schema: str = 'public'


@dataclass
class ArchiverConfig(BaseConfig):
    is_debug: bool = False
    chunk_size: int = 1000
    max_depth: int = 20
    to_archive: bool = True
    archive_suffix: str = 'archive'

    @classmethod
    def from_config(cls, config: ConfigParser, section: str):
        conf = super().from_config(config, section)
        conf.is_debug = arg_to_bool(str(conf.is_debug), default_value=cls.is_debug)
        conf.chunk_size = int(conf.chunk_size)
        conf.max_depth = int(conf.max_depth)
        conf.to_archive = arg_to_bool(str(conf.to_archive), default_value=cls.to_archive)
        return conf
