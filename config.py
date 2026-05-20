import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY          = os.getenv('SECRET_KEY', 'ram_factory_secret_2024')
    MYSQL_HOST          = os.getenv('MYSQL_HOST',     'localhost')
    MYSQL_USER          = os.getenv('MYSQL_USER',     'root')
    MYSQL_PASSWORD      = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB            = os.getenv('MYSQL_DB',       'ram_factory')
    MYSQL_CURSORCLASS   = 'DictCursor'
    GROQ_API_KEY        = os.getenv('GROQ_API_KEY', '')
