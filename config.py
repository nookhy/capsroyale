import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# 🔥 Utiliser PostgreSQL si la variable d’environnement `DATABASE_URL` est définie, sinon SQLite
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "caps.db?timeout=10"))

SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "supersecretkey"