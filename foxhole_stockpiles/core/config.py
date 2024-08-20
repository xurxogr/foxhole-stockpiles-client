import configparser
from functools import lru_cache
import json
import types
from typing import get_args, get_origin

from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings

from foxhole_stockpiles.core.env_interpolation import EnvInterpolation


def read_ini_file(file_path: str) -> dict[str, dict[str, str]]:
    """
    Read an INI file and return it as dictionary where the keys are sections and the values are dictionaries of key-value pairs.

    Args:
        file_path (str): The path to the INI file

    Returns:
        dict[str, dict[str, str]]: The INI file as a dictionary
    """
    config = configparser.ConfigParser(interpolation=EnvInterpolation())
    config.read(file_path)
    return {section.lower(): dict(config[section]) for section in config.sections()}

def write_ini_file(file_path: str, data: dict[str, dict[str, str]]):
    """
    Write a dictionary to an INI file.

    Args:
        file_path (str): The path to the INI file
        data (dict[str, dict[str, str]]): The data to write
    """
    config = configparser.ConfigParser()
    for section, section_data in data.items():
        if section_data:
            values = {key: value for key, value in section_data.items() if value}
            config[section.upper()] = values

    with open(file_path, "w") as file:
        config.write(file)

class SectionSettings(BaseSettings):
    model_config = ConfigDict(extra='ignore')

    @classmethod
    def from_dict(cls, data: dict):
        """
        Convert a dictionary to a class instance.

        Args:
            data (dict): The dictionary to convert
        """
        converted_data = {}
        for attr_name, attr_type in cls.__annotations__.items():
            if attr_name not in data:
                continue

            origin = get_origin(attr_type)
            if isinstance(attr_type, types.UnionType):
                args = get_args(attr_type)
                attr_type = next((arg for arg in args if arg is not type(None)), args[0])
            elif origin:
                attr_type = origin

            try:
                # list or dict
                if attr_type in [dict, list]:
                    converted_data[attr_name] = json.loads(data[attr_name]) if data[attr_name] else None
                # primitive types
                elif attr_type in [str, int, float]:
                    converted_data[attr_name] = attr_type(data[attr_name])
                elif attr_type == bool:
                    converted_data[attr_name] = data[attr_name].lower() in ['true', 'yes', '1']
                # anything else
                else:
                    converted_data[attr_name] = data[attr_name]
            except ValueError:
                converted_data[attr_name] = data[attr_name]

        return cls(**converted_data)

###### Sections of the INI
class KeybindSettings(SectionSettings):
    key: str | None = Field(description="Key to take a screenshot", default=None)

class ServerSettings(SectionSettings):
    token: str | None = Field(description="API token", default=None)
    url: str = Field(description="API URL", default="https://fs.veli.team/fs/ocr/scan_image")

# Sections. End

class AppSettings(BaseSettings):
    keybind: KeybindSettings | None = None
    server: ServerSettings | None = None

    @classmethod
    def from_ini(cls, file_name: str = 'config.ini'):
        """
        Read the settings from an INI file. Relative path from the project root.

        Args:
            file_name (str): The path to the INI file

        Returns:
            AppSettings: The settings
        """
        ini_data = read_ini_file(file_name)
        settings_data = {}
        for attr_name, attr_type in cls.__annotations__.items():
            if attr_name in ini_data:
                section_class = attr_type.__args__[0]  # Get the type from Optional
                section_data = ini_data[attr_name]
                settings_data[attr_name] = section_class.from_dict(section_data)

        # Initialize the settings with default values
        object = cls(**settings_data)
        for attr_name, attr_type in cls.__annotations__.items():
            if not getattr(object, attr_name):
                setattr(object, attr_name, attr_type.__args__[0]())

        return object

    def save(self, file_name: str = 'config.ini'):
        """
        Save the settings to the INI file.

        Args:
            file_name (str): The path to the INI file
        """
        write_ini_file(file_path=file_name, data=self.model_dump())


@lru_cache()
def get_settings():
    return AppSettings().from_ini()

settings = get_settings()
