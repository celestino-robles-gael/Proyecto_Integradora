-- Base de datos: miscelanea (MySQL / MariaDB)
-- Al importar este archivo se BORRAN y vuelven a crear las tablas.
CREATE DATABASE IF NOT EXISTS miscelanea
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE miscelanea;

DROP TABLE IF EXISTS Asistencia;
DROP TABLE IF EXISTS detalleVenta;
DROP TABLE IF EXISTS Venta;
DROP TABLE IF EXISTS Empleado;
DROP TABLE IF EXISTS Productos;

CREATE TABLE Productos (
  id           INT PRIMARY KEY AUTO_INCREMENT,
  nombre       VARCHAR(100) NOT NULL,
  stock        INT NOT NULL DEFAULT 0,
  stockMinimo  INT NOT NULL DEFAULT 0,
  precioCompra DECIMAL(10,2) NOT NULL,
  precioVenta  DECIMAL(10,2) NOT NULL
) AUTO_INCREMENT = 282282;

CREATE TABLE Empleado (
  id         INT PRIMARY KEY AUTO_INCREMENT,
  nombre     VARCHAR(100) NOT NULL,
  puesto     VARCHAR(50) NOT NULL,
  usuario    VARCHAR(50) NOT NULL UNIQUE,
  contrasena CHAR(64) NOT NULL          -- SHA-256 en hexadecimal
);

CREATE TABLE Venta (
  id         INT PRIMARY KEY AUTO_INCREMENT,
  fecha      DATETIME NOT NULL,
  total      DECIMAL(10,2) NOT NULL,
  idEmpleado INT NULL,                   -- NULL si el empleado eliminó su usuario
  FOREIGN KEY (idEmpleado) REFERENCES Empleado(id) ON DELETE SET NULL
);

-- Horas trabajadas: una fila por periodo de trabajo.
--   salida = última actividad real (ratón/teclado) del empleado, no la hora actual,
--            así el tiempo inactivo o con la compu suspendida no cuenta.
--   latido = última vez que el programa avisó que sigue abierto.
--   abierta = 1 mientras la sesión sigue abierta (evita iniciar sesión dos veces).
CREATE TABLE Asistencia (
  id         INT PRIMARY KEY AUTO_INCREMENT,
  idEmpleado INT NOT NULL,
  entrada    DATETIME NOT NULL,
  salida     DATETIME NOT NULL,
  latido     DATETIME NOT NULL,
  abierta    TINYINT(1) NOT NULL DEFAULT 1,
  FOREIGN KEY (idEmpleado) REFERENCES Empleado(id) ON DELETE CASCADE
);

CREATE TABLE detalleVenta (
  id             INT PRIMARY KEY AUTO_INCREMENT,
  idVenta        INT NOT NULL,
  idProducto     INT NOT NULL,
  precioUnitario DECIMAL(10,2) NOT NULL,
  cantidad       INT NOT NULL,
  FOREIGN KEY (idVenta)    REFERENCES Venta(id),
  FOREIGN KEY (idProducto) REFERENCES Productos(id)
);

-- ---------- Datos de ejemplo ----------
INSERT INTO Productos (id, nombre, stock, stockMinimo, precioCompra, precioVenta) VALUES
  (282282, 'Coca - cola',       15,  5, 15.00, 35.00),
  (282283, 'Sabritas Original',  3,  5, 12.00, 18.00),
  (282284, 'Agua 600 ml',       40, 10,  6.00, 10.00),
  (282285, 'Galletas Marias',   25,  8,  9.00, 15.00);

-- Usuarios de ejemplo:  admin / admin   y   cesar / admin  (todos usan la contraseña «admin»)
INSERT INTO Empleado (id, nombre, puesto, usuario, contrasena) VALUES
  (1, 'Cesar Carrillo', 'empleado', 'cesar', SHA2('admin', 256)),
  (2, 'Evelyn Gurrola', 'gerente',  'admin', SHA2('admin', 256));

INSERT INTO Venta (id, fecha, total, idEmpleado)
VALUES (1, '2026-10-24 10:30:00', 70.00, 1);

INSERT INTO detalleVenta (id, idVenta, idProducto, precioUnitario, cantidad)
VALUES (1, 1, 282282, 35.00, 2);
