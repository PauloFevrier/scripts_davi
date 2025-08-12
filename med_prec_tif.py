"""Código para calcular as médias de precipitação para arquivos TIF, 
alguns ajustes podem ser necesarios, como o diretório e o nome dos arquivos TIF"""

import arcpy
import os

# Define o diretório de trabalho
workspace = r"G:\BASE_ESTATICA\4_acima_100k\MODELAGEM_SE"
arcpy.env.workspace = workspace
arcpy.CheckOutExtension("Spatial")

# Lista de arquivos TIFF
meses = [f"MTZ_PREC_{str(i).zfill(2)}.TIF" for i in range(1, 13)]

# Inicializa uma lista para armazenar os rasters
rasters = []

# Percorre os arquivos TIFF e adiciona os rasters à lista
for tif_file in meses:
    caminho_tif = os.path.join(workspace, tif_file)
    rasters.append(arcpy.sa.Raster(caminho_tif))

# Calcula a média mensal
medias_mensais = []
for i, raster in enumerate(rasters):
    media_mensal = arcpy.sa.CellStatistics([raster], statistics_type="MEAN")
    media_mensal.save(os.path.join(workspace, f"Media_Mensal_{i + 1}.tif"))
    medias_mensais.append(media_mensal)

# Calcula a média anual
media_anual = arcpy.sa.CellStatistics(rasters, statistics_type="MEAN")
media_anual.save(os.path.join(workspace, "Media_Anual.tif"))

# Imprime as médias mensais
print("Médias Mensais de Precipitação:")
for i, media in enumerate(medias_mensais):
    # Usando arcpy para calcular a média do raster e convertendo para numpy para pegar o valor
    media_valor = arcpy.management.GetRasterProperties(media, "MEAN")  # Obtém a média do raster
    print(f"Mês {i + 1}: {media_valor}")

# Imprime a média anual
media_anual_valor = arcpy.management.GetRasterProperties(media_anual, "MEAN")
print("\nMédia Anual de Precipitação:")
print(media_anual_valor)