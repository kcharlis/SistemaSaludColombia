#  Nombre del archivo: App.py
from flask import Flask, request, render_template, redirect, url_for, session, flash
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory
from urllib.parse import unquote
import logging

# módulos necesarios para /contactenos
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_mail import Mail, Message





import mysql.connector

app = Flask(__name__)
app.secret_key = 'your_secret_key'  
app.logger.setLevel(logging.DEBUG)

# Configuración de la conexión a la BD
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456",
    database="SistemaSaludColombia"
)

# Función para verificar la extensión del archivo permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

# Configuración de la carpeta de carga
app.config['UPLOAD_FOLDER'] = 'uploads'  
# ...

# Ruta para el inicio de sesión
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None  

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        cursor = db.cursor()
        query = "SELECT * FROM Usuarios WHERE NombreUsuario = %s AND Contraseña = %s;"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]  # Almacenar el ID de usuario en la sesión
            session['user_name'] = user[1]  # Almacenar el nombre de usuario en la sesión
            return redirect(url_for('get_pacientes'))
        else:
            error = "Nombre de usuario o contraseña incorrectos."

   
    return render_template('login.html', error=error)



# Ruta para cerrar sesión
@app.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


# ...


# Ruta para obtener todos los pacientes con detalles de historias clínicas, EPS y citas
@app.route("/pacientes", methods=["GET"])
def get_pacientes():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = db.cursor()

    # Consulta para obtener la lista de todos los pacientes sin paginación
    query_pacientes = """
        SELECT 
            Pacientes.ID_Paciente,
            Pacientes.Nombre AS Nombre_Paciente,
            Pacientes.Apellido AS Apellido_Paciente,
            Pacientes.Documento_Identidad,
            Pacientes.Fecha_Nacimiento,
            Pacientes.Direccion,
            Pacientes.Contacto,
            Historias_Clinicas.Fecha_Consulta,
            Historias_Clinicas.Diagnostico,
            Historias_Clinicas.Tratamiento,
            Historias_Clinicas.Resultados_Examenes,
            EPS.Nombre AS Nombre_EPS,
            Pacientes.Historial_Medico,
            Citas.ID_Cita IS NOT NULL AS Tiene_Cita,
            Citas.Fecha_Cita
        FROM Pacientes
        LEFT JOIN Historias_Clinicas ON Pacientes.ID_Paciente = Historias_Clinicas.ID_Paciente
        LEFT JOIN EPS ON Pacientes.ID_EPS = EPS.ID_EPS
        LEFT JOIN Citas ON Pacientes.ID_Paciente = Citas.ID_Paciente
        ORDER BY Pacientes.ID_Paciente;
    """
    cursor.execute(query_pacientes)
    
    # Convertir las tuplas a diccionarios
    columns = [col[0] for col in cursor.description]
    pacientes_info = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render_template('pacientes_detalles.html', pacientes_detalles=pacientes_info)


@app.route("/buscar_paciente", methods=["POST"])
def buscar_paciente():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = db.cursor()

    documento_busqueda = request.form.get('documento_busqueda')
    print(f'Documento de búsqueda: {documento_busqueda}')  

    # Consulta para buscar paciente por número de identificación
    query_busqueda = """
        SELECT 
        Pacientes.ID_Paciente,
        Pacientes.Nombre AS Nombre_Paciente,
        Pacientes.Apellido AS Apellido_Paciente,
        Pacientes.Documento_Identidad,
        Pacientes.Fecha_Nacimiento,
        Pacientes.Direccion,
        Pacientes.Contacto,
        Historias_Clinicas.Fecha_Consulta,
        Historias_Clinicas.Diagnostico,
        Historias_Clinicas.Tratamiento,
        Historias_Clinicas.Resultados_Examenes,
        EPS.Nombre AS Nombre_EPS,
        Pacientes.Historial_Medico,
        Citas.ID_Cita IS NOT NULL AS Tiene_Cita,
        Citas.Fecha_Cita
    FROM Pacientes
    LEFT JOIN Historias_Clinicas ON Pacientes.ID_Paciente = Historias_Clinicas.ID_Paciente
    LEFT JOIN EPS ON Pacientes.ID_EPS = EPS.ID_EPS
    LEFT JOIN Citas ON Pacientes.ID_Paciente = Citas.ID_Paciente
    WHERE LOWER(Pacientes.Documento_Identidad) = LOWER(%s)
    ORDER BY Historias_Clinicas.Fecha_Consulta DESC, Pacientes.ID_Paciente;
    """
    cursor.execute(query_busqueda, (documento_busqueda.lower(),))
    
    # Convertir las tuplas a diccionarios
    columns = [col[0] for col in cursor.description]
    resultados_busqueda = [dict(zip(columns, row)) for row in cursor.fetchall()]

    print(f'Resultados de búsqueda: {resultados_busqueda}')  # Agrega esta línea

    return render_template('resultados_busqueda.html', resultados_busqueda=resultados_busqueda)


