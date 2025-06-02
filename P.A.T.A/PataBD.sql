drop database payta;

CREATE DATABASE IF NOT EXISTS payta;

USE payta;

-- Tabla para almacenar la información del usuario
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    apellido VARCHAR(50) NOT NULL,
    edad INT NOT NULL CHECK (edad >= 0),
    discapacidad ENUM('Discapacidad Física', 'Discapacidad Visual', 'Discapacidad Auditiva', 'Discapacidad Intelectual', 'Ninguna') NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para almacenar los puntos de parada
-- Crear tabla de puntos de parada
CREATE TABLE puntos_parada (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

-- Crear tabla de rutas de bus
CREATE TABLE rutas_bus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    punto_parada_id INT NOT NULL,
    FOREIGN KEY (punto_parada_id) REFERENCES puntos_parada(id) ON DELETE CASCADE
);

CREATE TABLE historial_QR (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Usuario_id INT,
    Punto_id INT,
    Ruta_id INT,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (Punto_id) REFERENCES puntos_parada(id) ON DELETE SET NULL,
    FOREIGN KEY (Ruta_id) REFERENCES rutas_bus(id) ON DELETE SET NULL
);

CREATE TABLE historial_sesiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    fecha_hora_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- Insertar valores iniciales para puntos de parada
INSERT INTO puntos_parada (nombre) VALUES
('Av. Urbina'),
('Universidad Técnica de Manabí'),
('Calle Ramos Iduarte'),
('Avenida Metropolitana');

-- Insertar valores iniciales para rutas de bus
INSERT INTO rutas_bus (nombre, punto_parada_id) VALUES
('Cooperativa Portoviejo Ruta 4', 1),
('Cooperativa Portoviejo Ruta 5', 2),
('Cooperativa Ciudad del Valle Ruta 2', 3),
('Cooperativa Ciudad del Valle Ruta 4', 4);



DELETE FROM usuarios where nombre = 'Ronny Yonaiquer';

SET SQL_SAFE_UPDATES = 0;

select * from puntos_parada; 

select * from historial_sesiones;