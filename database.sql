-- ============================================================
--  RAM Factory - Base de Datos
--  Ejecutar en phpMyAdmin (XAMPP)
-- ============================================================

CREATE DATABASE IF NOT EXISTS ram_factory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ram_factory;

-- ─── USUARIOS ───────────────────────────────────────────────
CREATE TABLE usuarios (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100)        NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    password    VARCHAR(255)        NOT NULL,
    rol         ENUM('admin','user') DEFAULT 'user',
    activo      TINYINT(1)          DEFAULT 1,
    creado_en   TIMESTAMP           DEFAULT CURRENT_TIMESTAMP
);

-- ─── MATERIA PRIMA ──────────────────────────────────────────
CREATE TABLE materia_prima (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(100)  NOT NULL,
    descripcion     TEXT,
    unidad          VARCHAR(30)   NOT NULL,
    stock_actual    DECIMAL(10,2) DEFAULT 0,
    stock_minimo    DECIMAL(10,2) DEFAULT 0,
    proveedor       VARCHAR(150),
    actualizado_en  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ─── PRODUCTOS ──────────────────────────────────────────────
CREATE TABLE productos (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    descripcion TEXT,
    tipo        VARCHAR(50),
    capacidad   VARCHAR(20),
    velocidad   VARCHAR(20),
    activo      TINYINT(1) DEFAULT 1
);

-- ─── LÍNEAS DE PRODUCCIÓN ────────────────────────────────────
CREATE TABLE lineas_produccion (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL,
    descripcion TEXT,
    activa      TINYINT(1) DEFAULT 1
);

-- ─── REGISTROS DE PRODUCCIÓN ─────────────────────────────────
CREATE TABLE produccion (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    fecha           DATE         NOT NULL,
    producto_id     INT          NOT NULL,
    linea_id        INT          NOT NULL,
    cantidad        INT          NOT NULL,
    turno           ENUM('matutino','vespertino','nocturno') DEFAULT 'matutino',
    operador        VARCHAR(100),
    notas           TEXT,
    registrado_por  INT,
    creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id)    REFERENCES productos(id),
    FOREIGN KEY (linea_id)       REFERENCES lineas_produccion(id),
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
);

-- ─── CONSUMO DE MATERIA PRIMA ────────────────────────────────
CREATE TABLE consumo_materia (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    produccion_id   INT           NOT NULL,
    materia_id      INT           NOT NULL,
    cantidad_usada  DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (produccion_id) REFERENCES produccion(id),
    FOREIGN KEY (materia_id)    REFERENCES materia_prima(id)
);

