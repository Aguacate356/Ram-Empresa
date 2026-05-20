from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import mysql
from config import Config
from groq import Groq
import json

ia_bp = Blueprint('ia', __name__)

def get_context_data():
    """Recopila datos de la BD para darle contexto a Claude."""
    cur = mysql.connection.cursor()

    cur.execute("SELECT SUM(cantidad) AS total FROM produccion WHERE fecha = CURDATE()")
    hoy = cur.fetchone()['total'] or 0

    cur.execute("""
        SELECT p.nombre, SUM(pr.cantidad) AS total
        FROM produccion pr JOIN productos p ON pr.producto_id = p.id
        WHERE pr.fecha >= CURDATE() - INTERVAL 6 DAY
        GROUP BY p.nombre ORDER BY total DESC
    """)
    semana = cur.fetchall()

    cur.execute("""
        SELECT p.nombre, SUM(pr.cantidad) AS total
        FROM produccion pr JOIN productos p ON pr.producto_id = p.id
        WHERE MONTH(pr.fecha) = MONTH(CURDATE())
        GROUP BY p.nombre ORDER BY total DESC
    """)
    mes = cur.fetchall()

    cur.execute("SELECT nombre, stock_actual, stock_minimo, unidad FROM materia_prima")
    inventario = cur.fetchall()

    cur.execute("""
        SELECT pr.fecha, p.nombre AS producto, pr.cantidad, lp.nombre AS linea, pr.turno
        FROM produccion pr
        JOIN productos p ON pr.producto_id = p.id
        JOIN lineas_produccion lp ON pr.linea_id = lp.id
        ORDER BY pr.fecha DESC, pr.creado_en DESC LIMIT 20
    """)
    ultimos = cur.fetchall()

    cur.close()

    bajos = [i for i in inventario if float(i['stock_actual']) <= float(i['stock_minimo'])]

    context = f"""
Empresa: RAM Factory S.A. de C.V. — Manufactura de módulos de memoria RAM.
Fecha actual: {__import__('datetime').date.today()}

PRODUCCIÓN HOY: {int(hoy)} unidades

PRODUCCIÓN ÚLTIMOS 7 DÍAS (por producto):
{json.dumps([{'producto': r['nombre'], 'unidades': int(r['total'])} for r in semana], ensure_ascii=False, indent=2)}

PRODUCCIÓN MES ACTUAL (por producto):
{json.dumps([{'producto': r['nombre'], 'unidades': int(r['total'])} for r in mes], ensure_ascii=False, indent=2)}

INVENTARIO DE MATERIA PRIMA:
{json.dumps([{'material': r['nombre'], 'stock': float(r['stock_actual']), 'minimo': float(r['stock_minimo']), 'unidad': r['unidad']} for r in inventario], ensure_ascii=False, indent=2)}

MATERIALES CON BAJO STOCK: {[i['nombre'] for i in bajos] if bajos else 'Ninguno'}

ÚLTIMOS 20 REGISTROS DE PRODUCCIÓN:
{json.dumps([{'fecha': str(r['fecha']), 'producto': r['producto'], 'cantidad': int(r['cantidad']), 'linea': r['linea'], 'turno': r['turno']} for r in ultimos], ensure_ascii=False, indent=2)}
"""
    return context

def get_system_prompt(rol):
    base = """Eres el Asistente IA de RAM Factory, una empresa de manufactura de módulos de memoria RAM.
Tienes acceso a los datos reales de producción e inventario de la empresa.
Responde siempre en español, de forma clara, precisa y profesional.
Basa tus respuestas únicamente en los datos proporcionados."""

    if rol == 'admin':
        return base + """
Como asistente del ADMINISTRADOR puedes:
- Analizar tendencias de producción y detectar anomalías
- Recomendar mejoras en eficiencia por línea de producción
- Alertar sobre materias primas que podrían agotarse
- Hacer análisis comparativos y proyecciones
- Sugerir estrategias de optimización de inventario"""
    else:
        return base + """
Como asistente del USUARIO solo puedes responder consultas operativas básicas:
- Producción del día o días recientes
- Estado general del inventario
- Productos fabricados recientemente
No proporciones análisis avanzados ni información estratégica confidencial."""

@ia_bp.route('/chat')
@login_required
def chat():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT pregunta, respuesta, creado_en
        FROM consultas_ia WHERE usuario_id = %s
        ORDER BY creado_en DESC LIMIT 20
    """, (current_user.id,))
    historial = cur.fetchall()
    cur.close()
    return render_template('ia_chat.html', historial=historial)

@ia_bp.route('/consultar', methods=['POST'])
@login_required
def consultar():
    data     = request.get_json()
    pregunta = data.get('pregunta', '').strip()
    if not pregunta:
        return jsonify({'error': 'Pregunta vacía'}), 400

    # Límite de preguntas para usuarios normales
    if current_user.rol == 'user':
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT COUNT(*) AS cnt FROM consultas_ia
            WHERE usuario_id = %s AND DATE(creado_en) = CURDATE()
        """, (current_user.id,))
        cnt = cur.fetchone()['cnt']
        cur.close()
        if cnt >= 10:
            return jsonify({'respuesta': 'Has alcanzado el límite de 10 consultas diarias. Contacta al administrador.'}), 200

    try:
        context = get_context_data()
        client  = Groq(api_key=Config.GROQ_API_KEY)

        completion = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            max_tokens = 1024,
            messages = [
                {"role": "system", "content": get_system_prompt(current_user.rol)},
                {"role": "user",   "content": f"DATOS ACTUALES DEL SISTEMA:\n{context}\n\nPREGUNTA: {pregunta}"}
            ]
        )
        respuesta = completion.choices[0].message.content

        # Guardar en historial
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO consultas_ia (usuario_id, pregunta, respuesta)
            VALUES (%s, %s, %s)
        """, (current_user.id, pregunta, respuesta))
        mysql.connection.commit()
        cur.close()

        return jsonify({'respuesta': respuesta})

    except Exception as e:
        return jsonify({'error': f'Error al conectar con la IA: {str(e)}'}), 500
