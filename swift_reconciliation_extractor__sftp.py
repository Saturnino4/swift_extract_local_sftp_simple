import fitz  # PyMuPDF
import os
import glob
import paramiko
import tempfile
from datetime import datetime

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_file(*args, **kwargs):
    """
    Load data from PDF files retrieved via SFTP
    """
    # Configurações SFTP
    sftp_host = 'XXXXXXXXX'
    sftp_port = 22
    sftp_username = 'sftpuser'  # Considere usar variáveis de ambiente para credenciais
    sftp_password = '12345678'
    remote_dir = '/docs/'
    
    # Criar diretório temporário local para os arquivos
    local_temp_dir = tempfile.mkdtemp()
    
    # Dicionário para armazenar o conteúdo de cada arquivo
    result = {}
    
    try:
        # Estabelecer conexão SFTP
        transport = paramiko.Transport((sftp_host, sftp_port))
        transport.connect(username=sftp_username, password=sftp_password)
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        today = str(datetime.today().date()).replace('-','.')
        print(f"Filtrando arquivos para a data: {today}")
        
        # Inicializar lista de arquivos remotos
        remote_files = []
        
        try:
            # Iterar pelos arquivos no diretório remoto
            for file_name in sftp.listdir(remote_dir):
                try:
                    # Verificar se o arquivo atende aos critérios básicos
                    if file_name.startswith('MT') and file_name.endswith('.pdf'):
                        # Extrair a data do formato do arquivo
                        parts = file_name.split('.')
                        if len(parts) >= 4:
                            date_on_file = f"{parts[1]}.{parts[2]}.{parts[3].split('-')[0]}"
                            
                            if today == date_on_file:
                                remote_files.append(file_name)
                                print(f"Arquivo selecionado: {file_name}")
                            else:
                                print(f"Arquivo ignorado (data não corresponde): {file_name}")
                except Exception as e:
                    print(f"Erro ao processar nome do arquivo {file_name}: {str(e)}")
                    # Continue para o próximo arquivo mesmo se houver erro
                    continue
            
            # Imprimir resultado da filtragem
            print(f"Total de arquivos encontrados: {len(remote_files)}")
            
            # Baixar e processar cada arquivo encontrado
            for remote_file in remote_files:
                remote_path = os.path.join(remote_dir, remote_file)
                local_path = os.path.join(local_temp_dir, remote_file)
                
                # Baixar o arquivo
                sftp.get(remote_path, local_path)
                print(f"Arquivo baixado: {remote_file}")
                
                # Processar o PDF
                try:
                    text = ""
                    doc = fitz.open(local_path)
                    for page in doc:
                        text += page.get_text()
                    doc.close()
                    
                    # Armazenar o texto com o nome do arquivo como chave
                    result[remote_file] = text
                    print(f"Processado: {remote_file}")
                    
                except Exception as e:
                    print(f"Erro ao processar {remote_file}: {str(e)}")
                
                # Remover o arquivo local temporário
                os.remove(local_path)
                
        except Exception as e:
            print(f"Erro ao listar/processar arquivos: {str(e)}")
        
        # Verificar se algum arquivo foi encontrado (após o loop)
        if not remote_files:
            print(f"Aviso: Nenhum arquivo SWIFT encontrado para hoje ({today}) em {remote_dir}")
            
    except Exception as e:
        print(f"Erro na conexão SFTP: {str(e)}")
        # Não relança a exceção - permite que o script continue
    
    finally:
        # Fechar conexões SFTP se estiverem abertas
        if 'sftp' in locals() and sftp:
            sftp.close()
        if 'transport' in locals() and transport:
            transport.close()
            
        # Limpar diretório temporário
        try:
            os.rmdir(local_temp_dir)
        except:
            print(f"Aviso: Não foi possível remover o diretório temporário: {local_temp_dir}")
    
    return result


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
    assert isinstance(output, dict), 'Output should be a dictionary'
    
    if len(output) > 0:
        for filename, content in output.items():
            print(f"Arquivo: {filename} - Primeiros 50 caracteres: {content[:50]}")
    else:
        print("Nenhum arquivo SWIFT processado nesta execução.")