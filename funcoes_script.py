# Baixa as tabelas do Survey e as assinaturas

from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from pathlib import Path
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import requests
import os
import logging
from logging.handlers import RotatingFileHandler
import configparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from jinja2 import Template
import re

config_path = os.path.join('config', "config.ini") # Caminho do arquivo de configuração
config = configparser.ConfigParser() # Ler o arquivo de configuração
config.read(config_path)

EMAIL_USER = config["EMAIL"]["EMAIL_USER"]
EMAIL_PASS = config["EMAIL"]["EMAIL_PASS"]
SMTP_SERVER = config["EMAIL"]["SMTP_SERVER"]
SMTP_PORT = int(config["EMAIL"]["SMTP_PORT"])
DEFAULT_RECIPIENT = config["EMAIL"]["DEFAULT_RECIPIENT"]

def setup_logging():
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    log_file = os.path.join("logs", "execucao.log") # Diretório dedicado para logs
    # Configurar handlers
    handlers = [
        RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=3,
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=handlers
    )

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

def baixar_csvs():
    saida_csvs = r"CSVs"
    os.makedirs(saida_csvs, exist_ok=True)
    # URLs das tabelas
    url_atual = config["PORTAL"]["CSV_URL"]
    url_link = config["PORTAL"]["URL_LINK"]
    urls = {
        'camada': f'{url_atual}/0',
        'notificacao': f'{url_atual}/1',
        'auto_const': f'{url_atual}/2',
        'medida_cautelar': f'{url_atual}/3',
        'repeat_rl_fotografico': f'{url_atual}/4',
        'assinaturas': f'{url_atual}/5',
        'links': f"{url_link}"
    }
    dfs = {} # Dicionário para armazenar os DataFrames
    for nome, url in urls.items(): # Loop para criar cada DataFrame
        try:
            layer = FeatureLayer(url) # Carrega a tabela
            query_result = layer.query(where="1=1", out_fields="*", result_record_count=10) # Consulta os dados
            if len(query_result.features) > 0:
                df = pd.DataFrame([f.attributes for f in query_result.features])
                dfs[nome] = df
            else:
                logging.error(f"⚠️  Aviso: Nenhum registro encontrado para {nome}DF")
        except Exception as e:
            logging.error(f"❌ Erro ao processar {nome}: {str(e)}")
    # Removendo a coluna e atualizando o dicionário
    dfs['links'] = dfs['links'].drop('observacao', axis=1, errors='ignore')
    for nome_df, df in dfs.items():
        try:
            df.to_excel(f"{saida_csvs}\\{nome_df}.xlsx", index=False)
        except Exception as e:
            logging.error(f"❌ Erro ao salvar o DataFrame '{nome_df}': {str(e)}")
    logging.info(f"✅ CSVs salvos!")

