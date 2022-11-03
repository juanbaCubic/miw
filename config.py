import os
from typing import List, Type

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    CONFIG_NAME = "base"
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    CONFIG_NAME = "dev"
    SECRET_KEY = os.getenv(
        "DEV_SECRET_KEY", "Building with bricks and stones"
    )
    DEBUG = True
    TESTING = False
    ROLE_ARN = os.getenv("AWS_ROLE_ARN","arn:aws:iam::539711557251:role/TextractRole")
    REGION = os.getenv("AWS_REGION","eu-west-1")


class TestingConfig(BaseConfig):
    CONFIG_NAME = "test"
    SECRET_KEY = os.getenv("TEST_SECRET_KEY", "Testing with hammer")
    DEBUG = True
    TESTING = True


class ProductionConfig(BaseConfig):
    CONFIG_NAME = "prod"
    SECRET_KEY = os.getenv("PROD_SECRET_KEY", "Producing quality")
    DEBUG = False
    TESTING = False

EXPORT_CONFIGS: List[Type[BaseConfig]] = [
    DevelopmentConfig,
    TestingConfig,
    ProductionConfig,
]

config_by_name = {cfg.CONFIG_NAME: cfg for cfg in EXPORT_CONFIGS}
