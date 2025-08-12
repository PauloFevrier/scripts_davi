''' SCRIPT PARA GERAR OS MAPAS DOS PONTOS DO RELATÓRIO SURVEY
requer um arquivo .ini com as variaveis'''
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import os
from pathlib import Path
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pandas as pd
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from acessar_dados import setup_logging, conectar_portal
import logging
import configparser

config_path = os.path.join('config', "config.ini") # Caminho do arquivo de configuração
config = configparser.ConfigParser() # Ler o arquivo de configuração
config.read(config_path)

setup_logging()
conectar_portal()

def criar_gdf():
    service_url = config["PORTAL"]["URL_PONTOS"]
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

gdf = criar_gdf()
plot_each_point(gdf, r"Output\Pontos", buffer_distance=100, id_column='GlobalID')