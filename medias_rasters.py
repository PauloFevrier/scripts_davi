# Calcula média de evapotranspiração e precipitação usando rasters
import arcpy
import pandas as pd
import os

# Define o caminho para o arquivo TIFF
tif_file = "MTZ_PREC_01.TIF"

# Defina o diretório de trabalho
workspace = r"Precipitacao"
arcpy.env.workspace = workspace

# Cria a tabela de atributos do raster
arcpy.management.BuildRasterAttributeTable(tif_file, "Overwrite")

# Exporta a tabela de atributos para um arquivo .dbf
dbf_file = os.path.join(workspace, "MTZ_PREC_01.dbf")
arcpy.conversion.TableToTable(tif_file, workspace, "MTZ_PREC_01")  # Salva como DBF

# Verifique se o DBF foi criado
if arcpy.Exists(dbf_file):
    # Carrega o DBF em um DataFrame
    df = pd.DataFrame(arcpy.da.TableToNumPyArray(dbf_file, "*"))  # Lê o DBF em um DataFrame

    # Salva o DataFrame como CSV
    csv_file = os.path.join(workspace, "MTZ_PREC_01.csv")
    df.to_csv(csv_file, index=False)

    # Mostra o DataFrame
    print(df)
else:
    print("O arquivo DBF não foi criado.")

# Calculating the annual average precipitation

annual_average = precipitacao.mean(axis=1)
annual_average.head()

# Calculating the monthly average precipitation

monthly_average = precipitacao.mean(axis=0)
monthly_average.head()

# Calculating the daily average precipitation

daily_average = precipitacao.mean(axis=1).mean(axis=0)
daily_average

# Calculating the seasonal average precipitation

def calculate_seasonal_average(precipitation_data, season):
    seasons = {
        "inverno": [12, 1, 2],
        "primavera": [3, 4, 5],
        "verao": [6, 7, 8],
        "outono": [9, 10, 11]
    }

#showing the results

print("Annual average precipitation:")
print(annual_average.mean())

print("\nMonthly average precipitation:")
print(monthly_average.mean())

# Define o diretório de trabalho
workspace = r"Evapotranspiracao"
arcpy.env.workspace = workspace
arcpy.CheckOutExtension("Spatial")

# Lista de anos
anos = range(2000, 2023)

# Inicializa uma lista para armazenar os rasters
rasters = {i: [] for i in range(1, 13)}  # Chave: mês, Valor: lista de rasters

# Percorre os arquivos TIFF para cada ano
for ano in anos:
    for mes in range(1, 13):
        tif_file = f"ep_raster{ano}.tif"
        caminho_tif = os.path.join(workspace, tif_file)
        
        # Verifica se o arquivo existe
        if arcpy.Exists(caminho_tif):
            # Adiciona a banda correspondente ao mês
            raster = arcpy.sa.Raster(caminho_tif + f"/{mes}")
            rasters[mes].append(raster)

# Calcula a média mensal
medias_mensais = {}
for mes, raster_list in rasters.items():
    if raster_list:  # Verifica se a lista não está vazia
        media_mensal = arcpy.sa.CellStatistics(raster_list, statistics_type="MEAN")
        media_mensal.save(os.path.join(workspace, f"Media_Mensal_Mes_{mes}.tif"))
        medias_mensais[mes] = media_mensal

# Calcula a média anual
media_anual = arcpy.sa.CellStatistics([raster for raster_list in rasters.values() for raster in raster_list], statistics_type="MEAN")
media_anual.save(os.path.join(workspace, "Media_Anual_Evapotranspiracao.tif"))

# Imprime as médias mensais
print("Médias Mensais de Evapotranspiração:")
for mes, media in medias_mensais.items():
    media_valor = arcpy.management.GetRasterProperties(media, "MEAN")
    print(f"Mês {mes}: {media_valor}")

# Imprime a média anual
media_anual_valor = arcpy.management.GetRasterProperties(media_anual, "MEAN")
print("\nMédia Anual de Evapotranspiração:")
print(media_anual_valor)