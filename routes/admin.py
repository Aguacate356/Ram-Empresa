from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import mysql, bcrypt
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            flash('Acceso restringido a administradores.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# ── Dashboard Admin ──────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    cur = mysql.connection.cursor()

    # Producción total hoy
    cur.execute("""
        SELECT COALESCE(SUM(cantidad), 0) AS total
        FROM produccion WHERE fecha = CURDATE()
    """)
    prod_hoy = cur.fetchone()['total']

    # Producción últimos 7 días (para gráfico)
    cur.execute("""
        SELECT fecha, SUM(cantidad) AS total
        FROM produccion
        WHERE fecha >= CURDATE() - INTERVAL 6 DAY
        GROUP BY fecha ORDER BY fecha
    """)
    prod_semana = cur.fetchall()

    # Producto más fabricado (mes actual)
    cur.execute("""
        SELECT p.nombre, SUM(pr.cantidad) AS total
        FROM produccion pr JOIN productos p ON pr.producto_id = p.id
        WHERE MONTH(pr.fecha) = MONTH(CURDATE())
        GROUP BY p.nombre ORDER BY total DESC LIMIT 5
    """)
    top_productos = cur.fetchall()

    # Alertas de inventario bajo
    cur.execute("""
        SELECT nombre, stock_actual, stock_minimo, unidad
        FROM materia_prima
        WHERE stock_actual <= stock_minimo
    """)
    alertas = cur.fetchall()

    # Consumo materia prima últimos 30 días
    cur.execute("""
        SELECT mp.nombre, SUM(cm.cantidad_usada) AS total
        FROM consumo_materia cm JOIN materia_prima mp ON cm.materia_id = mp.id
        JOIN produccion pr ON cm.produccion_id = pr.id
        WHERE pr.fecha >= CURDATE() - INTERVAL 29 DAY
        GROUP BY mp.nombre ORDER BY total DESC LIMIT 6
    """)
    consumo_mp = cur.fetchall()

    # Total usuarios
    cur.execute("SELECT COUNT(*) AS total FROM usuarios WHERE activo = 1")
    total_usuarios = cur.fetchone()['total']

    # Eficiencia por línea (últimos 7 días)
    cur.execute("""
        SELECT lp.nombre, SUM(pr.cantidad) AS total
        FROM produccion pr JOIN lineas_produccion lp ON pr.linea_id = lp.id
        WHERE pr.fecha >= CURDATE() - INTERVAL 6 DAY
        GROUP BY lp.nombre
    """)
    eficiencia_lineas = cur.fetchall()

    cur.close()

    return render_template('dashboard_admin.html',
        prod_hoy        = int(prod_hoy),
        prod_semana     = json.dumps([{'fecha': str(r['fecha']), 'total': int(r['total'])} for r in prod_semana]),
        top_productos   = json.dumps([{'nombre': r['nombre'], 'total': int(r['total'])} for r in top_productos]),
        consumo_mp      = json.dumps([{'nombre': r['nombre'], 'total': float(r['total'])} for r in consumo_mp]),
        eficiencia      = json.dumps([{'nombre': r['nombre'], 'total': int(r['total'])} for r in eficiencia_lineas]),
        alertas         = alertas,
        total_usuarios  = int(total_usuarios),
    )

# ── Inventario ───────────────────────────────────────────────
@admin_bp.route('/inventario')
@login_required
@admin_required
def inventario():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM materia_prima ORDER BY nombre")
    items = cur.fetchall()
    cur.close()
    return render_template('inventario.html', items=items)

@admin_bp.route('/inventario/agregar', methods=['POST'])
@login_required
@admin_required
def agregar_materia():
    d = request.form
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO materia_prima (nombre, descripcion, unidad, stock_actual, stock_minimo, proveedor)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (d['nombre'], d.get('descripcion',''), d['unidad'],
          d['stock_actual'], d['stock_minimo'], d.get('proveedor','')))
    mysql.connection.commit()
    cur.close()
    flash('Materia prima registrada correctamente.', 'success')
    return redirect(url_for('admin.inventario'))

