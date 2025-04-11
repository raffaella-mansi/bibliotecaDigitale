from flask import Blueprint, request, jsonify, render_template, send_file, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from models import User
import os
from encryption import encrypt_file, decrypt_file
import io

routes_bp = Blueprint('routes', __name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@routes_bp.route('/')
def home():
    return render_template('index.html')


@routes_bp.route('/login', methods=['POST'])
def login_page():
    if not request.is_json:
        return jsonify({"msg": "Content-Type deve essere application/json"}), 415

    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"msg": "Username e password sono obbligatori"}), 400

    username = data.get("username")
    password = data.get("password")

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200

    return jsonify({"msg": "Credenziali non valide"}), 401


@routes_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({"msg": "Nessun file caricato"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"msg": "Nome file non valido"}), 400

    username = get_jwt_identity()
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    os.makedirs(user_folder, exist_ok=True)

    file_path = os.path.join(user_folder, file.filename)
    encrypted_data = encrypt_file(file.read())  # Cifra il file

    with open(file_path, 'wb') as f:
        f.write(encrypted_data)  # Salva il file cifrato

    return jsonify({"message": "File caricato e cifrato con successo!"}), 200


# ✅ Nuova rotta per servire la dashboard HTML (non protetta da JWT)
@routes_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# ✅ API protetta per ottenere i file dell'utente
@routes_bp.route('/api/user-files', methods=['GET'])
@jwt_required()
def get_user_files():
    username = get_jwt_identity()
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    os.makedirs(user_folder, exist_ok=True)
    files = os.listdir(user_folder)
    return jsonify({"username": username, "files": files})


# ✅ Funzione per scaricare un file PDF
@routes_bp.route('/download/<filename>', methods=['GET'])
@jwt_required()
def download_file(filename):
    username = get_jwt_identity()
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    file_path = os.path.join(user_folder, filename)

    if not os.path.exists(file_path):
        return abort(404)  # Se il file non esiste, ritorna errore 404

    # Leggi il file cifrato
    with open(file_path, 'rb') as f:
        encrypted_data = f.read()

    # Decripta il file
    decrypted_data = decrypt_file(encrypted_data)

    # Restituisci il file decrittografato per il download
    return send_file(
        io.BytesIO(decrypted_data),
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )


# ✅ Funzione per visualizzare un file PDF nel browser
@routes_bp.route('/view/<filename>', methods=['GET'])
@jwt_required()
def view_file(filename):
    username = get_jwt_identity()
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    file_path = os.path.join(user_folder, filename)

    if not os.path.exists(file_path):
        return abort(404)  # Se il file non esiste, ritorna errore 404

    # Leggi il file cifrato
    with open(file_path, 'rb') as f:
        encrypted_data = f.read()

    # Decripta il file
    decrypted_data = decrypt_file(encrypted_data)

    # Restituisci il file decrittografato per la visualizzazione nel browser
    return send_file(
        io.BytesIO(decrypted_data),
        mimetype='application/pdf'  # Serve il file direttamente come PDF
    )


# ✅ Funzione per eliminare un file
@routes_bp.route('/delete/<filename>', methods=['DELETE'])
@jwt_required()
def delete_file(filename):
    username = get_jwt_identity()
    user_folder = os.path.join(UPLOAD_FOLDER, username)
    file_path = os.path.join(user_folder, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"msg": "File eliminato con successo"}), 200
    else:
        return jsonify({"msg": "File non trovato"}), 404

