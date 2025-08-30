from app import app
from models import db

with app.app_context():
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        if table.name.lower() != "admin":
            print(f"🔴 Suppression de la table {table}")
            db.session.execute(table.delete())
    db.session.commit()
    print("✅ Toutes les données ont été supprimées.")