def baixar_imagens():
    gis = conectar_portal()
    id_imagens = config["PORTAL"]["ID_IMAGENS"]
    item = gis.content.get(id_imagens)
    sublayer = item.tables[4]
    oid_field = sublayer.properties.objectIdField # Verificar o campo OID
    features = sublayer.query(where="1=1", return_attachments=True).features # Consulta features (com return_attachments=True)
    token = gis._con.token.replace('\n', '') # Obtem token sem quebras de linha
    lista_imagens = [] # Listar anexos corretamente
    features = sublayer.query(where="1=1").features
    oid_field = sublayer.properties.objectIdField
    pasta_saida = r"Output\assinaturas"
    os.makedirs(pasta_saida, exist_ok=True) # Cria diretório se não existir
    for feature in features:
        try:
            feature_id = feature.attributes.get("nomes", "N/A")
            oid = feature.attributes[oid_field]
            attachments = sublayer.attachments.get_list(oid)
            for attachment in attachments:
                if attachment['name'].lower().endswith('.jpg'):
                    # URL corrigida (com OID e token sem quebras)
                    url_imagem = f"{sublayer.url}/{oid}/attachments/{attachment['id']}?token={token}"
                    lista_imagens.append({
                        "feature_id": feature_id,
                        "nome_imagem": attachment['name'],
                        "url": url_imagem
                    })
        except Exception as e:
            logging.error(f"Erro na feature {oid}: {str(e)}")
    for item in lista_imagens:
        try:
            url = item['url']
            nome_imagem =  f"Assinatura_{item['feature_id']}_{item['nome_imagem']}"
            caminho_imagem = f"{pasta_saida}\\{nome_imagem}"
            # Headers para simular um navegador
            headers = {"Referer": config["PORTAL"]["URL_PORTAL"], 
                       "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            response = requests.get(url, headers=headers, timeout=10, stream=True) # Faz a requisição
            if response.status_code == 200: # Verificar status e conteúdo
                content_type = response.headers.get('Content-Type', '') # Verifica se é uma imagem
                if 'image' not in content_type:
                    logging.error(f"⚠️ A URL não é uma imagem válida: {url} (Content-Type: {content_type})")
                    continue
                with open(caminho_imagem, 'wb') as f: # Salva a imagem em modo binário
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # Filtra chunks vazios
                            f.write(chunk)
                if os.path.getsize(caminho_imagem) > 0: # Verifica se o arquivo foi salvo
                    None
                else:
                    logging.error(f"❌ Arquivo vazio: {caminho_imagem}")
                    os.remove(caminho_imagem)
            else:
                logging.error(f"❌ Falha ao baixar {nome_imagem} (Status: {response.status_code})")
        except Exception as e:
            logging.error(f"🔥 Erro ao baixar {nome_imagem}: {str(e)}")
    logging.info(f"✅ {len(lista_imagens)} assinaturas salvas!")

def criar_gdf():
    service_url = config["PORTAL"]["URL_CAMADA"]
    layer = FeatureLayer(service_url)
    features = layer.query(where="1=1").features
    pontos = [] # Lista para armazenar dados dos pontos (coordenadas + atributos)
    for feature in features:
        if feature.geometry and "x" in feature.geometry and "y" in feature.geometry:
            # Extrair geometria
            x = feature.geometry["x"]
            y = feature.geometry["y"]
            # Extrair atributos (ex: GlobalID, OBJECTID, etc.)
            atributos = feature.attributes  # Dicionário com todos os campos
            pontos.append({
                "Longitude": x,
                "Latitude": y,
                "GlobalID": atributos.get("globalid"),  # Substitua pelo nome correto do campo
                "OBJECTID": atributos.get("objectid"),  # Campo padrão do ArcGIS
                # Adicione outros campos necessários aqui
            })
    df = pd.DataFrame(pontos) # Criar DataFrame com todos os atributos
    df = df[(df["Longitude"].abs() > 1e-10) & (df["Latitude"].abs() > 1e-10)] # Filtrar pontos inválidos (ajuste conforme necessário)
    # Criar GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,  # Usar o DataFrame completo (com atributos)
        geometry=gpd.points_from_xy(df["Longitude"], df["Latitude"]),
        crs="EPSG:4326"
    )
    return gdf

