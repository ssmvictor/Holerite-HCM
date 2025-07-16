from flask import Flask, render_template, request, send_file, jsonify
from holerite_system import HoleriteGenerator
import os
from io import BytesIO
from datetime import datetime

app = Flask(__name__)

# Configurações do banco Oracle
db_config = {
    'host': '192.168.1.4',
    'port': 1521,
    'service_name': 'prodpdb',
    'user': 'grupoael',
    'password': 'sapael'
}

def is_valid_date(date_string):
    try:
        datetime.strptime(date_string, '%d/%m/%Y')
        return True
    except ValueError:
        return False

def is_valid_cpf(cpf):
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False

    # Validação do primeiro dígito
    sum_of_products = sum(int(cpf[i]) * (10 - i) for i in range(9))
    expected_digit = (sum_of_products * 10) % 11
    if expected_digit == 10:
        expected_digit = 0
    if int(cpf[9]) != expected_digit:
        return False

    # Validação do segundo dígito
    sum_of_products = sum(int(cpf[i]) * (11 - i) for i in range(10))
    expected_digit = (sum_of_products * 10) % 11
    if expected_digit == 10:
        expected_digit = 0
    if int(cpf[10]) != expected_digit:
        return False

    return True

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/check_first_access', methods=['POST'])
def check_first_access():
    data = request.get_json()
    num_cad = data.get('num_cad')
    if not num_cad:
        return jsonify({'message': 'Matrícula é obrigatória.'}), 400

    generator = HoleriteGenerator(db_config)
    try:
        if not generator.connect_database():
            return jsonify({'message': 'Erro ao conectar ao banco de dados.'}), 500
        
        is_first = generator.verificar_primeiro_acesso(num_cad)
        return jsonify({'is_first_access': is_first})
    except Exception as e:
        return jsonify({'message': f'Erro ao verificar primeiro acesso: {e}'}), 500
    finally:
        generator.disconnect_database()

@app.route('/set_password', methods=['POST'])
def set_password():
    data = request.get_json()
    num_cad = data.get('num_cad')
    nova_senha = data.get('nova_senha')

    if not all([num_cad, nova_senha]):
        return jsonify({'message': 'Matrícula e nova senha são obrigatórios.'}), 400

    # Validação da senha
    if not (6 <= len(nova_senha) <= 12 and any(c.isupper() for c in nova_senha) and any(c.isdigit() for c in nova_senha)):
        return jsonify({'message': 'A senha deve ter entre 6 e 12 caracteres, com pelo menos uma letra maiúscula e um número.'}), 400

    generator = HoleriteGenerator(db_config)
    try:
        if not generator.connect_database():
            return jsonify({'message': 'Erro ao conectar ao banco de dados.'}), 500
        
        success, error_message = generator.atualizar_senha(num_cad, nova_senha)
        if success:
            return jsonify({'message': 'Senha atualizada com sucesso!'})
        else:
            return jsonify({'message': error_message}), 500
    except Exception as e:
        return jsonify({'message': f'Erro ao definir a senha: {e}'}), 500
    finally:
        generator.disconnect_database()

@app.route('/validar', methods=['POST'])
def validar():
    data = request.get_json()
    num_cad = data.get('num_cad')
    cpf = data.get('cpf')
    credential = data.get('credential')
    mes = data.get('mes')
    ano = data.get('ano')
    tipo_calculo = data.get('tipo_calculo')

    if not all([num_cad, cpf, credential, mes, ano, tipo_calculo]):
        return jsonify({'message': 'Todos os campos são obrigatórios.'}), 400

    if not is_valid_cpf(cpf):
        return jsonify({'message': 'CPF inválido.'}), 400

    cpf_cleaned = ''.join(filter(str.isdigit, cpf))
    generator = HoleriteGenerator(db_config)
    try:
        if not generator.connect_database():
            return jsonify({'message': 'Erro ao conectar ao banco de dados.'}), 500

        is_first = generator.verificar_primeiro_acesso(num_cad)
        
        if is_first and not is_valid_date(credential):
            return jsonify({'message': 'Data de nascimento inválida.'}), 400

        if not generator.validar_credenciais(num_cad, cpf_cleaned, credential, is_first):
            return jsonify({'message': 'Dados incorretos. Verifique a matrícula, CPF e data de nascimento/senha.'}), 401

        per_ref_formatted = f"01/{mes.zfill(2)}/{ano}"
        sql_file = 'holerite.sql'
        columns, data = generator.execute_sql_file(sql_file, num_cad, per_ref_formatted, tipo_calculo)

        if not data:
            return jsonify({'message': 'Nenhum registro encontrado para os dados informados.'}), 404

        pdf_data = generator.generate_pdf_in_memory(columns, data)
        
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
        return jsonify({'message': f'Erro ao gerar o holerite: {e}'}), 500
    finally:
        generator.disconnect_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)