from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')
    failed_login_count = db.Column(db.Integer, default=0)  # Nuovo campo per tentativi falliti
    account_locked = db.Column(db.Boolean, default=False)  # Nuovo campo per bloccare l'account

    def check_password(self, password):
        return check_password_hash(self.password, password)

