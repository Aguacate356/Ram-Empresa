from flask import Flask
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from config import Config

mysql         = MySQL()
bcrypt        = Bcrypt()
login_manager = LoginManager()

# ── Modelo de usuario ────────────────────────────────────────
class User(UserMixin):
    def __init__(self, id, nombre, email, rol):
        self.id     = id
        self.nombre = nombre
        self.email  = email
        self.rol    = rol

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id = %s AND activo = 1", (user_id,))
    u = cur.fetchone()
    cur.close()
    if u:
        return User(u['id'], u['nombre'], u['email'], u['rol'])
    return None

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mysql.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view             = 'auth.login'
    login_manager.login_message          = 'Por favor inicia sesión para continuar.'
    login_manager.login_message_category = 'warning'

    from routes.auth  import auth_bp
    from routes.admin import admin_bp
    from routes.user  import user_bp
    from routes.ia    import ia_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp,  url_prefix='/user')
    app.register_blueprint(ia_bp,    url_prefix='/ia')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
