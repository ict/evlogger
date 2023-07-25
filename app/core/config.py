import pathlib

from starlette.config import Config

ROOT = pathlib.Path(__file__).resolve().parent.parent  # app/
BASE_DIR = ROOT.parent  # ./

config = Config(BASE_DIR / ".env")

MONGODB_URL = config("MONGODB_URL", str)

API_USERNAME = config("API_USERNAME", str)
API_PASSWORD = config("API_PASSWORD", str)

# Auth configs.
API_SECRET_KEY = config("API_SECRET_KEY", str)
API_ALGORITHM = config("API_ALGORITHM", str)
API_ACCESS_TOKEN_EXPIRE_MINUTES = config(
    "API_ACCESS_TOKEN_EXPIRE_MINUTES", int
)  # infinity

DATABASE_NAME = 'chargelogger'
COLLECTION_CARS = 'cars'
COLLECTION_CHARGES = 'charges'
COLLECTION_CPOS = 'cpos'

ALLOWED_HOSTS = '*'
PROJECT_NAME = 'chargelogger'
