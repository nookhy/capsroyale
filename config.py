import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "caps.db?timeout=10")
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "supersecretkey"
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 Mo
UPLOAD_FOLDER = os.path.join("static", "uploads")
UPLOAD_FOLDER_PROFILE = os.path.join("static", "profiles")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Crée le dossier s’il n’existe pas
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Crée le dossier s’il n’existe pas
if not os.path.exists(UPLOAD_FOLDER_PROFILE):
    os.makedirs(UPLOAD_FOLDER_PROFILE)
