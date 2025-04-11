from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models import db, User
from ldap3 import Server, Connection, ALL
from werkzeug.security import generate_password_hash
import os
import logging

# Inizializzazione del Blueprint
auth_bp = Blueprint('auth', __name__)

# Configurazione del logging
logging.basicConfig(level=logging.INFO)

def ldap_authenticate(username, password):
    """Autentica l'utente con LDAP"""
    ldap_url = os.getenv('LDAP_URL')
    bind_dn = os.getenv('LDAP_BIND_DN')
    bind_password = os.getenv('LDAP_PASSWORD')
    search_base = os.getenv('LDAP_SEARCH_BASE')

    if not all([ldap_url, bind_dn, bind_password, search_base]):
        logging.error("❌ Variabili d'ambiente LDAP non configurate correttamente.")
        return False

    logging.info(f"🔍 Connessione a LDAP: {ldap_url}")

    try:
        # Creazione connessione al server LDAP
        server = Server(ldap_url, use_ssl=True, get_info=ALL)
        conn = Connection(server, user=bind_dn, password=bind_password)

        if not conn.bind():
            logging.error("❌ Errore: impossibile connettersi al server LDAP. Controlla le credenziali.")
            return False

        # Ricerca dell'utente in LDAP con filtro (uid=username)
        search_filter = f"(uid={username})"
        conn.search(search_base, search_filter, attributes=['uid'])  # Modificato per cercare solo 'uid'

        if not conn.entries:
            logging.warning(f"❌ Utente '{username}' non trovato in LDAP.")
            return False

        # Otteniamo il DN dell'utente trovato, che è l'entry_dn
        user_dn = conn.entries[0].entry_dn  # Usa entry_dn per ottenere il DN completo
        logging.info(f"✅ Utente trovato in LDAP: {user_dn}")

        # Tentiamo di fare il bind con il DN dell'utente e la sua password
        user_conn = Connection(server, user=user_dn, password=password)

        if user_conn.bind():
            logging.info(f"✅ Autenticazione riuscita per {username}.")
            return True
        else:
            logging.warning(f"❌ Password errata per {username}.")
            return False

    except Exception as e:
        logging.error(f"❌ Errore LDAP: {e}")
        return False

@auth_bp.route('/login', methods=['POST'])
def login():
    """Gestisce il login con LDAP e genera un token JWT"""
    if not request.is_json:
        return jsonify({"msg": "Content-Type deve essere application/json"}), 415

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"msg": "Username e password sono obbligatori"}), 400

    # Rimuovi gli spazi bianchi (strip) e fai il logging della lunghezza
    username = username.strip()
    password = password.strip()

    # Log delle lunghezze dei valori
    logging.debug(f"Username: {username}, Password (lunghezza): {len(password)}")

    # Cerca l'utente nel database
    user = User.query.filter_by(username=username).first()

    # Se l'utente non esiste nel database, crealo
    if not user:
        # Se l'autenticazione LDAP ha successo, crea un nuovo utente nel database
        if ldap_authenticate(username, password):
            # Creazione del nuovo utente nel database
            user = User(
                username=username,
                password=generate_password_hash(password),  # Crea una hash della password per il DB
                email=f"{username}@example.com",  # Usa un'email generica, o implementa una logica per gestirla
                role="user",  # Imposta il ruolo (puoi personalizzare)
            )
            db.session.add(user)
            db.session.commit()
            logging.info(f"✅ Nuovo utente {username} creato nel database.")
        else:
            return jsonify({"msg": "Credenziali non valide"}), 401

    # Gestione login per utenti esistenti
    if user:
        if user.account_locked:
            logging.warning(f"❌ Account {username} è stato bloccato dopo troppi tentativi falliti.")
            return jsonify({"msg": "Account bloccato a causa di troppi tentativi falliti"}), 403

        if ldap_authenticate(username, password):
            # Se il login è corretto, resetta il contatore dei tentativi falliti
            user.failed_login_count = 0
            db.session.commit()

            # Generazione del token JWT
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200
        else:
            # Se il login fallisce, incrementa il contatore dei tentativi
            user.failed_login_count += 1
            if user.failed_login_count >= 3:
                user.account_locked = True  # Blocca l'account dopo 3 tentativi falliti
            db.session.commit()

            logging.warning(f"❌ Tentativo di login fallito per {username}. Tentativi falliti: {user.failed_login_count}")
            return jsonify({"msg": "Credenziali non valide"}), 401
    else:
        logging.warning(f"❌ Utente {username} non trovato nel database.")
        return jsonify({"msg": "Credenziali non valide"}), 401

