"""
Copyright Ⓒ 2020 Sberbank Real Estate Centre LLC. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
from configparser import ConfigParser, NoSectionError, NoOptionError


class BaseConfig:
    def as_dict(self):
        return self.__dict__

    @classmethod
    def from_config(cls, config: ConfigParser, section: str):
        fields = {}
        for field in cls.__annotations__:
            try:
                fields[field] = config.get(section, field)
            except (NoSectionError, NoOptionError):
                if hasattr(cls, field):
                    fields[field] = getattr(cls, field)
                else:
                    raise KeyError(f'{field} not found in config')

        return cls(**fields)
