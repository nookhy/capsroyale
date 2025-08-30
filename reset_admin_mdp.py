from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    username = "admin"  # Ton identifiant admin
    password = "saucisseV45"  # Ton mot de passe

    hashed_pw = generate_password_hash(password)
    new_admin = Admin(username=username, password_hash=hashed_pw)

    db.session.add(new_admin)
    db.session.commit()
    print("✅ Admin ajouté avec succès !")