import os
from dotenv import load_dotenv
import secrets
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
    JWT_SECRET_KEY = os.getenv('JWT_SECRET') or secrets.token_hex(32)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=10) 
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LDAP_URL = os.getenv('LDAP_URL')
    LDAP_BIND_DN = os.getenv('LDAP_BIND_DN')
    LDAP_PASSWORD = os.getenv('LDAP_PASSWORD')
    LDAP_SEARCH_BASE = os.getenv('LDAP_SEARCH_BASE')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

    if not os.getenv('JWT_SECRET'):
        print(f"⚠️ Attenzione: JWT_SECRET non è impostata. Usa questo valore nel tuo .env: {JWT_SECRET_KEY}")

