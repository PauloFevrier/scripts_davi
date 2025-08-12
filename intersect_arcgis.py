import arcpy

# Função para realizar o processo completo
def processor_intersects(cicatrizes, gdb_layers, campos_a_manter):
    
    # 1. Interseção entre a camada de cicatrizes e cada camada do gdb
    for layer in gdb_layers:
        nome_saida_intersecao = f"Intersecao_{cicatrizes}_{layer}"
        
        # Realizar a interseção
        arcpy.Intersect_analysis([cicatrizes, layer], nome_saida_intersecao, join_attributes="ALL")
        print(f"Interseção concluída: {nome_saida_intersecao}")

        # 2. Delete Fields - Remover campos que não são necessários
        campos_da_camada = [f.name for f in arcpy.ListFields(nome_saida_intersecao)]
        campos_para_remover = [campo for campo in campos_da_camada if campo not in campos_a_manter]
        
        # Remover os campos desnecessários
        arcpy.DeleteField_management(nome_saida_intersecao, campos_para_remover)
        print(f"Campos removidos de {nome_saida_intersecao}: {campos_para_remover}")

        # 3. Adicionar os campos 'area_inter' e 'porc'
        arcpy.AddField_management(nome_saida_intersecao, "area_inter", "DOUBLE")
        arcpy.AddField_management(nome_saida_intersecao, "porc", "DOUBLE")
        print(f"Campos 'area_inter' e 'porc' adicionados a {nome_saida_intersecao}")

        # 4. Calcular a área geodésica da interseção
        arcpy.CalculateField_management(nome_saida_intersecao, "area_inter", "!shape.geodesicArea@meters!", "PYTHON3")
        print(f"Área geodésica calculada para {nome_saida_intersecao}")

        # 5. Calcular a porcentagem para todas as camadas de uma vez
    for layer in gdb_layers:
        if layer.isFeatureLayer:
            fields = [f.name for f in arcpy.ListFields(layer)]
            if 'area_inter' in fields and 'area_m2' in fields:
                with arcpy.da.UpdateCursor(layer, ['area_inter', 'area_m2', 'porc']) as cursor:
                    for row in cursor:
                        area_inter = row[0]
                        area_m2 = row[1]
                        if area_m2 != 0:
                            row[2] = (area_inter / area_m2) * 100
                        else:
                            row[2] = 0
                        cursor.updateRow(row)
                print(f"Porcentagem calculada para {nome_saida_intersecao}")


# Parâmetros
cicatrizes = "C:\CICATRIZES_04_10.CSV"

# Lista de camadas de polígonos no GDB
gdb_layers = [
    "C:\CAMADAS_INTERSECTS",
    "C:\GDB_INTERSECT_QUEIMADAS_24.gdb"]
    # Adicionar mais camadas conforme necessário

# Campos que devem ser mantidos após a interseção (inserir os nomes dos campos corretos)
campos_a_manter = [
    "area_m2",
    # Adicionar mais conforme necessário
]

# Chamar a função
processor_intersects(cicatrizes, gdb_layers, campos_a_manter)