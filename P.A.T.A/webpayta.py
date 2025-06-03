from flask import Flask, render_template, request, redirect, session, jsonify, send_file, url_for
from flask_mysqldb import MySQL
import qrcode
import io
import base64
import MySQLdb
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'secreto'
app.permanent_session_lifetime = timedelta(days=1)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Ronny2003'
app.config['MYSQL_DB'] = 'payta'

mysql = MySQL(app)

@app.route('/', methods=['GET'])
def mostrar_login():
    return render_template('login.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    datos = request.json
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO usuarios (nombre, apellido, edad, discapacidad, email, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            datos['nombre'],
            datos['apellido'],
            datos['edad'],
            datos['discapacidad'],
            datos['email'],
            datos['password']
        ))
        mysql.connection.commit()
        return jsonify({"success": True, "message": "Usuario registrado correctamente"})
    except Exception as e:
        print("Error al registrar usuario:", e)
        return jsonify({"success": False, "message": "Error al registrar el usuario"}), 500

@app.route('/info-usuario', methods=['POST'])
def info_usuario():
    datos = request.json
    email = datos.get('email')
    password = datos.get('password')

    if not email or not password:
        return jsonify({"success": False, "message": "Por favor, ingrese todos los campos."}), 400

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre, apellido, edad, discapacidad, email, password FROM usuarios WHERE email = %s", (email,))
    user = cur.fetchone()

    if not user:
        return jsonify({"success": False, "message": "Usuario no encontrado."}), 401

    if password == user[6]:
        session['usuario'] = {
            'id': user[0],
            'nombre': user[1],
            'apellido': user[2],
            'edad': user[3],
            'discapacidad': user[4],
            'email': user[5],
        }

        try:
            cur.execute("INSERT INTO historial_sesiones (usuario_id) VALUES (%s)", (user[0],))
            mysql.connection.commit()
        except Exception as e:
            print("Error guardando historial:", e)

        cur.execute("SELECT id, nombre FROM puntos_parada ORDER BY id")
        puntos = cur.fetchall()

        cur.execute("""
            SELECT r.id, r.nombre, p.nombre
            FROM rutas_bus r
            JOIN puntos_parada p ON r.punto_parada_id = p.id
            ORDER BY r.id
        """)
        rutas = cur.fetchall()

        return jsonify({
            "success": True,
            "message": "Inicio de sesión exitoso",
            "user": session['usuario'],
            "puntos": puntos,
            "rutas": rutas
        })
    else:
        return jsonify({"success": False, "message": "Contraseña incorrecta."}), 401


@app.route('/solicitar_codigo_QR')
def solicitar_codigo_qr():
    if 'usuario' not in session:
        return redirect('/')
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, nombre FROM puntos_parada ORDER BY id")
    puntos = cur.fetchall()
    cur.execute("""
        SELECT r.id, r.nombre, p.nombre
        FROM rutas_bus r
        JOIN puntos_parada p ON r.punto_parada_id = p.id
        ORDER BY r.id
    """)
    rutas = cur.fetchall()
    return render_template('solicitar_codigo_QR.html', usuario=session['usuario'], puntos=puntos, rutas=rutas)

@app.route('/generar_qr', methods=['POST'])
def generar_qr():
    if 'usuario' not in session:
        return "Usuario no autenticado", 401

    usuario = session['usuario']
    punto_id = request.form.get('punto-parada')
    ruta_id = request.form.get('ruta-bus')

    cur = mysql.connection.cursor()
    cur.execute("SELECT nombre FROM puntos_parada WHERE id = %s", (punto_id,))
    punto_nombre = cur.fetchone()
    punto_nombre = punto_nombre[0] if punto_nombre else 'No especificado'

    cur.execute("""
        SELECT r.nombre, p.nombre
        FROM rutas_bus r
        JOIN puntos_parada p ON r.punto_parada_id = p.id
        WHERE r.id = %s
    """, (ruta_id,))
    ruta_data = cur.fetchone()
    ruta_nombre, punto_relacionado = ruta_data if ruta_data else ('No especificada', 'No especificado')

    discapacidad = usuario['discapacidad'] if usuario['discapacidad'] != 'Ninguna' else 'Ninguna'
    tercera_edad = 'Si' if usuario['edad'] >= 65 else 'No'

    contenido_qr = f"""
Nombre: {usuario['nombre']}
Apellidos: {usuario['apellido']}
Discapacidad: {discapacidad}
Tercera edad: {tercera_edad}
Punto de parada: {punto_nombre}
Ruta de bus: {ruta_nombre}
    """.strip()

    cur.execute("""
        INSERT INTO historial_QR (Usuario_id, Punto_id, Ruta_id)
        VALUES (%s, %s, %s)
    """, (usuario['id'], punto_id, ruta_id))
    mysql.connection.commit()

    img = qrcode.make(contenido_qr)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return render_template("Resultado_QR.html", qrCodeUrl="data:image/png;base64," + img_base64)

