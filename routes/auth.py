from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from app import mysql, bcrypt, User

auth_bp = Blueprint('auth', __name__)

# ── Login ────────────────────────────────────────────────────
@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE email = %s AND activo = 1", (email,))
        u = cur.fetchone()
        cur.close()
        if u and bcrypt.check_password_hash(u['password'], password):
            user = User(u['id'], u['nombre'], u['email'], u['rol'])
            login_user(user)
            if u['rol'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.dashboard'))
        flash('Credenciales incorrectas.', 'danger')
    return render_template('login.html')

# ── Logout ───────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
