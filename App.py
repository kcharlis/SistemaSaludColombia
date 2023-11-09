from flask import Flask, request, render_template
import mysql.connector

app = Flask(__name__)

# Configuración de la conexión a la BD
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456",
    database="SistemaSaludColombia"
)

# Ruta para obtener todos los pacientes con detalles de historias clínicas y EPS
@app.route("/pacientes", methods=["GET"])
def get_pacientes():
    cursor = db.cursor()
    query = """
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
            EPS.Nombre AS Nombre_EPS
        FROM Pacientes
        LEFT JOIN Historias_Clinicas ON Pacientes.ID_Paciente = Historias_Clinicas.ID_Paciente
        LEFT JOIN EPS ON Pacientes.ID_EPS = EPS.ID_EPS;
    """
    cursor.execute(query)
    pacientes_detalles = cursor.fetchall()

    return render_template('pacientes_detalles.html', pacientes_detalles=pacientes_detalles)

# Ruta para buscar un paciente por ID
@app.route("/buscar_paciente_por_id", methods=["GET"])
def buscar_paciente_por_id():
    id_paciente = request.args.get('idPaciente')
    cursor = db.cursor()
    query = """
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
            EPS.Nombre AS Nombre_EPS
        FROM Pacientes
        LEFT JOIN Historias_Clinicas ON Pacientes.ID_Paciente = Historias_Clinicas.ID_Paciente
        LEFT JOIN EPS ON Pacientes.ID_EPS = EPS.ID_EPS
        WHERE Pacientes.ID_Paciente = %s;
    """
    cursor.execute(query, (id_paciente,))
    paciente_encontrado = cursor.fetchall()

    return render_template('resultado_busqueda.html', paciente_encontrado=paciente_encontrado)

if __name__ == "__main__":
    app.run(debug=True)
