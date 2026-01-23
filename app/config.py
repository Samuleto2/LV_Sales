
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # CRÍTICO: Cambiar en producción
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY no está configurada")
    
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL no está configurada")

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CORS_RESOURCES = {r"/*": {"origins": "*"}}
    
    # Configuración de sesión
    SESSION_COOKIE_SECURE = os.getenv("ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 21600  # 6hs