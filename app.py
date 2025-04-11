from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from config import Config
from models import db, User
from auth import auth_bp
from routes import routes_bp

app = Flask(__name__)
app.config.from_object(Config)

# Inizializzazione delle estensioni
db.init_app(app)
jwt = JWTManager(app)
login_manager = LoginManager(app)

# Registrazione dei blueprint
app.register_blueprint(auth_bp)  # Registrazione del Blueprint per l'autenticazione
app.register_blueprint(routes_bp)  # Altri eventuali route

# Configurazione del login manager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Avvio dell'applicazione
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Crea le tabelle se non esistono già
    app.run(host='0.0.0.0', port=5000, debug=True)

