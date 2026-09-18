"""Repository paths and environment loading, independent of the launch directory."""
import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / 'data'
ENV_FILE = BACKEND_DIR / '.env'
# An explicitly supplied environment variable takes precedence over the local file.
load_dotenv(ENV_FILE, override=False)

def database_url():
    value = os.getenv('DATABASE_URL')
    if not value:
        raise ValueError('DATABASE_URL is required; configure backend/.env or the environment')
    return value