@app.route('/historial_qr')
def historial_qr():
    if 'usuario' not in session:
        return redirect('/')
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT h.id, p.nombre, r.nombre, h.fecha_hora
        FROM historial_QR h
        JOIN puntos_parada p ON h.punto_id = p.id
        JOIN rutas_bus r ON h.ruta_id = r.id
        WHERE h.usuario_id = %s
        ORDER BY h.fecha_hora DESC
    """, (session['usuario']['id'],))
    historial = [
        {
            'id': row[0],
            'punto': row[1],
            'ruta': row[2],
            'fecha': row[3].strftime("%Y-%m-%d %H:%M")
        }
        for row in cur.fetchall()
    ]
    return render_template("historial_qr.html", historial=historial)

@app.route('/qr/ver/<int:qr_id>')
def visualizar_qr(qr_id):
    if 'usuario' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.nombre, u.apellido, u.edad, u.discapacidad, p.nombre, r.nombre
        FROM historial_QR h
        JOIN usuarios u ON h.usuario_id = u.id
        JOIN puntos_parada p ON h.punto_id = p.id
        JOIN rutas_bus r ON h.ruta_id = r.id
        WHERE h.id = %s AND h.usuario_id = %s
    """, (qr_id, session['usuario']['id']))
    datos = cur.fetchone()
    if not datos:
        return "No autorizado o código QR no encontrado", 403

    nombre, apellido, edad, discapacidad, punto, ruta = datos
    tercera_edad = "Si" if edad >= 65 else "No"
    discapacidad = discapacidad if discapacidad != 'Ninguna' else 'Ninguna'

    contenido_qr = f"""
Nombre: {nombre}
Apellidos: {apellido}
Discapacidad: {discapacidad}
Tercera edad: {tercera_edad}
Punto de parada: {punto}
Ruta de bus: {ruta}
    """.strip()

    img = qrcode.make(contenido_qr)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return render_template("Resultado_QR.html", qrCodeUrl="data:image/png;base64," + img_base64)

@app.route('/qr/descargar/<int:qr_id>')
def descargar_qr(qr_id):
    if 'usuario' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.nombre, u.apellido, u.edad, u.discapacidad, p.nombre, r.nombre
        FROM historial_QR h
        JOIN usuarios u ON h.usuario_id = u.id
        JOIN puntos_parada p ON h.punto_id = p.id
        JOIN rutas_bus r ON h.ruta_id = r.id
        WHERE h.id = %s AND h.usuario_id = %s
    """, (qr_id, session['usuario']['id']))
    datos = cur.fetchone()
    if not datos:
        return "No autorizado o código QR no encontrado", 403

    nombre, apellido, edad, discapacidad, punto, ruta = datos
    tercera_edad = "Si" if edad >= 65 else "No"
    discapacidad = discapacidad if discapacidad != 'Ninguna' else 'Ninguna'

    contenido_qr = f"""
Nombre: {nombre}
Apellidos: {apellido}
Discapacidad: {discapacidad}
Tercera edad: {tercera_edad}
Punto de parada: {punto}
Ruta de bus: {ruta}
    """.strip()

    img = qrcode.make(contenido_qr)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return send_file(buffer, mimetype='image/png', as_attachment=True, download_name=f"QR_{qr_id}.png")

@app.route('/qr/eliminar/<int:qr_id>', methods=['POST'])
def eliminar_qr(qr_id):
    if 'usuario' not in session:
        return redirect('/')

    cur = mysql.connection.cursor()
    try:
        cur.execute("SELECT id FROM historial_QR WHERE id = %s AND usuario_id = %s", (qr_id, session['usuario']['id']))
        if not cur.fetchone():
            return "No autorizado o QR no encontrado", 403

        cur.execute("DELETE FROM historial_QR WHERE id = %s", (qr_id,))
        mysql.connection.commit()
        return redirect(url_for('historial_qr'))
    except Exception as e:
        print("Error al eliminar QR:", e)
        return "Error al eliminar", 500