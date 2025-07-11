from flask import Flask, render_template, request, send_file
from holerite_system import HoleriteGenerator
import os
from io import BytesIO

app = Flask(__name__)

# Configurações do banco Oracle
db_config = {
    'host': '192.168.1.4',
    'port': 1521,
    'service_name': 'prodpdb',
    'user': 'grupoael',
    'password': 'sapael'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    num_cad = request.form.get('num_cad')
    if not num_cad or not num_cad.isdigit():
        return "Matrícula inválida.", 400

    sql_file = 'holerite.sql'

    generator = HoleriteGenerator(db_config)
    try:
        if not generator.connect_database():
            return "Erro ao conectar ao banco de dados.", 500

        columns, data = generator.execute_sql_file(sql_file, num_cad)

        if not data:
            return "Nenhum registro encontrado para a matrícula informada.", 404

        pdf_data = generator.generate_pdf_in_memory(columns, data)
        
        return send_file(
            BytesIO(pdf_data),
            as_attachment=True,
            download_name=f'holerite_{num_cad}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return f"Erro ao gerar o holerite: {e}", 500
    finally:
        generator.disconnect_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)