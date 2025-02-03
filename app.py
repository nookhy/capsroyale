from flask import Flask
from models import db  # ✅ Importer db ici
from routes import init_routes

app = Flask(__name__)
app.config.from_object("config")

db.init_app(app)  # ✅ Associer db à Flask

with app.app_context():  
    db.create_all()  # ✅ Crée la base de données si elle n'existe pas

init_routes(app)

if __name__ == "__main__":
    app.run(debug=True)