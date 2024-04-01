import os

from .projectRoot import projectRoot

from dataclasses import dataclass, fields, asdict
import configparser
import logging

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
        mode = os.environ.get("CURRENT_RUN_MODE")
        if cls._section == "MASTER":
            if mode == "docker":
                cls._section = "MASTER_DOCKER"
            else:
                cls._section = "MASTER_LOCAL"
        if mode == "docker":
            conf = os.environ["CONFIG_FILE"]
            cls._parser.read(conf)
        else:
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
            if value:
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

    basicUrl: str = ''
    modelName: str = ''
    apiVersion: str = ''
    accessToken: str = ''


@_initConfig
@dataclass
class MasterConfig(BaseConfig):
    _configPath = "config/master.ini"
    _section = 'MASTER'

    basicUrl: str = ''
    accessToken: str = ''


@_initConfig
@dataclass
class DiffusionConfig(BaseConfig):
    _configPath = "config/diffusion.ini"
    _section = 'DIFFUSION'

    host: str
    port: int