def plot_each_point(
    gdf,
    png_folder,
    buffer_distance=50,
    color='red',
    opacity=0.9,
    marker_size=200,
    basemap_source=ctx.providers.Esri.WorldImagery,
    id_column='GlobalID'):  # Campo para nomear os arquivos
    Path(png_folder).mkdir(parents=True, exist_ok=True)
    gdf_web = gdf.to_crs(epsg=3857)  # Converter para Web Mercator
    for idx, row in gdf_web.iterrows():
        if row.geometry.geom_type != 'Point':
            logging.info(f"⚠️ Entrada {idx} não é um ponto. Pulando...")
            continue
        try:
            fig, ax = plt.subplots(figsize=(10, 10))
            # Coordenadas para zoom
            x, y = row.geometry.x, row.geometry.y
            ax.set_xlim(x - buffer_distance, x + buffer_distance)
            ax.set_ylim(y - buffer_distance, y + buffer_distance)
            pin_icon = plt.imread(r'Arquivos\pin.png')
            imagebox = OffsetImage(pin_icon, zoom=0.1)
            ab = AnnotationBbox(imagebox, (x, y), frameon=False)
            ax.add_artist(ab),
            ctx.add_basemap(ax, source=basemap_source, zoom=18) # Adicionar basemap
            # Obter coordenadas WGS84 (lat/lon)
            point_wgs84 = gpd.GeoSeries([row.geometry], crs='EPSG:3857').to_crs('EPSG:4326').geometry[0]
            lon, lat = point_wgs84.x, point_wgs84.y
            # Legenda com coordenadas
            texto_legenda = f'Lat: {lat:.6f}°\nLon: {lon:.6f}°'
            ax.text(
                0.05, 0.95,
                texto_legenda,
                transform=ax.transAxes,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='black', boxstyle='round'),
                fontsize=12,
                verticalalignment='top'
            )
            # Nome do arquivo usando o ID (ex: GlobalID)
            file_id = row[id_column] if id_column in gdf.columns else idx
            output_path = os.path.join(png_folder, f"ponto_{file_id}.png")
            plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0)
            plt.close()
        except Exception as e:
            logging.error(f"🔥 Erro ao plotar ponto: {str(e)}")
    logging.info(f"✅ {len(gdf_web)} mapas salvos em '{png_folder}'")

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_email(recipients, subject, body, attachments=None, cc=None, bcc=None):
    """Envia e-mails com suporte a anexos e HTML."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = ", ".join(recipients) if isinstance(recipients, list) else recipients
    msg['Cc'] = ", ".join(cc) if cc else ""
    msg['Subject'] = subject
    # Validar todos os e-mails primeiro
    invalid_emails = []
    all_recipients = []
    # Coletar todos os destinatários
    for email_list in [recipients, cc, bcc]:
        if email_list:
            emails = email_list if isinstance(email_list, list) else [email_list]
            for email in emails:
                if not is_valid_email(email):
                    invalid_emails.append(email)
                else:
                    all_recipients.append(email)
    # Se houver e-mails inválidos, enviar alerta
    if invalid_emails:
        logging.error(f"⚠️ E-mails inválidos detectados: {invalid_emails}")
        # Criar mensagem de alerta separada
        alert_msg = MIMEMultipart()
        alert_msg['From'] = EMAIL_USER
        alert_msg['To'] = DEFAULT_RECIPIENT
        alert_msg['Subject'] = "E-mail do fiscal inválido"
        alert_body = f"""
        Alerta do Sistema:
        Os seguintes e-mails são inválidos e não receberam o laudo:
        {', '.join(invalid_emails)}
        Detalhes do laudo não enviado:
        Assunto: {subject}
        """
        alert_msg.attach(MIMEText(alert_body, 'plain'))
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.sendmail(EMAIL_USER, DEFAULT_RECIPIENT, alert_msg.as_string())
            logging.info(f"⚠️ Alerta enviado para: {DEFAULT_RECIPIENT}")
        except Exception as e:
            logging.error(f"❌ Falha ao enviar alerta: {e}")
            return False
    # (Apenas se houver destinatários válidos)
    if not all_recipients:
        logging.error("❌ Nenhum destinatário válido encontrado.")
        return False
    # Corpo do e-mail (HTML/plain)
    msg.attach(MIMEText(body, 'html' if '<html>' in body else 'plain'))
    # Anexos
    if attachments:
        for file_path in attachments:
            try:
                with open(file_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(part)
            except FileNotFoundError:
                logging.error(f"Anexo não encontrado: {file_path}")
                return False
    # Envio
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, all_recipients, msg.as_string())
        logging.info(f"✅ E-mail enviado para: {all_recipients}")
        return True
    except smtplib.SMTPException as e:
        logging.error(f"❌ Erro SMTP: {e}")
        return False
    except Exception as e:
        logging.error(f"🔥 Erro inesperado: {e}")
        return False

if __name__ == "__main__":
    setup_logging()
    conectar_portal()
    baixar_csvs()
    baixar_imagens()
    gdf = criar_gdf()
    plot_each_point(gdf, r"Output\Pontos", buffer_distance=100, id_column='GlobalID')