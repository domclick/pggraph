"""
Copyright Ⓒ 2020 "Sberbank Real Estate Center" Limited Liability Company. Licensed under the MIT license.
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
                    raise KeyError(f'{field} is required')

        return cls(**fields)

    @classmethod
    def from_dict(cls, config_data: dict):
        fields = {}
        for field, field_type in cls.__annotations__.items():
            if field in config_data:
                value = config_data.get(field)
            elif hasattr(cls, field):
                value = getattr(cls, field)
            else:
                raise KeyError(f'{field} is required')

            if not isinstance(value, field_type):
                value_type = value.__class__.__name__
                correct_type = field_type.__name__
                raise ValueError(f'{field} value has incorrect type {value_type}, correct type - {correct_type}')

            fields[field] = value

        return cls(**fields)
