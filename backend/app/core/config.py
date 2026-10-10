import pathlib

from starlette.config import Config

ROOT = pathlib.Path(__file__).resolve().parent.parent  # app/
BASE_DIR = ROOT.parent  # ./

config = Config(BASE_DIR / '.env')

MONGODB_URL = config('MONGODB_URL', str)

# API_USERNAME = config("API_USERNAME", str)
# API_PASSWORD = config("API_PASSWORD", str)

# Auth configs.
API_SECRET_KEY = config('API_SECRET_KEY', str)
# A publicly known key (e.g. the FastAPI tutorial example) would let anyone forge logins.
_PUBLIC_EXAMPLE_KEYS = {
    '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7',
}
if API_SECRET_KEY in _PUBLIC_EXAMPLE_KEYS or len(API_SECRET_KEY) < 32:
    raise RuntimeError(
        'API_SECRET_KEY is a public example or shorter than 32 chars; generate one: openssl rand -hex 32'
    )
API_ALGORITHM = config('API_ALGORITHM', str)
API_ACCESS_TOKEN_EXPIRE_MINUTES = config('API_ACCESS_TOKEN_EXPIRE_MINUTES', int)  # infinity

DATABASE_NAME = 'chargelogger'
COLLECTION_CARS = 'cars'
COLLECTION_CHARGES = 'charges'
COLLECTION_CPOS = 'cpos'
COLLECTION_EXPENSES = 'expenses'
COLLECTION_USERS = 'users'
COLLECTION_API_TOKENS = 'api_tokens'
COLLECTION_SITE_SETTINGS = 'site_settings'

# Long-lived personal access tokens issued by users to authenticate API clients.
API_TOKEN_PREFIX = 'clk_'

ALLOWED_HOSTS = '*'
PROJECT_NAME = 'EVLogger'
