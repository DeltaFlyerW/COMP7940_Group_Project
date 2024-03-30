from src.util.projectRoot import projectRoot

from dataclasses import dataclass, fields, asdict
import configparser


@dataclass
class BaseConfig:
    _configPath: str
    _section: str
    _parser: configparser.ConfigParser

    @classmethod
    def load(cls):
        if True:
            cls.load_config_from_path()

    @classmethod
    def load_config_from_path(cls):
        cls._parser = configparser.ConfigParser()
        cls._parser.read((projectRoot / cls._configPath))

        fieldMap = {}
        for field in fields(cls):
            if field.name.startswith("_"):
                continue
            fieldMap[field.name.upper()] = field

        for key, value in cls._parser[cls._section].items():
            field = fieldMap.get(key.replace("_", '').upper())
            if not field:
                continue
            if field.type != str:
                value = field.type(value)
            setattr(cls, field.name, value)

    @classmethod
    def toDict(cls):
        result = {}
        for field in fields(cls):
            if field.name.startswith("_") or not hasattr(cls, field.name):
                continue
            value = getattr(cls, field.name)
            if value is not None:
                result[field.name] = value
        return result


def _initConfig(cls: BaseConfig):
    cls.load()
    return cls


@_initConfig
@dataclass
class ChatbotConfig(BaseConfig):
    _configPath = "config/chatbot.ini"
    _section = 'CHATGPT'

    basicUrl: str
    modelName: str
    apiVersion: str
    accessToken: str


@_initConfig
@dataclass
class TelegramConfig(BaseConfig):
    _configPath = "config/telegram.ini"
    _section = 'TELEGRAM'

    accessToken: str


@_initConfig
@dataclass
class DatabaseConfig(BaseConfig):
    _configPath = "config/database.ini"
    _section = 'SQLITE'

    provider: str
    filename: str
    host: str
    port: int
    user: str
    password: str
    db: str


