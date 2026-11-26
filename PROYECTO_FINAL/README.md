# El Baratero Minisúper

Sistema de ventas e inventario (Python + Tkinter + MySQL).

## Cómo ejecutarlo
1. Importa `miscelanea.sql` en MySQL (phpMyAdmin o `mysql -u root -p < miscelanea.sql`).
   **Ojo:** borra y vuelve a crear las tablas.
2. Instala el conector: `pip install -r requirements.txt`
3. Si tu MySQL tiene otro usuario, contraseña o nombre de base, cámbialos en `conexionBD.py`.
4. Ejecuta desde esta carpeta: `python main.py`

## Cómo entrar
| Usuario | Contraseña | Puesto  |
|---------|------------|---------|
| admin   | admin      | gerente |
| cesar   | admin      | empleado|

- **La contraseña de todos los empleados es `admin`.**
- Empleado nuevo: en la pantalla de inicio de sesión pulsa **«¿Eres empleado nuevo? Regístrate aquí»**,
  escribe tu nombre y elige un usuario.
- **Permisos:** solo el **gerente** puede insertar, actualizar o eliminar empleados y ver a todos.
  Los empleados solo ven sus propios datos. Quien se registra siempre queda como «empleado».
- **Contraseña:** todos empiezan con `admin`, pero cada uno puede cambiarla con
  **🔑 Cambiar mi contraseña** (menú izquierdo). Si alguien la olvida, el gerente la restablece en
  Empleados → Actualizar.
- **Horas trabajadas:** se muestran en Inicio, al pulsar el icono 👤 y en **Empleados → Consultar**.
  Cuenta el tiempo con actividad real (ratón o teclado). A los 10 minutos sin actividad aparece
  un aviso **«¿Sigues trabajando?»**: si mueves el ratón o pulsas el botón, ese rato sí cuenta.
  Si nadie responde, a los 15 minutos se pausa el conteo y, al volver, se retoma solo.
  Lo que ya se contó nunca se pierde, aunque el programa se cierre mal (como máximo ~30 s).
  Al cerrar la ventana se pide confirmación para evitar cierres por error. Los tiempos se
  cambian en `main.py` (`MINUTOS_AVISO`, `MINUTOS_INACTIVIDAD`).
  Un mismo usuario no puede tener dos ventanas abiertas a la vez.
- **Eliminar mi usuario:** botón rojo en el menú de la izquierda (pide confirmación).
  Las ventas que hiciste se conservan; el usuario `admin` no se puede eliminar.

## Logo
Si guardas tu logo como `GUI/logo.png`, aparece en la pantalla de inicio de sesión
(si no existe, se usa un dibujo de gallo).

## Estructura
- `main.py` — ventana principal, menú lateral y navegación
- `conexionBD.py` — conexión a MySQL (`conexion` y `cursor`)
- `errores.py`, `utilidades.py` — errores por campo y manejo de fechas
- `PRODUCTOS/`, `EMPLEADOS/`, `VENTAS/`, `DETALLEVENTA/` — lógica de cada módulo
- `GUI/` — pantallas (login, menús, formularios, listas y reportes)
