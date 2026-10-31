import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()

database_url = os.environ.get('DATABASE_URL') or 'sqlite:///surm_store.db'
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'surm-store-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True, 'pool_recycle': 300}
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    BACKUP_DIR = os.environ.get('BACKUP_DIR') or 'backups/'
    STORE_NAME = 'Surm Store'
    STORE_ADDRESS = 'Bogoso, Western Region, Ghana'
    STORE_PHONE = '+233-XX-XXX-XXXX'
    STORE_EMAIL = 'info@surmstore.com'
    ITEMS_PER_PAGE = 25
    VAT_RATE = 0.15
    LOW_STOCK_THRESHOLD = 10

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_SECURE = True

config = {'development': DevelopmentConfig, 'production': ProductionConfig, 'default': DevelopmentConfig}
