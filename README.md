# RAM Factory 

Aplicación web con Flask + MySQL (XAMPP) + grok

---

##  REQUISITOS PREVIOS
- Python 3.10+
- XAMPP instalado y corriendo (Apache + MySQL)
- Cuenta en console.anthropic.com para obtener tu API Key

---

## INSTALACIÓN PASO A PASO

### Instalar dependencias
Abre una terminal (CMD o PowerShell) dentro de la carpeta del proyecto:

```bash
pip install -r requirements.txt
```

### Configurar la base de datos
1. Inicia XAMPP y activa Apache + MySQL
2. Abre phpMyAdmin: http://localhost/phpmyadmin
3. Crea una base de datos llamada `ram_factory`
4. Importa el archivo `database.sql`

### Configurar variables de entorno
Edita el archivo `.env` y pon tu API Key de Anthropic:

```
ANTHROPIC_API_KEY=sk-ant-TU_CLAVE_AQUI
```

Obtén tu API Key en: https://console.anthropic.com

Si tu MySQL tiene contraseña, también ponla:
```
MYSQL_PASSWORD=tu_contraseña
```

### Ejecutar la aplicación
```bash
python app.py
```

Abre en tu navegador: http://localhost:5000

---
### Ejecutar el codigo para que te de las contraseñas 
python reset_passwords.py

## USUARIOS DE PRUEBA
| Email                    | Contraseña | Rol   |
| admin@ramfactory.com     | admin123   | Admin |
| user@ramfactory.com      | admin123   | User  |

---

## ESTRUCTURA DEL PROYECTO
```
ram_factory/
├── app.py              ← Punto de entrada
├── config.py           ← Configuración
├── database.sql        ← Base de datos
├── requirements.txt    ← Dependencias
├── .env                ← Variables de entorno (API keys)
├── routes/
│   ├── auth.py         ← Login / Logout
│   ├── admin.py        ← Rutas del administrador
│   ├── user.py         ← Rutas del usuario
│   └── ia.py           ← Integración con Claude AI
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard_admin.html
│   ├── dashboard_user.html
│   ├── inventario.html
│   ├── produccion.html
│   ├── usuarios.html
│   └── ia_chat.html
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## FUNCIONALIDADES
-  Login con roles (Admin / User)
-  Dashboard Admin con 4 gráficas (Chart.js)
- Dashboard User con vista operativa
- Control de inventario de materia prima
- Registro de producción diaria
- Gestión de usuarios
- Asistente IA con grok
- Historial de consultas IA
- Alertas de stock bajo
