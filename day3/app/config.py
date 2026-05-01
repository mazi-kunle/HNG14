import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DATABASE_NAME = os.environ.get('MYSQL_DATABASE', 'day1_db')
    DATABASE_USER = os.environ.get('MYSQLUSER', 'user')
    DATABASE_PASSWORD = os.environ.get('MYSQLPASSWORD', 'password')
    DATABASE_HOST = os.environ.get('MYSQLHOST', 'localhost')
    DATABASE_PORT = os.environ.get('MYSQLPORT', '3306')


    DATABASE_URI = (
        f'mysql+pymysql://{DATABASE_USER}:'
        f'{DATABASE_PASSWORD}@'
        f'{DATABASE_HOST}:'
        f'{DATABASE_PORT}/'
        f'{DATABASE_NAME}'
    )

    # Github Auth
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")

    GITHUB_CLI_CLIENT_ID = os.getenv("GITHUB_CLI_CLIENT_ID")
    GITHUB_CLI_CLIENT_SECRET = os.getenv("GITHUB_CLI_CLIENT_SECRET")
    GITHUB_CLI_REDIRECT_URI = os.getenv("GITHUB_CLI_REDIRECT_URI")
    
    # Token expiry (in seconds)
    ACCESS_TOKEN_EXPIRY = 5 * 60       # 3 minutes
    REFRESH_TOKEN_EXPIRY = 5 * 60      # 5 minutes

    # Rate limiting
    RATELIMIT_AUTH = "10 per minute"
    RATELIMIT_DEFAULT = "60 per minute"

    # secret key
    SECRET_KEY = os.getenv('SECRET_KEY')