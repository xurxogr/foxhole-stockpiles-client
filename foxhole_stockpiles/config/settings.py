from configparser import ConfigParser
import json
import logging
from typing import Final

from foxhole_stockpiles.config.env_interpolation import EnvInterpolation
from foxhole_stockpiles.models.singleton.singletonmeta import SingletonMeta


class Settings(metaclass=SingletonMeta):
    __FILE_NAME: Final = 'config.ini'
    SECTION_KEYBIND: Final = 'KEYBIND'
    SECTION_SERVER: Final = 'SERVER'
    SECTION_LOGGING: Final = 'LOGGING'

    # Keybind options
    OPTION_KEY: Final = 'KEY'

    # Server options
    OPTION_URL: Final = 'URL'
    OPTION_TOKEN: Final = 'TOKEN'

    # Logging options
    OPTION_LOG_LEVEL: Final = 'log_level'
    OPTION_LOGGERS: Final = 'loggers'

    # Hardcoded values
    DEFAULT_URL: Final = 'https://fs.veli.team'

    def __init__(self) -> None:
        self.__config_parser = None

        self.__config_parser = ConfigParser(interpolation=EnvInterpolation())
        self.__config_parser.read(self.__FILE_NAME)

        self.__check_section(section=Settings.SECTION_KEYBIND, options=[Settings.OPTION_KEY])
        self.__check_section(section=Settings.SECTION_SERVER, options=[Settings.OPTION_URL, Settings.OPTION_TOKEN])

        section = Settings.SECTION_SERVER
        option = Settings.OPTION_URL
        url = self.__config_parser.get(section=section, option=option)
        if not url:
            self.__config_parser.set(section=section, option=option, value=Settings.DEFAULT_URL)

        self.__init_logging()

    def get_section(self, section: str) -> dict:
        """
        gets a section from the config
        :param section: str = Name of the section
        :returns dict: Section as dictionary
        """

        return self.get_sections([ section ])

    def get_sections(self, sections: list) -> dict:
        """
        gets multiple sections from the config. If the same option exists in multiple sections it will be overwritten
        :param sections: list = List of sections to read
        :returns dict: Sections as dictionary
        """
        options = {}
        for section in sections:
            if self.__config_parser.has_section(section):
                options.update(dict(self.__config_parser[section]))

        return options

    def get(self, section: str, option: str) -> str:
        """
        gets an option from a section
        :param section: str = Section to read from
        :param option: str = Option to read from
        :returns str: Returns the value read
        """
        return self.__config_parser.get(section=section, option=option)

    def set(self, section: str, option: str, value: any):
        """
        sets option for a section
        :param section: str = Section
        :param option: str = Option
        :param value: any = Value to set
        """
        return self.__config_parser.set(section=section, option=option, value=value)

    def save(self):
        """
        Saves the config to file
        """
        with open(self.__FILE_NAME, 'w') as file:
            self.__config_parser.write(file)

    def __check_section(self, section: str, options: list[str]):
        """Checks for needed options in a section"""
        if not self.__config_parser.has_section(section):
            self.__config_parser.add_section(section)
            #raise NoSectionError(section)

        for option in options:
            if not self.__config_parser.has_option(section, option):
                self.__config_parser.set(section=section, option=option, value='')
                #raise NoOptionError(option, section)

    def __init_logging(self):
        """Checks for needed options in logging section (optional)"""
        section = self.SECTION_LOGGING
        if not self.__config_parser.has_section(section):
            logging.basicConfig(level='INFO')
            return

        log_level = self.__config_parser.get(section=section, option=self.OPTION_LOG_LEVEL) or 'INFO'
        loggers = self.__config_parser.get(section=section, option=self.OPTION_LOGGERS) or '{}'
        logging.basicConfig(level=log_level)
        loggers = json.loads(loggers)
        for logger, name_level in loggers.items():
            try:
                log_level = logging._nameToLevel.get(name_level, logging.WARNING)
                logging.getLogger(logger).setLevel(level=log_level)
            except:
                pass
