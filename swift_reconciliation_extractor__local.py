import os
import re
from datetime import datetime

import fitz  # PyMuPDF
from openpyxl import Workbook

# if 'data_loader' not in globals():
# 	from mage_ai.data_preparation.decorators import data_loader
# if 'test' not in globals():
# 	from mage_ai.data_preparation.decorators import test


# Informe aqui o caminho completo para o arquivo MT950 local.
SWIFT_FILE_PATH = r'C:\\Users\\saturnino.mendes\\Documents\\projects\\rec_swift_extract\\asstes\\MT950.2026.06.26-08.06.04.635.25JUN25JUN92761.pdf'
EXCEL_FILE_NAME = 'swift_mt950_movimentos.xlsx'


def _convert_amount(amount_text):
	"""Converte valores SWIFT no formato 1.234,56 para float."""
	return float(amount_text.replace('.', '').replace(',', '.'))


def extract_transactions(swift_text):
	"""Extrai Debito, Credito e Reference, incluindo linhas de continuacao."""
	transactions = {}
	transaction_number = 1

	transaction_pattern = re.compile(
		r'^\s*(\d{6})\s+\d{4}\s+\S+\s+(.*?)\s+#\s*([\d.,]+)\s*#\s*([CD])\s*$',
	)
	lines = swift_text.splitlines()
	line_number = 0

	while line_number < len(lines):
		match = transaction_pattern.match(lines[line_number])
		if not match:
			line_number += 1
			continue

		reference_parts = [match.group(2).strip().rstrip('-').strip()]
		transaction_date = datetime.strptime(match.group(1), '%y%m%d')
		amount = _convert_amount(match.group(3))
		credit_or_debit = match.group(4)
		line_number += 1

		while line_number < len(lines):
			continuation = lines[line_number].strip()
			if transaction_pattern.match(lines[line_number]) or continuation.startswith(('62', '64')):
				break
			if continuation:
				reference_parts.append(continuation)
			line_number += 1

		reference = ' '.join(reference_parts)

		transactions[transaction_number] = {
			'Data': transaction_date,
			'Débito': amount if credit_or_debit == 'D' else 0,
			'Crédito': amount if credit_or_debit == 'C' else 0,
			'Descrição': reference,
		}
		transaction_number += 1

	return transactions


def export_to_excel(transactions):
	"""Gera o Excel na mesma pasta deste arquivo Python."""
	output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), EXCEL_FILE_NAME)
	workbook = Workbook()
	worksheet = workbook.active
	worksheet.title = 'Movimentos'
	worksheet.append(['Data', 'Débito', 'Crédito', 'Descrição'])

	for transaction in transactions.values():
		worksheet.append([
			transaction['Data'],
			transaction['Débito'],
			transaction['Crédito'],
			transaction['Descrição'],
		])

	for cell in worksheet['A'][1:]:
		cell.number_format = 'mm-dd-yyyy'
	for cell in worksheet['B'][1:] + worksheet['C'][1:]:
		cell.number_format = '#,##0.00'

	worksheet.column_dimensions['A'].width = 16
	worksheet.column_dimensions['B'].width = 16
	worksheet.column_dimensions['C'].width = 16
	worksheet.column_dimensions['D'].width = 50
	workbook.save(output_path)
	return output_path


def load_data_from_file():
	"""
	Load the text from a local SWIFT MT950 PDF file.
	"""
	if not SWIFT_FILE_PATH or not os.path.isfile(SWIFT_FILE_PATH):
		raise FileNotFoundError(
			f'Arquivo SWIFT local nao encontrado: {SWIFT_FILE_PATH}'
		)

	try:
		with fitz.open(SWIFT_FILE_PATH) as document:
			swift_text = '\n'.join(page.get_text() for page in document)
	except Exception as error:
		raise RuntimeError(
			f'Erro ao processar o arquivo SWIFT {SWIFT_FILE_PATH}: {error}'
		) from error

	transactions = extract_transactions(swift_text)
	excel_path = export_to_excel(transactions)
	print(f'Transacoes encontradas: {len(transactions)}')
	print(f'Excel gerado: {excel_path}')
	return transactions


load_data_from_file()