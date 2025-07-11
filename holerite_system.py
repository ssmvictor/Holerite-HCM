#!/usr/bin/env python3
"""
Sistema de Geração de Holerite
Conecta ao banco Oracle, executa SQL e gera PDF
"""
 
import oracledb
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
from datetime import datetime
from decimal import Decimal
from io import BytesIO

class HoleriteGenerator:
    def __init__(self, db_config):
        """
        Inicializa o gerador de holerite
        
        Args:
            db_config (dict): Configurações do banco de dados
                - host: endereço do servidor Oracle
                - port: porta do servidor (padrão 1521)
                - service_name: nome do serviço Oracle
                - user: usuário do banco
                - password: senha do usuário
        """
        self.db_config = db_config
        self.connection = None
        
    def connect_database(self):
        """Conecta ao banco de dados Oracle"""
        try:
            dsn = oracledb.makedsn(
                host=self.db_config['host'],
                port=self.db_config.get('port', 1521),
                service_name=self.db_config['service_name']
            )
            
            self.connection = oracledb.connect(
                user=self.db_config['user'],
                password=self.db_config['password'],
                dsn=dsn
            )
            print("Conexão com Oracle estabelecida com sucesso!")
            return True
            
        except Exception as e:
            print(f"Erro ao conectar ao banco Oracle: {e}")
            return False
    
    def disconnect_database(self):
        """Desconecta do banco de dados"""
        if self.connection:
            self.connection.close()
            print("Conexão com Oracle encerrada.")
    
    def execute_sql_file(self, sql_file_path, num_cad):
        """
        Executa o SQL do arquivo fornecido
        
        Args:
            sql_file_path (str): Caminho para o arquivo SQL
            num_cad (str): Número de cadastro do funcionário
            
        Returns:
            list: Lista de tuplas com os resultados da consulta
        """
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                sql_query = file.read()
            
            # Substitui o placeholder pelo número de cadastro real
            sql_query = sql_query.replace('AND VRS.NUMCAD = 175', f'AND VRS.NUMCAD = {num_cad}')

            cursor = self.connection.cursor()
            cursor.execute(sql_query)
            
            # Obtém os nomes das colunas
            columns = [desc[0] for desc in cursor.description]
            
            # Obtém os dados
            data = cursor.fetchall()
            cursor.close()
            
            print(f"Consulta executada com sucesso! {len(data)} registros encontrados.")
            return columns, data
            
        except Exception as e:
            print(f"Erro ao executar SQL: {e}")
            return None, None
    
    def format_currency(self, value):
        """Formata valor monetário"""
        if value is None:
            return "R$ 0,00"
        
        # Converte para Decimal se necessário
        if isinstance(value, (int, float)):
            value = Decimal(str(value))
        
        # Formata o valor
        formatted = f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return formatted

    def _build_story(self, columns, data):
        story = []
        # Agrupa dados por funcionário
        funcionarios = {}
        for row in data:
            row_dict = dict(zip(columns, row))
            numcad = row_dict.get('NUMCAD', 'N/A')
            if numcad not in funcionarios:
                funcionarios[numcad] = {'info': row_dict, 'eventos': []}
            funcionarios[numcad]['eventos'].append(row_dict)

        for numcad, func_data in funcionarios.items():
            info = func_data['info']
            eventos = func_data['eventos']

            # Estilos
            style_header_empresa = ParagraphStyle('header_empresa', fontSize=9, alignment=TA_LEFT)
            style_header_title = ParagraphStyle('header_title', fontSize=10, alignment=TA_CENTER, fontName='Helvetica-Bold')
            style_header_mes = ParagraphStyle('header_mes', fontSize=9, alignment=TA_RIGHT)
            style_label = ParagraphStyle('label', fontSize=6, textColor=colors.grey)
            style_value = ParagraphStyle('value', fontSize=8, fontName='Helvetica-Bold')
            style_table_header = ParagraphStyle('table_header', fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)
            style_table_cell = ParagraphStyle('table_cell', fontSize=8, alignment=TA_LEFT)
            style_table_cell_right = ParagraphStyle('table_cell_right', fontSize=8, alignment=TA_RIGHT)
            style_footer_label = ParagraphStyle('footer_label', fontSize=6, textColor=colors.grey, alignment=TA_LEFT)
            style_footer_value = ParagraphStyle('footer_value', fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)
            style_message = ParagraphStyle('message', fontSize=7, alignment=TA_LEFT)

            # Header
            logo_path = 'static/logo.png'  # Caminho para o arquivo de logo
            logo = Image(logo_path, width=50*mm, height=23*mm)

            perref = info.get('PERREF', '')
            mes_ano_formatado = ''
            if isinstance(perref, str) and len(perref) == 10 and perref[2] == '/' and perref[5] == '/':
                # Formato: DD/MM/YY -> MM/YYYY (brasileiro)
                dia = perref[:2]
                mes = perref[3:5]
                ano = '20' + perref[8:] # Assumindo que 'YY' é '25' para 2025
                mes_ano_formatado = f"{mes}/{ano}"
            elif isinstance(perref, datetime):
                mes_ano_formatado = perref.strftime('%m/%Y')
            else:
                mes_ano_formatado = str(perref) 

            header_data = [
                [logo, Paragraph('EMPRESA: NOME DA EMPRESA', style_header_empresa)],
                ['', Paragraph(f'MÊS/ANO: {mes_ano_formatado}', style_header_mes)],
                ['', Paragraph('Página: 0001', style_header_mes)]
            ]
            header_table = Table(header_data, colWidths=[60*mm, 130*mm])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (0,2), 'MIDDLE'),
                ('SPAN', (0,0), (0,2)),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph('Demonstrativo de Pagamento de Salário', style_header_title))
            story.append(Spacer(1, 2*mm))

            # Employee Info
            employee_data = [
                [Paragraph('CADASTRO', style_label), Paragraph('NOME', style_label), '', Paragraph('LOCAL', style_label)],
                [Paragraph(str(info.get('NUMCAD', '')), style_value), Paragraph(info.get('NOME', ''), style_value), '', Paragraph(info.get('LOCAL', ''), style_value)],
                [Paragraph('DATA ADMISSÃO', style_label), Paragraph('CARGO', style_label), '', Paragraph('', style_label)],
                [Paragraph(info.get('DATADM', '').strftime('%d/%m/%Y') if info.get('DATADM') else '', style_value), Paragraph(info.get('CARGO', ''), style_value), '', '']
            ]
            employee_table = Table(employee_data, colWidths=[40*mm, 90*mm, 10*mm, 50*mm])
            employee_table.setStyle(TableStyle([
                ('LINEBELOW', (0,1), (1,1), 1, colors.black),
                ('LINEBELOW', (3,1), (3,1), 1, colors.black),
                ('LINEBELOW', (0,3), (1,3), 1, colors.black),
            ]))
            story.append(employee_table)
            story.append(Spacer(1, 5*mm))

            # Events Table
            events_header = [
                Paragraph('CÓD', style_table_header),
                Paragraph('DESCRIÇÃO', style_table_header),
                Paragraph('REFERÊNCIA', style_table_header),
                Paragraph('VENCIMENTOS', style_table_header),
                Paragraph('DESCONTOS', style_table_header)
            ]
            events_data = [events_header]
            total_vencimentos = Decimal('0')
            total_descontos = Decimal('0')

            for evento in eventos:
                tipo = int(evento.get('TIPEVE', 0))
                if tipo == 4:
                    continue

                vencimento = ''
                desconto = ''
                valor = Decimal(evento.get('VLRREAL', '0'))

                if tipo in [1, 2]: # Proventos
                    vencimento = self.format_currency(valor)
                    total_vencimentos += valor
                elif tipo == 3: # Descontos
                    desconto = self.format_currency(abs(valor))
                    total_descontos += abs(valor)

                events_data.append([
                    Paragraph(str(evento.get('CODEVE', '')), style_table_cell),
                    Paragraph(evento.get('DESEVE', ''), style_table_cell),
                    Paragraph(str(evento.get('REFERÊNCIA', '')), style_table_cell_right),
                    Paragraph(vencimento, style_table_cell_right),
                    Paragraph(desconto, style_table_cell_right)
                ])

            events_table = Table(events_data, colWidths=[20*mm, 70*mm, 30*mm, 35*mm, 35*mm])
            events_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ]))
            story.append(events_table)
            story.append(Spacer(1, 5*mm))

            # Footer
            fgts_valor = Decimal('0')
            for evento in eventos:
                if evento.get('CODEVE') == 300:
                    fgts_valor = Decimal(evento.get('VLRIMP', '0'))
                    break
            valor_liquido = total_vencimentos - total_descontos
            footer_data = [
                [Paragraph('SALARIO BASE', style_footer_label), Paragraph('BASE CÁLC. FGTS', style_footer_label), Paragraph('FGTS DO MÊS', style_footer_label), '', Paragraph('TOTAL DE VENCIMENTOS', style_footer_label)],
                [Paragraph(self.format_currency(info.get('SALBASE', 0)), style_footer_value), Paragraph(self.format_currency(info.get('BASEINSS', 0)), style_footer_value), Paragraph(self.format_currency(fgts_valor), style_footer_value), '', Paragraph(self.format_currency(total_vencimentos), style_footer_value)],
                [Paragraph('SALARIO CONTR. INSS', style_footer_label), Paragraph('BASE CÁLCULO IRRF', style_footer_label), Paragraph('FAIXA IRRF', style_footer_label), '', Paragraph('TOTAL DE DESCONTOS', style_footer_label)],
                [Paragraph(self.format_currency(info.get('BASEINSS', 0)), style_footer_value), Paragraph(self.format_currency(info.get('BASEIR', 0)), style_footer_value), Paragraph(str(info.get('FAIXAIR', '')), style_footer_value), '', Paragraph(self.format_currency(total_descontos), style_footer_value)],
                ['', '', '', '', Paragraph('VALOR LÍQUIDO', style_footer_label)],
                ['', '', '', '', Paragraph(self.format_currency(valor_liquido), style_footer_value)],
                [Paragraph('BANCO DEPOSITÁRIO', style_footer_label), Paragraph('AGÊNCIA', style_footer_label), Paragraph('CONTA', style_footer_label), Paragraph('DÍGITO', style_footer_label), ''],
                [Paragraph('Banco Itau S/A', style_value), Paragraph(str(info.get('CODAGE', '')), style_value), Paragraph(str(info.get('CONBAN', '')), style_value), Paragraph(str(info.get('DIGBAN', '')), style_value), '']
            ]
            footer_table = Table(footer_data, colWidths=[40*mm, 40*mm, 40*mm, 30*mm, 40*mm])
            footer_table.setStyle(TableStyle([
                ('LINEABOVE', (0,0), (4,0), 1, colors.black),
                ('LINEBELOW', (0,1), (4,1), 1, colors.black),
                ('LINEABOVE', (0,2), (4,2), 1, colors.black),
                ('LINEBELOW', (0,3), (4,3), 1, colors.black),
                ('LINEABOVE', (4,4), (4,4), 1, colors.black),
                ('LINEBELOW', (4,5), (4,5), 1, colors.black),
                ('LINEABOVE', (0,6), (3,6), 1, colors.black),
                ('LINEBELOW', (0,7), (3,7), 1, colors.black),
            ]))
            story.append(footer_table)
            story.append(Spacer(1, 5*mm))

            # Messages
            story.append(Paragraph('Informar ao RH quando: Alterar Estado Civil, nasc.filhos, endereço.', style_message))
            story.append(Paragraph('Para receber cotas SAL.FAMILIA, deve apresentar ao RH: Mês 5 e 11 Comp.Escolar; Mês 11, cartão de vacina filhos até 5 anos', style_message))

            if numcad != list(funcionarios.keys())[-1]:
                story.append(PageBreak())
        return story

    def generate_pdf_modelo(self, columns, data, output_path):
        """
        Gera o PDF do holerite e salva em um arquivo
        """
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4, topMargin=10*mm, bottomMargin=10*mm, leftMargin=10*mm, rightMargin=10*mm)
            story = self._build_story(columns, data)
            doc.build(story)
            print(f"PDF gerado com sucesso: {output_path}")
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
            raise

    def generate_pdf_in_memory(self, columns, data):
        """
        Gera o PDF do holerite em memória
        """
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=10*mm, bottomMargin=10*mm, leftMargin=10*mm, rightMargin=10*mm)
            story = self._build_story(columns, data)
            doc.build(story)
            pdf_data = buffer.getvalue()
            buffer.close()
            print("PDF gerado em memória com sucesso!")
            return pdf_data
        except Exception as e:
            print(f"Erro ao gerar PDF em memória: {e}")
            raise

