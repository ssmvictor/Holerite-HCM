#!/usr/bin/env python3
"""
Script simplificado para executar o sistema de holerite
As configurações são carregadas do arquivo .env
"""

from holerite_system import HoleriteGenerator
import os
from dotenv import load_dotenv

def main():
    """Executa o sistema de holerite com configurações personalizadas"""
    
    # Carrega as variáveis de ambiente do arquivo .env
    load_dotenv()
    
    # ========================================
    # CONFIGURAÇÕES - Carregadas do .env
    # ========================================
    
    # Configurações do banco Oracle a partir de variáveis de ambiente
    db_config = {
        'host': os.getenv('host'),
        'port': int(os.getenv('port', 1521)),
        'service_name': os.getenv('service_name'),
        'user': os.getenv('user'),
        'password': os.getenv('password')
    }
    
    # Validação das variáveis de ambiente
    required_vars = ['host', 'service_name', 'user', 'password']
    missing_vars = [var for var in required_vars if not db_config[var]]

    if missing_vars:
        print("ERRO: As seguintes variáveis de ambiente obrigatórias não foram definidas no arquivo .env:")
        for var in missing_vars:
            print(f"- {var}")
        return

    # Caminhos dos arquivos
    sql_file = 'holerite.sql'  # Arquivo SQL fornecido
    output_pdf = 'holerite_gerado.pdf'  # Arquivo PDF de saída
    
    # ========================================
    # EXECUÇÃO DO SISTEMA
    # ========================================
    
    print("=== SISTEMA DE GERAÇÃO DE HOLERITE ===")
    
    # Solicita o número de matrícula
    num_cad = input("Digite o código de matrícula do funcionário: ")
    if not num_cad.isdigit():
        print("ERRO: Matrícula inválida. Por favor, insira apenas números.")
        return

    print(f"Arquivo SQL: {sql_file}")
    print(f"Arquivo PDF de saída: {output_pdf}")
    print(f"Matrícula: {num_cad}")
    print()
    
    # Verifica se o arquivo SQL existe
    if not os.path.exists(sql_file):
        print(f"ERRO: Arquivo SQL não encontrado: {sql_file}")
        return
    
    # Cria o gerador
    generator = HoleriteGenerator(db_config)
    
    try:
        print("1. Conectando ao banco Oracle...")
        if not generator.connect_database():
            print("ERRO: Falha na conexão com o banco de dados.")
            print("Verifique as configurações de conexão no arquivo .env.")
            return
        
        print("2. Executando consulta SQL...")
        columns, data = generator.execute_sql_file(sql_file, num_cad)
        
        if data is None:
            print("ERRO: Falha na execução da consulta SQL.")
            return
        
        if len(data) == 0:
            print("AVISO: Nenhum registro encontrado para a matrícula informada.")
            print("Verifique os parâmetros da consulta SQL e a matrícula.")
            return
        
        print(f"   Encontrados {len(data)} registros.")
        
        print("3. Gerando PDF...")
        # Gera o PDF
        generator.generate_pdf_modelo(columns, data, output_pdf)
        
        print()
        print("=== PROCESSO CONCLUÍDO COM SUCESSO! ===")
        print(f"Arquivo PDF gerado: {output_pdf}")
        
        # Verifica se o arquivo foi criado
        if os.path.exists(output_pdf):
            file_size = os.path.getsize(output_pdf)
            print(f"Tamanho do arquivo: {file_size:,} bytes")
        
    except Exception as e:
        print(f"ERRO durante a execução: {e}")
        print("Verifique as configurações e tente novamente.")
        
    finally:
        print("4. Encerrando conexão com o banco...")
        generator.disconnect_database()

if __name__ == "__main__":
    main()