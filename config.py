import os
from dotenv import load_dotenv

# Load environment variables from .env file in development
load_dotenv()

# Database and Redis configuration
DATABASE_URL = os.getenv('DATABASE_URL')
REDIS_URL = os.getenv('REDIS_URL')

# Replace "postgres://" with "postgresql://" for SQLAlchemy if needed
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# App configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)