import os


class Config(object):
    """
    Common configurations
    """
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False


class DevelopmentConfig(Config):
    """
    Development configurations
    """

    DEBUG = True
    
    # AWS variables
    S3_BUCKET = 'env-s-img1-bucket1'
    AWS_ACCESS_KEY_ID = 'XXXXXXXXXXXXXXXXXX'
    AWS_SECRET_ACCESS_KEY = 'XXXXXXXXXXXXXXXXXX'
    AWS_REGION = 'eu-west-1'

    # DB variables
    DATABASE_ENGINE = 'mysql'
    DB_HOST = 'XXXXXXXXXXX.rds.amazonaws.com'
    DB_USER = 'appuser'
    DB_PWD = 'password'
    DB_PORT = '3306'
    DB_NAME = 'download_images'
    DB_URI = '{}://{}:{}@{}:{}/{}'.format(
        DATABASE_ENGINE,
        DB_USER,
        DB_PWD,
        DB_HOST,
        DB_PORT,
        DB_NAME)

class ProductionConfig(Config):
    """
    Production configurations
    """

    DEBUG = False
 
    # AWS variables
    S3_BUCKET = 'env-p-img1-bucket1'
    AWS_ACCESS_KEY_ID = 'XXXXXXXXXXXXXXXXXX'
    AWS_SECRET_ACCESS_KEY = 'XXXXXXXXXXXXXXXXXX'
    AWS_REGION = 'eu-west-1'

    # DB variables
    DATABASE_ENGINE = 'mysql'
    DB_HOST = 'XXXXXXXXXXX.rds.amazonaws.com'
    DB_USER = 'appuser'
    DB_PWD = 'password'
    DB_PORT = '3306'
    DB_NAME = 'download_images'
    DB_URI = '{}://{}:{}@{}:{}/{}'.format(
        DATABASE_ENGINE,
        DB_USER,
        DB_PWD,
        DB_HOST,
        DB_PORT,
        DB_NAME)

app_config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}
