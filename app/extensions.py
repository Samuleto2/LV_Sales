from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
login_manager = LoginManager()

# Configuración de login
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Debes iniciar sesión para acceder'