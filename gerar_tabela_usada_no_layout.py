'''
Gera a tabela Planilha_ONVC_ECR_CAR.xlsx que é usada na geração dos laudos
Anteriormente era feita manualmente a partir de um Join, aqui combinamos os resultados do intersect com a camada 
para a partir de um merge gerar a tabela
'''

import configparser
import os
import logging
from logging.handlers import RotatingFileHandler
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd

config_path = os.path.join('config', "config.ini") # Caminho do arquivo de configuração
config = configparser.ConfigParser() # Ler o arquivo de configuração
config.read(config_path)

def setup_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    log_file = os.path.join("logs", "execucao.log") # Diretório dedicado para logs
    # Configurar handlers
    handlers = [
        RotatingFileHandler( log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8"),
        logging.StreamHandler()]
    logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)

def conectar_portal():
    portal_url = config["PORTAL"]["URL_PORTAL"]
    username = config["PORTAL"]["GIS_USER"]
    password = config["PORTAL"]["GIS_PASSWORD"]
    try:
        gis = GIS(portal_url, username=username, password=password)
        logging.info("✅ Conexão com ArcGIS Online estabelecida.")
        return gis
    except Exception as e:
        logging.error(f"❌ Erro ao conectar ao ArcGIS Online: {e}")

def baixar_csvs(url, arquivo):
    saida_csvs = r"CSVs"
    os.makedirs(saida_csvs, exist_ok=True)
    # URLs das tabelas
    urls = {'camada': f'{url}/0'}
    dfs = {} # Dicionário para armazenar os DataFrames
    for nome, url in urls.items(): # Loop para criar cada DataFrame
        try:
            layer = FeatureLayer(url) # Carrega a tabela
            query_result = layer.query(where="1=1", out_fields="*", result_record_count=10) # Consulta os dados
            if len(query_result.features) > 0:
                df = pd.DataFrame([f.attributes for f in query_result.features])
                dfs[nome] = df
            else:
                logging.warning(f"⚠️  Aviso: Nenhum registro encontrado para {nome}DF")
        except Exception as e:
            logging.error(f"❌ Erro ao processar {nome}: {str(e)}")
    for nome_df, df in dfs.items():
        try:
            df.to_excel(f"{saida_csvs}\\{arquivo}.xlsx", index=False)
        except Exception as e:
            logging.error(f"❌ Erro ao salvar o DataFrame '{arquivo}': {str(e)}")
    logging.info(f"✅ CSVs salvos!")

def execucao():
    """
    Função que compila a execução de todas as funções
    """
    setup_logging() # Configura o logging

    conectar_portal() # Se conecta ao portal

    # Coleta os links que estão no arquivo config.ini
    csv_url = config["PORTAL"]["CSV_URL"]
    car_url = config["PORTAL"]["CAR_URL"]

    # Baixa os CSVs direto do portal
    baixar_csvs(csv_url, "alertas_em_uso")
    baixar_csvs(car_url, "tabela_car")

    # Lê os arquivos no formato DataFrame
    car_df = pd.read_excel(r"CSVs\tabela_car.xlsx")
    alertas_df = pd.read_excel(r"CSVs\alertas_em_uso.xlsx")
    intersecoes_car = pd.read_csv(r"CSVs\tabela_nova_camada_inter_GPL_08_Codigo_CAR.csv", delimiter=';')

    lista_ids = []
    lista_cars = []
    lista_ids = intersecoes_car['id'].tolist() # Cria uma lista com os ids
    lista_cars = intersecoes_car['cod_imovel'].tolist() # Cria uma lista com os cars

    # Pega apenas as colunas de interesse
    alertas_df = alertas_df[['id', 'data_refer', 'data_atual', 'area_m2', 'area_ha', 'centro_x', 'centro_y', 'link_kml', 'ant_dep']].copy()

    # Para evitar que o merge crie colunas duplicadas com sufixos (_x, _y)
    colunas_em_comum = alertas_df.columns.drop('id')
    intersecoes_car_limpo = intersecoes_car.drop(columns=colunas_em_comum, errors='ignore')

    # Realiza o merge, combinando as informações
    DF = pd.merge(intersecoes_car_limpo, alertas_df, on='id')

    # Salva a tabela em formato excel
    DF.to_excel(r"CSVs\Planilha_ONVC_ECR_CAR.xlsx", index=False)

# Chama a função com tratamento de erros
try:
    execucao()
except Exception as e:
    logging.error(f"❌ Erro na execução: {str(e)}")