@admin_bp.route('/inventario/actualizar/<int:id>', methods=['POST'])
@login_required
@admin_required
def actualizar_stock(id):
    nuevo_stock = request.form.get('stock_actual')
    cur = mysql.connection.cursor()
    cur.execute("UPDATE materia_prima SET stock_actual = %s WHERE id = %s", (nuevo_stock, id))
    mysql.connection.commit()
    cur.close()
    flash('Stock actualizado.', 'success')
    return redirect(url_for('admin.inventario'))

@admin_bp.route('/inventario/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_materia(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM materia_prima WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Material eliminado.', 'info')
    return redirect(url_for('admin.inventario'))

# ── Producción ───────────────────────────────────────────────
@admin_bp.route('/produccion')
@login_required
@admin_required
def produccion():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT pr.*, p.nombre AS producto, lp.nombre AS linea
        FROM produccion pr
        JOIN productos p ON pr.producto_id = p.id
        JOIN lineas_produccion lp ON pr.linea_id = lp.id
        ORDER BY pr.fecha DESC, pr.creado_en DESC LIMIT 100
    """)
    registros = cur.fetchall()
    cur.execute("SELECT * FROM productos WHERE activo = 1")
    productos = cur.fetchall()
    cur.execute("SELECT * FROM lineas_produccion WHERE activa = 1")
    lineas = cur.fetchall()
    cur.close()
    return render_template('produccion.html', registros=registros,
                           productos=productos, lineas=lineas)

@admin_bp.route('/produccion/registrar', methods=['POST'])
@login_required
@admin_required
def registrar_produccion():
    d = request.form
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO produccion (fecha, producto_id, linea_id, cantidad, turno, operador, notas, registrado_por)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (d['fecha'], d['producto_id'], d['linea_id'], d['cantidad'],
          d['turno'], d.get('operador',''), d.get('notas',''), current_user.id))
    mysql.connection.commit()
    cur.close()
    flash('Producción registrada correctamente.', 'success')
    return redirect(url_for('admin.produccion'))

@admin_bp.route('/produccion/eliminar/<int:id>', methods=['POST'])
@login_required
@admin_required
def eliminar_produccion(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM produccion WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Registro eliminado.', 'info')
    return redirect(url_for('admin.produccion'))

# ── Usuarios ─────────────────────────────────────────────────
@admin_bp.route('/usuarios')
@login_required
@admin_required
def usuarios():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, email, rol, activo, creado_en FROM usuarios ORDER BY creado_en DESC")
    users = cur.fetchall()
    cur.close()
    return render_template('usuarios.html', users=users)

@admin_bp.route('/usuarios/agregar', methods=['POST'])
@login_required
@admin_required
def agregar_usuario():
    d = request.form
    hashed = bcrypt.generate_password_hash(d['password']).decode('utf-8')
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO usuarios (nombre, email, password, rol)
            VALUES (%s,%s,%s,%s)
        """, (d['nombre'], d['email'], hashed, d['rol']))
        mysql.connection.commit()
        flash('Usuario creado correctamente.', 'success')
    except Exception:
        flash('El email ya está registrado.', 'danger')
    finally:
        cur.close()
    return redirect(url_for('admin.usuarios'))

@admin_bp.route('/usuarios/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_usuario(id):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE usuarios SET activo = NOT activo WHERE id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    flash('Estado del usuario actualizado.', 'info')
    return redirect(url_for('admin.usuarios'))

# ── API datos para gráficos (AJAX) ───────────────────────────
@admin_bp.route('/api/produccion_mes')
@login_required
@admin_required
def api_produccion_mes():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT DATE_FORMAT(fecha,'%d/%m') AS dia, SUM(cantidad) AS total
        FROM produccion
        WHERE fecha >= CURDATE() - INTERVAL 29 DAY
        GROUP BY fecha ORDER BY fecha
    """)
    rows = cur.fetchall()
    cur.close()
    return jsonify(rows)
