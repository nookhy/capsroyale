import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "caps.db?timeout=10")
SQLALCHEMY_TRACK_MODIFICATIONS = False
SECRET_KEY = "supersecretkey"