# Antes de la declaración de la ruta
def obtener_eps():
    cursor = db.cursor()
    query_obtener_eps = "SELECT ID_EPS, Nombre FROM EPS;"
    cursor.execute(query_obtener_eps)
    eps = cursor.fetchall()
    print(eps)  # Agrega esta línea para imprimir las EPS en la consola
    return eps



# Ruta para registrar pacientes
@app.route("/registrar_paciente", methods=["GET", "POST"])
def registrar_paciente():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = db.cursor()

    if request.method == "GET":
        eps = obtener_eps()
        print(eps)  
        return render_template('registro_paciente.html', eps=eps)

    if request.method == "POST":
        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        documento = request.form.get("documento")
        fecha_nacimiento = request.form.get("fecha_nacimiento")
        direccion = request.form.get("direccion")
        contacto = request.form.get("contacto")
        historial_medico = request.files['historial_medico']
        fecha_consulta = request.form.get("fecha_consulta")
        Diagnostico = request.form.get("Diagnostico")
        tratamiento = request.form.get("tratamiento")
        resultados_examenes = request.form.get("resultados_examenes")
        fecha_cita = request.form.get("fecha_cita")  

        # Validar que el archivo es un PDF
        if historial_medico and allowed_file(historial_medico.filename):
            # Generar un nombre seguro para el archivo
            filename = secure_filename(historial_medico.filename)

            # Guardar el archivo en el directorio de carga
            historial_medico.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Obtener el ID de la EPS seleccionada en el formulario
            eps_id = request.form.get("eps")

            # Insertar paciente en la base de datos con referencia al archivo
            query_insert_paciente = """
                INSERT INTO Pacientes (Nombre, Apellido, Documento_Identidad, 
                                    Fecha_Nacimiento, Direccion, Contacto, ID_EPS, Historial_Medico)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query_insert_paciente, (nombre, apellido, documento,
                                                fecha_nacimiento, direccion,
                                                contacto, eps_id, filename))
            db.commit()

            # Obtener ID del paciente recién registrado
            paciente_id = cursor.lastrowid

            # Modificar el nombre del archivo PDF para incluir el ID del paciente
            new_filename = f"{paciente_id}_{filename}"
            os.rename(
                os.path.join(app.config['UPLOAD_FOLDER'], filename),
                os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            )

            # Actualizar el nombre del archivo en la base de datos
            query_update_filename = """
                UPDATE Pacientes
                SET Historial_Medico = %s
                WHERE ID_Paciente = %s;
            """
            cursor.execute(query_update_filename, (new_filename, paciente_id))
            db.commit()

            # Insertar historia clínica del paciente
            query_insert_historia = """
                INSERT INTO Historias_Clinicas (ID_Paciente, Fecha_Consulta, 
                                                Diagnostico, Tratamiento, 
                                                Resultados_Examenes)
                VALUES (%s, %s, %s, %s, %s);
            """
            cursor.execute(query_insert_historia, (paciente_id, fecha_consulta,
                                                Diagnostico, tratamiento,
                                                resultados_examenes))
            db.commit()

            # Insertar cita del paciente (si se proporciona la fecha de la cita)
            if fecha_cita:
                query_insert_cita = """
                    INSERT INTO Citas (ID_Paciente, Fecha_Cita)
                    VALUES (%s, %s);
                """
                cursor.execute(query_insert_cita, (paciente_id, fecha_cita))
                db.commit()

            flash('Registro exitoso', 'success')
            return redirect(url_for('get_pacientes'))

        else:
            flash('Error: Solo se permiten archivos PDF.', 'danger')

    return render_template('registro_paciente.html')

# Función para formatear los detalles del paciente
def format_paciente_details(paciente):
    paciente_detalles = {
        'ID_Paciente': paciente[0],
        'Nombre_Paciente': paciente[1],
        'Apellido_Paciente': paciente[2],
        'Documento_Identidad': paciente[3],
        'Fecha_Nacimiento': paciente[4],
        'Direccion': paciente[5],
        'Contacto': paciente[6],
        'Fecha_Consulta': paciente[7],
        'Diagnostico': paciente[8],
        'Tratamiento': paciente[9],
        'Resultados_Examenes': paciente[10],
        'Nombre_EPS': paciente[11],
        'Historial_Medico': os.path.join('uploads', paciente[12].decode('utf-8')),  # Agrega la ruta completa
        'Tiene_Cita': paciente[13],
        'Fecha_Cita': paciente[14],
    }

    # Imprimir algunos valores clave para depuración
    print("ID_Paciente:", paciente_detalles['ID_Paciente'])
    print("Nombre_Paciente:", paciente_detalles['Nombre_Paciente'])
    
    return paciente_detalles


# Ruta para obtener el historial médico desde la carpeta de carga
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    # Eliminar comillas simples y la 'b' al principio del nombre del archivo
    clean_filename = filename.replace("b'", "").replace("'", "")
    return send_from_directory(app.config['UPLOAD_FOLDER'], clean_filename)

# Ruta para mostrar el historial médico
@app.route("/historial_medico/<int:paciente_id>")
def historial_medico(paciente_id):
    # Lógica para obtener el historial médico del paciente con ID paciente_id
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()

    # Consulta para obtener el nombre del archivo del historial médico
    query_historial_medico = """
        SELECT Historial_Medico FROM Pacientes WHERE ID_Paciente = %s;
    """
    cursor.execute(query_historial_medico, (paciente_id,))
    resultado = cursor.fetchone()

    if resultado and resultado[0]:
        # El paciente tiene historial médico, redirigir a la ruta de descarga
        filename = unquote(resultado[0])  
        return redirect(url_for('uploaded_file', filename=filename))
    else:
        # El paciente no tiene historial médico
        flash('Sin Historial Médico', 'danger')
        return redirect(url_for('get_pacientes'))

# ...


# Ruta para eliminar paciente
@app.route("/eliminar_paciente/<int:paciente_id>", methods=["POST"])
def eliminar_paciente(paciente_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = db.cursor()

    try:
        # Eliminar citas asociadas al paciente
        query_eliminar_citas = "DELETE FROM Citas WHERE ID_Paciente = %s;"
        cursor.execute(query_eliminar_citas, (paciente_id,))
        db.commit()

        # Obtener detalles del paciente antes de eliminarlo
        query_paciente = """
            SELECT 
                Pacientes.ID_Paciente,
                Pacientes.Nombre AS Nombre_Paciente,
                Pacientes.Apellido AS Apellido_Paciente
            FROM Pacientes
            WHERE Pacientes.ID_Paciente = %s;
        """
        cursor.execute(query_paciente, (paciente_id,))
        paciente = cursor.fetchone()

        # Eliminar al paciente
        query_eliminar_paciente = "DELETE FROM Pacientes WHERE ID_Paciente = %s;"
        cursor.execute(query_eliminar_paciente, (paciente_id,))
        db.commit()

        flash('Paciente eliminado exitosamente', 'success')

    except mysql.connector.errors.IntegrityError as e:
        flash('Error al eliminar el paciente: {}'.format(str(e)), 'danger')

    return redirect(url_for('get_pacientes'))

# Agrega la función obtener_inventarios
def obtener_inventarios():
    cursor = db.cursor()

    # Consulta para obtener la lista de inventarios de medicamentos
    query_inventarios = """
        SELECT 
            inventarios_medicamentos.ID_Inventario,
            medicamentos.Nombre AS Nombre_Medicamento,
            eps.Nombre AS Nombre_EPS,
            inventarios_medicamentos.Stock_Actual,
            inventarios_medicamentos.Fecha_Actualizacion
        FROM inventarios_medicamentos
        JOIN medicamentos ON inventarios_medicamentos.ID_Medicamento = medicamentos.ID_Medicamento
        JOIN eps ON inventarios_medicamentos.ID_EPS = eps.ID_EPS;
    """
    cursor.execute(query_inventarios)

    # Convertir las tuplas a diccionarios
    columns = [col[0] for col in cursor.description]
    inventarios = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return inventarios

# Agrega la nueva función obtener_medicamentos
def obtener_medicamentos():
    cursor = db.cursor()

    # Consulta para obtener la lista de medicamentos
    query_medicamentos = """
        SELECT ID_Medicamento, Nombre FROM medicamentos;
    """
    cursor.execute(query_medicamentos)

    # Convertir las tuplas a diccionarios
    columns = [col[0] for col in cursor.description]
    medicamentos = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return medicamentos

# Ruta para manejar el inventario de medicamentos
@app.route("/inventarios_medicamentos", methods=["GET", "POST"])
def inventarios_medicamentos():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    cursor = db.cursor()

    # Agrega la función obtener_inventarios
    def obtener_inventarios():
        cursor = db.cursor()

        # Consulta para obtener la lista de inventarios de medicamentos
        query_inventarios = """
            SELECT 
                inventarios_medicamentos.ID_Inventario,
                medicamentos.Nombre AS Nombre_Medicamento,
                eps.Nombre AS Nombre_EPS,
                inventarios_medicamentos.Stock_Actual,
                inventarios_medicamentos.Fecha_Actualizacion
            FROM inventarios_medicamentos
            JOIN medicamentos ON inventarios_medicamentos.ID_Medicamento = medicamentos.ID_Medicamento
            JOIN eps ON inventarios_medicamentos.ID_EPS = eps.ID_EPS;
        """
        cursor.execute(query_inventarios)

        # Convertir las tuplas a diccionarios
        columns = [col[0] for col in cursor.description]
        inventarios = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return inventarios

    # Agrega la función obtener_eps
    def obtener_eps():
        cursor = db.cursor()

        # Consulta para obtener la lista de EPS
        query_eps = """
            SELECT ID_EPS, Nombre FROM eps;
        """
        cursor.execute(query_eps)

        # Convertir las tuplas a diccionarios
        columns = [col[0] for col in cursor.description]
        eps_list = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return eps_list

    if request.method == "GET":
        inventarios = obtener_inventarios()
        medicamentos = obtener_medicamentos()
        eps_list = obtener_eps()
        return render_template('inventarios_medicamentos.html', inventarios=inventarios, medicamentos=medicamentos, eps_list=eps_list)

    if request.method == "POST":
        id_medicamento = request.form.get("id_medicamento")
        id_eps = request.form.get("id_eps")
        stock_actual = request.form.get("stock_actual")
        fecha_actualizacion = request.form.get("fecha_actualizacion")

        # Agrega la función para insertar inventario
        def insertar_inventario(id_medicamento, id_eps, stock_actual, fecha_actualizacion):
            cursor = db.cursor()

            query_insert_inventario = """
                INSERT INTO inventarios_medicamentos (ID_Medicamento, ID_EPS, Stock_Actual, Fecha_Actualizacion)
                VALUES (%s, %s, %s, %s);
            """
            cursor.execute(query_insert_inventario, (id_medicamento, id_eps, stock_actual, fecha_actualizacion))
            db.commit()

        insertar_inventario(id_medicamento, id_eps, stock_actual, fecha_actualizacion)
        flash('Inventario registrado exitosamente', 'success')
        return redirect(url_for('inventarios_medicamentos'))

    return render_template('inventarios_medicamentos.html')





# Configuración para Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # Puerto de STARTTLS
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'kcharlis16@gmail.com'
app.config['MAIL_PASSWORD'] = 'TuContraseña'

mail = Mail(app)

# formulario usando Flask-WTF
class ContactForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    correo = StringField('Correo electrónico', validators=[DataRequired(), Email()])
    mensaje = TextAreaField('Mensaje', validators=[DataRequired()])

# Ruta para la página de contacto
@app.route("/contactanos", methods=["GET", "POST"])
def contactanos():
    form = ContactForm()

    if request.method == "POST" and form.validate_on_submit():
        nombre = form.nombre.data
        correo = form.correo.data
        mensaje = form.mensaje.data

        msg = Message('Nuevo mensaje de contacto',
                      sender=correo,
                      recipients=['kcharlis16@gmail.com'])

        msg.body = f"Nombre: {nombre}\nCorreo: {correo}\n\nMensaje:\n{mensaje}"

        try:
            mail.send(msg)
            flash('Mensaje enviado correctamente', 'success')
        except Exception as e:
            flash('Error al enviar el mensaje. Inténtalo de nuevo más tarde.', 'error')

        return redirect(url_for('contactanos'))

    return render_template('contactanos.html', form=form)




if __name__ == "__main__":
    app.run(debug=True)
