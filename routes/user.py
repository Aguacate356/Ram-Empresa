from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import mysql
import json

user_bp = Blueprint('user', __name__)

@user_bp.route('/dashboard')
@login_required
def dashboard():
    cur = mysql.connection.cursor()

    # Producción hoy
    cur.execute("""
        SELECT COALESCE(SUM(cantidad), 0) AS total
        FROM produccion WHERE fecha = CURDATE()
    """)
    prod_hoy = cur.fetchone()['total']

    # Últimos 5 registros
    cur.execute("""
        SELECT pr.fecha, p.nombre AS producto, pr.cantidad, pr.turno, lp.nombre AS linea
        FROM produccion pr
        JOIN productos p  ON pr.producto_id = p.id
        JOIN lineas_produccion lp ON pr.linea_id = lp.id
        ORDER BY pr.fecha DESC, pr.creado_en DESC LIMIT 5
    """)
    recientes = cur.fetchall()

    # Inventario disponible (solo nombre y stock)
    cur.execute("""
        SELECT nombre, stock_actual, unidad,
               CASE WHEN stock_actual <= stock_minimo THEN 1 ELSE 0 END AS bajo_stock
        FROM materia_prima ORDER BY nombre
    """)
    inventario = cur.fetchall()

    # Producción últimos 7 días para mini-gráfico
    cur.execute("""
        SELECT fecha, SUM(cantidad) AS total
        FROM produccion
        WHERE fecha >= CURDATE() - INTERVAL 6 DAY
        GROUP BY fecha ORDER BY fecha
    """)
    prod_semana = cur.fetchall()

    # Top 3 productos del mes
    cur.execute("""
        SELECT p.nombre, SUM(pr.cantidad) AS total
        FROM produccion pr JOIN productos p ON pr.producto_id = p.id
        WHERE MONTH(pr.fecha) = MONTH(CURDATE())
        GROUP BY p.nombre ORDER BY total DESC LIMIT 3
    """)
    top3 = cur.fetchall()

    cur.close()

    return render_template('dashboard_user.html',
        prod_hoy    = prod_hoy,
        recientes   = recientes,
        inventario  = inventario,
      prod_semana = json.dumps([{'fecha': str(r['fecha']), 'total': int(r['total'])} for r in prod_semana]),
        top3        = top3,
    )
