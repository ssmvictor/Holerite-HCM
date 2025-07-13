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
    mes = request.form.get('mes')
    ano = request.form.get('ano')
    tipo_calculo = request.form.get('tipo_calculo')
    
    if not num_cad or not num_cad.isdigit():
        return "Matrícula inválida.", 400
    if not mes or not ano:
        return "Mês e ano são obrigatórios.", 400
    if not tipo_calculo:
        return "Tipo de cálculo é obrigatório.", 400
    
    # Validar mês
    try:
        mes_int = int(mes)
        if mes_int < 1 or mes_int > 12:
            return "Mês inválido. Deve estar entre 01 e 12.", 400
    except ValueError:
        return "Mês inválido.", 400
    
    # Validar ano
    try:
        ano_int = int(ano)
        if ano_int < 2020 or ano_int > 2030:
            return "Ano inválido. Deve estar entre 2020 e 2030.", 400
    except ValueError:
        return "Ano inválido.", 400
    
    # Validar tipo de cálculo
    tipos_validos = ['11', '91', '31', '32']
    if tipo_calculo not in tipos_validos:
        return "Tipo de cálculo inválido.", 400

    # Converter para formato dd/mm/yyyy (primeiro dia do mês)
    per_ref_formatted = f"01/{mes.zfill(2)}/{ano}"

    sql_file = 'holerite.sql'

    generator = HoleriteGenerator(db_config)
    try:
        if not generator.connect_database():
            return "Erro ao conectar ao banco de dados.", 500

        columns, data = generator.execute_sql_file(sql_file, num_cad, per_ref_formatted, tipo_calculo)

        if not data:
            return "Nenhum registro encontrado para a matrícula informada.", 404

        pdf_data = generator.generate_pdf_in_memory(columns, data)
        
        # Mapear tipo de cálculo para nome do arquivo
        tipo_nomes = {
            '11': 'folha',
            '91': 'adiantamento',
            '31': 'decimo_adiantamento',
            '32': 'decimo_integral'
        }
        tipo_nome = tipo_nomes.get(tipo_calculo, 'folha')
        
        return send_file(
            BytesIO(pdf_data),
            as_attachment=True,
            download_name=f'holerite_{num_cad}_{mes}_{ano}_{tipo_nome}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        return f"Erro ao gerar o holerite: {e}", 500
    finally:
        generator.disconnect_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)