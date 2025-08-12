'''
Detecta novas entradas no portal, gera os relatórios e envia por e-mail a cada 30 minutos
'''

import logging
from logging.handlers import RotatingFileHandler
import json
import os
import time
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from funcoes_script import *
from gerar_layout import create_pdf_for_idtxt
from reportlab.lib.styles import getSampleStyleSheet
import configparser

config_path = os.path.join('config', "config.ini") # Caminho do arquivo de configuração
config = configparser.ConfigParser() # Ler o arquivo de configuração
config.read(config_path)

setup_logging()

def carregar_estado():
    """Carrega o último ObjectID e os últimos 5 GlobalIDs."""
    caminho_config = os.path.join("config", "ultimo_oid.json")
    try:
        with open(caminho_config, "r") as f:
            dados = json.load(f)
            return dados["ultimo_oid"], dados["ultimos_globalids"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return 0, []

def salvar_estado(oid, globalids):
    """Salva o novo estado no arquivo."""
    caminho_config = os.path.join("config", "ultimo_oid.json")
    os.makedirs("config", exist_ok=True)
    with open(caminho_config, "w") as f:
        json.dump({"ultimo_oid": oid, "ultimos_globalids": globalids}, f)

def obter_globalids_validos(camada, globalids_esperados):
    """Retorna os GlobalIDs que ainda existem na camada e seus OIDs."""
    if not globalids_esperados:
        return []
    query = "GlobalID IN ('{}')".format("','".join(globalids_esperados))
    features = camada.query(where=query).features
    return [{"GlobalID": f.attributes["globalid"], "OID": f.attributes["objectid"]} for f in features]

def main():
    conectar_portal()
    camada_url = config["PORTAL"]["URL_CAMADA"]
    camada = FeatureLayer(camada_url)
    ultimo_oid, ultimos_globalids = carregar_estado()
    globalids_validos = obter_globalids_validos(camada, ultimos_globalids) # Verifica GlobalIDs válidos
    if len(globalids_validos) < len(ultimos_globalids):
        if globalids_validos:
            # Encontra o MAIOR OID entre os válidos e define o novo início como OID + 1
            maior_oid_valido = max(g["OID"] for g in globalids_validos)
            novo_oid_inicio = maior_oid_valido + 1
            logging.info(f"⚠️ {len(ultimos_globalids) - len(globalids_validos)} registros foram excluídos. Reprocessando a partir do OID {novo_oid_inicio}.")
            ultimo_oid = novo_oid_inicio
        else: # ... (caso todos sejam excluídos)
            logging.info("⚠️ Todos os registros anteriores foram excluídos! Reprocessando desde o início.") # Nenhum GlobalID válido: força reprocessamento completo
            ultimo_oid = 0
    # Consultar novas features
    query = f"OBJECTID > {ultimo_oid}"
    novas_features = camada.query(where=query).features
    if not novas_features:
        logging.info("✅ Nenhuma nova entrada encontrada.")
        return
    try:
        globalids_processar = [f.attributes["globalid"] for f in novas_features]
        conectar_portal()
        baixar_csvs()
        baixar_imagens()
        gdf = criar_gdf()
        plot_each_point(gdf, r"Output\Pontos", buffer_distance=100, id_column='GlobalID')

        # CONFIGURAÇÕES PARA O LAYOUT
        logo_olho_no_verde_caminho = r"Arquivos\Logo_Olho_no_Verde_Branca.png" # Logos do INEA:
        csv_folder = r"CSVs" # Pasta onde se encontram os CSVs
        layout_folder = r"Output\layouts"
        os.makedirs(layout_folder, exist_ok=True) # Criando as pastas de saída
        camada_DF = pd.read_excel(f"{csv_folder}\\camada.xlsx", header=0, dtype=object, keep_default_na=False, na_values=[""], na_filter=True)
        notificacao_DF = pd.read_excel(f"{csv_folder}\\notificacao.xlsx")
        auto_const_DF = pd.read_excel(f"{csv_folder}\\auto_const.xlsx")
        medida_cautelar_DF = pd.read_excel(f"{csv_folder}\\medida_cautelar.xlsx")
        repeat_rl_fotografico_DF = pd.read_excel(f"{csv_folder}\\repeat_rl_fotografico.xlsx")
        assinaturas_DF = pd.read_excel(f"{csv_folder}\\assinaturas.xlsx")
        links_DF = pd.read_csv(f"{csv_folder}\\tabela_alertas_em_uso.csv", sep=';', on_bad_lines='skip')
        cntd = 0
        styles = getSampleStyleSheet()

        for id in camada_DF['globalid']:
            if id in globalids_processar:
                try:
                    camada_linha = camada_DF[camada_DF['globalid'] == id]
                    nome_rz = camada_linha['nome_rzsocial'].astype(str).tolist()
                    mapa = camada_linha['globalid'].iloc[0]
                    idtxt = camada_linha['id_alerta'].iloc[0] #.astype(str).tolist()
                    linha_link = links_DF[links_DF['id'].astype(str) == str(idtxt)]
                    link_poligono = linha_link['link_kml'].astype(str).tolist()
                    link_imagemAD = linha_link['ant_dep'].astype(str).tolist()
                    notificacao_linha = notificacao_DF[notificacao_DF['globalid'] == id]
                    auto_const_linha = auto_const_DF[auto_const_DF['globalid'] == id]
                    medida_cautelar_linha = medida_cautelar_DF[medida_cautelar_DF['globalid'] == id]
                    repeat_rl_fotografico_linha = repeat_rl_fotografico_DF[repeat_rl_fotografico_DF['parentrowid'] == id]
                    repeat_rl_fotografico_linha = repeat_rl_fotografico_linha[['descr_foto', 'nota04']]
                    id_assinatura = camada_linha['id_fiscalizacao'].iloc[0]
                    imagem_assinatura =  camada_linha['globalid'].iloc[0]
                    assinaturas_linha = assinaturas_DF[assinaturas_DF['id_fiscalizacao_assinaturas'].astype(str) == str(id_assinatura)]
                    if not assinaturas_linha.empty:
                        email_destinatario = assinaturas_linha['email_fisc01'].iloc[0]
                    else:
                        email_destinatario = config["EMAIL"]["DEFAULT_RECIPIENT"]
                    pdf_laudo = os.path.join(layout_folder, f"{nome_rz}.pdf")
                except Exception as e:
                    logging.error(f"❌ Ocorreu um erro durante o tratamento dos dados: {id} {e}")
                try:
                    cntd += 1
                    create_pdf_for_idtxt(id, camada_linha, linha_link, repeat_rl_fotografico_linha, auto_const_linha, assinaturas_linha, notificacao_linha, medida_cautelar_linha, camada_DF, cntd)
                except Exception as e:
                    logging.error(f"❌ Ocorreu um erro ao gerar o pdf para: {id} {e}")
                try:
                    send_email(
                    recipients=[email_destinatario],
                    subject="Relatório Survey",
                    body="Prezados,\n\nSeguem os laudos em anexo.\n\nAtenciosamente,\nEquipe Técnica\n",
                    attachments=[pdf_laudo]
                )
                except Exception as e:
                    logging.error(f"❌ Ocorreu um erro ao enviar o e-mail para: {id} {e}")
        
        # Atualizar estado com os últimos 5 GlobalIDs
        novos_globalids = [f.attributes["globalid"] for f in novas_features[-5:]]  # Pega os últimos 5
        novo_ultimo_oid = max(f.attributes["objectid"] for f in novas_features)
        salvar_estado(novo_ultimo_oid, novos_globalids)
        logging.info(f"✅ Processadas {len(novas_features)} entradas. Último OID: {novo_ultimo_oid}")
    except Exception as e:
        logging.error(f"🔥 Erro: {str(e)} (Nenhum dado foi salvo)")

while True:
    main()
    time.sleep(1800) 