-- ─── HISTORIAL CONSULTAS IA ──────────────────────────────────
CREATE TABLE consultas_ia (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id  INT  NOT NULL,
    pregunta    TEXT NOT NULL,
    respuesta   TEXT,
    creado_en   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- ============================================================
--  DATOS SEMILLA
-- ============================================================

-- Usuarios  (password para ambos: admin123)
INSERT INTO usuarios (nombre, email, password, rol) VALUES
('Administrador',  'admin@ramfactory.com',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'admin'),
('Carlos López',   'user@ramfactory.com',
 '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'user');

-- Materia prima
INSERT INTO materia_prima (nombre, descripcion, unidad, stock_actual, stock_minimo, proveedor) VALUES
('Chips DRAM DDR4',      'Chips DRAM para módulos DDR4',              'chips',  15000, 2000, 'Samsung Semiconductor'),
('Chips DRAM DDR5',      'Chips DRAM para módulos DDR5',              'chips',   8000, 1500, 'Micron Technology'),
('PCB 288-pin DIMM',     'Placas de circuito para DDR4/DDR5',         'piezas', 12000, 1000, 'PCB Solutions MX'),
('PCB 260-pin SO-DIMM',  'Placas SO-DIMM para laptops',               'piezas',  5000,  800, 'PCB Solutions MX'),
('Capacitores 100nF',    'Capacitores de desacople',                  'piezas', 50000, 5000, 'TDK Electronics'),
('Resistencias 22Ω',     'Resistencias de terminación',               'piezas', 40000, 4000, 'Yageo Corp'),
('IC SPD EEPROM',        'Chips de identificación SPD',               'chips',  10000, 1000, 'Microchip Technology'),
('Etiquetas RAM',        'Etiquetas con especificaciones del módulo',  'piezas', 20000, 2000, 'PrintTech MX'),
('Stickers holográficos','Stickers de autenticidad',                  'piezas', 18000, 1500, 'SecureLabel MX');

-- Productos
INSERT INTO productos (nombre, descripcion, tipo, capacidad, velocidad) VALUES
('DDR4-8GB-3200',  'Módulo DDR4 8GB  3200MHz DIMM',  'DDR4', '8GB',  '3200MHz'),
('DDR4-16GB-3200', 'Módulo DDR4 16GB 3200MHz DIMM',  'DDR4', '16GB', '3200MHz'),
('DDR4-32GB-3600', 'Módulo DDR4 32GB 3600MHz DIMM',  'DDR4', '32GB', '3600MHz'),
('DDR5-16GB-4800', 'Módulo DDR5 16GB 4800MHz DIMM',  'DDR5', '16GB', '4800MHz'),
('DDR5-32GB-5600', 'Módulo DDR5 32GB 5600MHz DIMM',  'DDR5', '32GB', '5600MHz'),
('SO-DDR4-8GB',    'Módulo SO-DIMM DDR4 8GB Laptop', 'DDR4', '8GB',  '3200MHz');

-- Líneas de producción
INSERT INTO lineas_produccion (nombre, descripcion) VALUES
('Línea A - DDR4 Estándar', 'Producción de módulos DDR4 DIMM estándar'),
('Línea B - DDR5 Alta Vel.', 'Producción de módulos DDR5 de alta velocidad'),
('Línea C - SO-DIMM',        'Producción de módulos para laptops y miniPCs');

-- Producción de los últimos 14 días (datos de ejemplo)
INSERT INTO produccion (fecha, producto_id, linea_id, cantidad, turno, operador, registrado_por) VALUES
(CURDATE() - INTERVAL 13 DAY, 1, 1, 320, 'matutino',    'Juan Pérez',    1),
(CURDATE() - INTERVAL 13 DAY, 2, 1, 210, 'vespertino',  'María Gómez',   1),
(CURDATE() - INTERVAL 12 DAY, 1, 1, 350, 'matutino',    'Juan Pérez',    1),
(CURDATE() - INTERVAL 12 DAY, 4, 2, 180, 'matutino',    'Luis Torres',   1),
(CURDATE() - INTERVAL 11 DAY, 2, 1, 230, 'matutino',    'María Gómez',   1),
(CURDATE() - INTERVAL 11 DAY, 5, 2, 120, 'vespertino',  'Luis Torres',   1),
(CURDATE() - INTERVAL 10 DAY, 1, 1, 400, 'matutino',    'Juan Pérez',    1),
(CURDATE() - INTERVAL 10 DAY, 6, 3, 200, 'matutino',    'Ana Ruiz',      1),
(CURDATE() - INTERVAL  9 DAY, 3, 1, 150, 'nocturno',    'Pedro Solis',   1),
(CURDATE() - INTERVAL  9 DAY, 4, 2, 210, 'matutino',    'Luis Torres',   1),
(CURDATE() - INTERVAL  8 DAY, 1, 1, 380, 'matutino',    'Juan Pérez',    1),
(CURDATE() - INTERVAL  8 DAY, 2, 1, 190, 'vespertino',  'María Gómez',   1),
(CURDATE() - INTERVAL  7 DAY, 5, 2, 140, 'matutino',    'Luis Torres',   1),
(CURDATE() - INTERVAL  7 DAY, 6, 3, 220, 'matutino',    'Ana Ruiz',      1),
(CURDATE() - INTERVAL  6 DAY, 1, 1, 360, 'matutino',    'Juan Pérez',    1),
(CURDATE() - INTERVAL  6 DAY, 4, 2, 195, 'nocturno',    'Pedro Solis',   1),
(CURDATE() - INTERVAL  5 DAY, 2, 1, 245, 'matutino',    'María Gómez',   1),
(CURDATE() - INTERVAL  5 DAY, 3, 1, 130, 'vespertino',  'Juan Pérez',    1),
(CURDATE() - INTERVAL  4 DAY, 1, 1, 420, 'matutino',    'Juan Pérez',    1),
(CURDATE() - INTERVAL  4 DAY, 5, 2, 160, 'matutino',    'Luis Torres',   1),
(CURDATE() - INTERVAL  3 DAY, 6, 3, 240, 'matutino',    'Ana Ruiz',      1),
(CURDATE() - INTERVAL  3 DAY, 2, 1, 200, 'vespertino',  'María Gómez',   1),
(CURDATE() - INTERVAL  2 DAY, 1, 1, 390, 'matutino',    'Juan Pérez',    1),
(CURDATE() - INTERVAL  2 DAY, 4, 2, 175, 'matutino',    'Luis Torres',   1),
(CURDATE() - INTERVAL  1 DAY, 3, 1, 145, 'nocturno',    'Pedro Solis',   1),
(CURDATE() - INTERVAL  1 DAY, 5, 2, 185, 'vespertino',  'Luis Torres',   1),
(CURDATE(),                   1, 1, 200, 'matutino',    'Juan Pérez',    1),
(CURDATE(),                   2, 1, 150, 'matutino',    'María Gómez',   1);
