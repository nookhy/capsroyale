from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    floor = db.Column(db.String(10), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    elo = db.Column(db.Integer, default=400)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)  # 🔒 Stocke en hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)  # 🔒 Hash sécurisé

    


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    player3_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    player4_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    player5_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    player6_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    winning_team = db.Column(db.String(10), nullable=False)
    mode = db.Column(db.String(20), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_players = db.Column(db.Text, default="")
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  
    commentaire = db.Column(db.Text, nullable=True)  # ✅ Nouveau champ pour le commentaire

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

