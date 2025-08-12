import arcpy
import os

gdb_directory = r"Arquivos.gdb"  # TROCAR
arcpy.env.workspace = gdb_directory
gdb_layers = arcpy.ListFeatureClasses()

Saida = r"Output"
os.makedirs(Saida, exist_ok=True)

def coletar_dados():
    """
    Extrai as tabelas de atributos e converte para CSV
    atribute table -> CSV"""
    for layer in gdb_layers:
        print(f"Processando: {layer}")
        if not arcpy.Exists(layer):
            print(f"A camada {layer} não existe ou não é suportada.")
            continue

        # Nome de saída
        layer_name = os.path.splitext(os.path.basename(layer))[0]
        nome_saida_csv = os.path.join(Saida, f"tabela_{layer_name}.csv")

        try:
            # Exportar a tabela de atributos para CSV
            arcpy.TableToTable_conversion(layer, Saida, f"tabela_{layer_name}.csv")
            print(f"Dados extraídos para: {nome_saida_csv}")

        except Exception as e:
            print(f"Erro ao processar {layer}: {str(e)}")

def delete_files(directory, condition):
    files = os.listdir(directory)
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and not file.endswith(condition):
            os.remove(file_path)
            print(f"Arquivo excluído: {file_path}")

coletar_dados()
delete_files(Saida, ".csv")
print("fim do processamento")