'''
Versão mais atualizada do script, gera por nome
'''

import geopandas as gpd
import matplotlib.pyplot as plt
import os
import contextily as ctx
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image, ImageDraw
from reportlab.platypus import PageBreak
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from PIL import Image as PILImage
from reportlab.lib.enums import TA_CENTER

# Pasta principal de onde sairá os outputs:
workstation = r"layout"
# Pastas dos prints de antes e depois:
pasta_antes = r"PRINTS_41_FINAL\ANTES"
pasta_durante = r"PRINTS_41_FINAL\DURANTE"
pasta_depois = r"PRINTS_41_FINAL\DEPOIS"
# Pasta onde se encontram os CSVs e o XLSX
csv_folder = r"C:\csv"
tabela_CAR = f"{csv_folder}\\tabela_42_inseridototal_CAR_intersect_join.csv"
tabela_cpf = f"{csv_folder}\\Planilha_ONVC_ECR_CAR.xlsx"
referencias = f"{csv_folder}\\referencias.csv"
input_folder = r"C:\gpl_cicatrizes" # Camada dos alertas
# Imagens do papel timbrado:
imagem_cbc1 = r"C:\cbc1.jpg"
imagem_cbc2 = r"C:\cbc2.jpg"

# Criando as pastas de saída
output_folder = f"{workstation}\\Layouts_output"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
png_folder = f"{output_folder}\\mapas"
if not os.path.exists(png_folder):
    os.makedirs(png_folder)
layout_folder = f"{output_folder}\\layouts"
if not os.path.exists(layout_folder):
    os.makedirs(layout_folder)

# Identificações dos arquivos
cicatriz_prefix = 'tabela_42_inseridototal_CAR_datas'
inter_prefix = 'tabela_Intersecao_'
id_column = 'idtxt'
cntd = 1

# Função para gerar o mapa em PNG para cada `idtxt`
def plot_map_for_idtxt_satellite(
    gdf, idtxt, png_folder, buffer_distance=19, color='none', opacity=0.9,
    basemap_source="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
):
    gdf_filtered = gdf[gdf[id_column] == idtxt]
    if gdf_filtered.empty:
        print(f"ID {idtxt} não encontrado no shapefile.")
        return
    
    # Reprojetar para Web Mercator
    gdf_filtered = gdf_filtered.to_crs(epsg=3857)
    bounds = gdf_filtered.total_bounds
    xmin, ymin, xmax, ymax = bounds
    margin = buffer_distance
    xlim = (xmin - margin, xmax + margin)
    ylim = (ymin - margin, ymax + margin)
    
    # Criar figura e eixo
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf_filtered.plot(ax=ax, color=color, edgecolor='red', alpha=opacity, linewidth=3.5)
    
    # Adicionar basemap de imagens de satélite
    ctx.add_basemap(ax, source=basemap_source, zoom=18)
    
    # Definir os limites
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    
    # Salvar o mapa
    output_path = os.path.join(png_folder, f"{idtxt}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    #print(f"Mapa salvo em: {output_path}")

# Função para gerar o PDF para cada `idtxt`
styles = getSampleStyleSheet()

# Função para gerar o PDF para cada `idtxt`
def create_pdf_for_idtxt(idtxt, cicatriz_data, inter_data, png_folder, cntd, link_poligono, nome_car, nome_pessoa):
    pdf_file = os.path.join(layout_folder, f"{idtxt}_{nome_car}_{nome_pessoa}.pdf")
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, leftMargin=0.4 * inch, rightMargin=0.4 * inch,
                            topMargin=0.2 * inch, bottomMargin=0.3 * inch)

    # Formatando as colunas para mostrar apenas dois dígitos após a vírgula
    if 'Área(m2)' in cicatriz_data.columns:
        cicatriz_data['Área(m2)'] = cicatriz_data['Área(m2)'].fillna(0).astype(str).str.replace(',', '.').apply(lambda x: f"{float(x):.2f}")
    if 'Centróide X' in cicatriz_data.columns:
        cicatriz_data['Centróide X'] = cicatriz_data['Centróide X'].fillna(0).astype(str).str.replace(',', '.').apply(lambda x: f"{float(x):.4f}")
    if 'Centróide Y' in cicatriz_data.columns:
        cicatriz_data['Centróide Y'] = cicatriz_data['Centróide Y'].fillna(0).astype(str).str.replace(',', '.').apply(lambda x: f"{float(x):.4f}")
    if 'Área(ha)' in cicatriz_data.columns:
        cicatriz_data['Área(ha)'] = cicatriz_data['Área(ha)'].fillna(0).astype(str).str.replace(',', '.').apply(lambda x: f"{float(x):.4f}")
        
    # Para inter_data
    if 'Porcentagem' in inter_data.columns:
        inter_data['Porcentagem'] = inter_data['Porcentagem'].fillna('0').astype(str).str.replace(',', '.').apply(lambda x: f"{float(x):.2f}")
    if 'Área da interseção(m2)' in inter_data.columns:
        inter_data['Área da interseção(m2)'] = inter_data['Área da interseção(m2)'].fillna('0').astype(str).str.replace(',', '.').apply(lambda x: f"{float(x):.2f}")    
    if 'area_ha' in inter_data.columns:
        inter_data['area_ha'] = inter_data['area_ha'].fillna('0').astype(str).str.replace(',', '.').apply(lambda x: f"{float(x):.2f}")
    if 'area_m2' in inter_data.columns:
        inter_data['area_m2'] = inter_data['area_m2'].fillna('0').astype(str).str.replace(',', '.').apply(lambda x: f"{float(x):.2f}")

    def clean_data(data):
        data = data.dropna(how='all')  # Remove linhas totalmente vazias
        data = data.dropna(axis=1, how='all')  # Remove colunas totalmente vazias
        data = data.fillna('-')  # Preenche valores NaN restantes com marcador
        data = data[~(data == '-').all(axis=1)]  # Remove linhas onde todos os valores são '-'
        return data

    def add_table_with_split(data, title, lado, qtd_colunas, remover_id):
        # Se o DataFrame principal estiver vazio, pula a adição da tabela
        data = clean_data(data)
        if data.empty:
            print(f"Nenhum dado válido encontrado para {title}.")
            return

        elements.append(Paragraph(title, styles['Heading2']))

        if remover_id == 1:
            data = data.drop(columns=['idtxt'])

        # Obter lista de colunas e calcular o número de tabelas necessárias
        columns = data.columns.tolist()
        num_tables = (len(columns) + qtd_colunas - 1) // qtd_colunas

        # Loop para dividir a tabela em sub-tabelas
        for i in range(num_tables):
            start_col = i * qtd_colunas
            end_col = min(start_col + qtd_colunas, len(columns))
            sub_data = data.iloc[:, start_col:end_col]

            # Limpa a sub-tabela após a divisão
            sub_data = clean_data(sub_data)

            # Se a sub-tabela estiver vazia após a limpeza, pula
            if sub_data.empty:
                continue

            # Formatação dos dados com 2 casas decimais para valores numéricos
            table_data = [sub_data.columns.tolist()] + sub_data.values.tolist()

            # Criação e estilo da sub-tabela
            sub_table = Table(table_data, colWidths=(A4[0] - 0.8 * inch) / len(sub_data.columns))
            sub_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Fundo cinza para os títulos
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),    # Negrito nos títulos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),        # Fonte normal para o restante
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),       # Linhas da grade
            ('FONTSIZE', (0, 0), (-1, -1), 8),                 # Tamanho da fonte
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),             # Alinhamento central
        ]))
            elements.append(sub_table)
            elements.append(Spacer(1, 0.2 * inch))

    def add_tables_by_columns(data, title_prefix, lado, qtd_colunas, remover_id):

        campos_a_manter = ["vegetacao2", "NOME", 'NomeOficia', 'Tipo_16', 'Tipo_6', 'classe', 'nome_uce', 'ZA UCE',
            "rotulo", "cod_imovel", "Tipo_8", "Tipo_7", "Tipo_5", "Tipo_3", "Tipo1", "nm_municip", 'Classe',
            "zona", "grau", "Tipo_6", "Tipo_3", "Tipo_4", "Nome", "rotulo", 'Código CAR', 'Altitude',
            'Declividade', 'Lagos e lagoas', 'Mangue', 'Nascente', 'Restinga', 'Rio', 'Topo de Morro',
            'Uso restrito', 'FMP', 'Vegetação', 'Nome município', 'Nome UCE', 'Nome UCF', 'Nome UCM', 'Zona UCE']

        # Dicionário dos titulos de acordo com o nome das colunas
        titulos_colunas = {
            'Altitude': 'APP de Altitude',
            'Declividade': 'APP de Declividade',
            'Lagos e lagoas': 'APP de Lagos e Lagoas',
            'Mangue': 'APP de Mangue',
            'Nascente': 'APP de Nascente',
            'Restinga': 'APP de Restinga',
            'Rio': 'APP de Rio',
            'Topo de Morro': 'APP de Topo de Morro',
            'Uso restrito': 'Áreas de Uso Restrito (declividade 25° a 45°)',
            'FMP': 'Faixa Marginal de Proteção',
            'Código CAR': 'Imóvel CAR',
            'Classe': 'Mapeamento de Uso e Cobertura (2018)',
            'Vegetação': 'Mapeamento da Vegetação (2024)',
            'Nome município': 'Municípios',
            'Nome UCE': 'Unidades de Conservação Estaduais',
            'Nome UCF': 'Unidades de Conservação Federais',
            'Nome UCM': 'Unidades de Conservação Municipais',
            'ZA UCE': 'Zona de Amortecimento (Ucs Estaduais)',
            'Zona UCE': 'Zoneamento (Ucs Estaduais)'
        }

        # Iterar sobre cada coluna em `manter_colunas`
        for coluna in campos_a_manter:
            if coluna in data.columns:
                # Processar cada valor único na coluna
                for valor in data[coluna].unique():
                    sub_data = data[data[coluna] == valor].copy()
                    sub_data = clean_data(sub_data)

                    # Pular conjuntos de dados vazios
                    if sub_data.empty:
                        #print(f"Nenhum dado válido encontrado para {coluna}: {valor}.")
                        continue

                    if remover_id == 1 and 'idtxt' in sub_data.columns:
                        sub_data = sub_data.drop(columns=['idtxt'])

                    # Continua com o processamento normal das demais colunas
                    columns = sub_data.columns.tolist()
                    num_tables = (len(columns) + qtd_colunas - 1) // qtd_colunas

                    # Loop para dividir a tabela em sub-tabelas
                    for i in range(num_tables):
                        start_col = i * qtd_colunas
                        end_col = min(start_col + qtd_colunas, len(columns))
                        sub_data = sub_data.iloc[:, start_col:end_col]

                        # Limpa a sub-tabela após a divisão
                        sub_data = clean_data(sub_data)

                        # Se a sub-tabela estiver vazia após a limpeza, pula
                        if sub_data.empty:
                            continue

                        # Formatação dos dados com 2 casas decimais para valores numéricos
                        table_data = [sub_data.columns.tolist()] + sub_data.values.tolist()

                        # Criação e estilo da sub-tabela
                        sub_table = Table(table_data, colWidths=(A4[0] - 0.8 * inch) / len(sub_data.columns))
                        sub_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Fundo cinza para os títulos
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),    # Negrito nos títulos
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),        # Fonte normal para o restante
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),       # Linhas da grade
                        ('FONTSIZE', (0, 0), (-1, -1), 8),                 # Tamanho da fonte
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),             # Alinhamento central
                    ]))
                        elements.append(Paragraph(f"{title_prefix} - {titulos_colunas[coluna]}: ", styles['Heading2']))
                        elements.append(sub_table)
                        elements.append(Spacer(1, 0.2 * inch))

    elements = []

    if os.path.exists(imagem_cbc1):
        img_cbc1 = RLImage(imagem_cbc1)
        img_cbc1.drawHeight = 1.5 * inch
        img_cbc1.drawWidth = 3 * inch
        elements.append(img_cbc1)

    # Verifica se as imagens existem e as adiciona ao PDF lado a lado
    logo_inea_caminho = r"C:\inea_logo.png"
    logo_olho_no_verde_caminho = r"C:\dados\Logo_Olho_no_Verde.png"

    # Lista para armazenar as imagens
    imagens = []

    if os.path.exists(logo_inea_caminho):
        img_inea = RLImage(logo_inea_caminho)
        img_inea.drawHeight = 1.5 * inch
        img_inea.drawWidth = 3.5 * inch
        imagens.append(img_inea)
    else:
        print(f"Logo INEA não encontrada para ID: {idtxt}")

    if os.path.exists(logo_olho_no_verde_caminho):
        img_olho_no_verde = RLImage(logo_olho_no_verde_caminho)
        img_olho_no_verde.drawHeight = 1.5 * inch
        img_olho_no_verde.drawWidth = 3.5 * inch
        imagens.append(img_olho_no_verde)
    else:
        print(f"Logo Olho no Verde não encontrada para ID: {idtxt}")

    if imagens: # Se ambas as imagens existirem, adiciona-as lado a lado centralizadas
        tabela_imagens = Table([[img_inea, img_olho_no_verde]], colWidths=[3.5 * inch, 3.5 * inch], hAlign='CENTER')
        elements.append(tabela_imagens)
        elements.append(Spacer(0.2, 0.2 * inch))

    elements.append(Paragraph(f"LAUDO DE EMBARGO CAUTELAR REMOTO", styles['Title']))
    elements.append(Spacer(1, 0.12 * inch))

    subtitulo = "Documento automatizado gerado a partir do sistema de detecção de alertas"

    # Cria um estilo com alinhamento centralizado
    centered_style = styles['Normal'].clone('CenteredStyle')  # Clona o estilo existente
    centered_style.alignment = TA_CENTER  # Define o alinhamento como centralizado

    # Adiciona o subtítulo com o estilo centralizado
    elements.append(Paragraph(subtitulo, centered_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Adiciona tabela de cicatriz com divisão, se necessário
    add_table_with_split(cicatriz_data, "Tabela de informações do alerta", 'CENTER', 3, 0) # LEFT

    # tabela CAR:
    CAR_table = pd.read_csv(tabela_CAR, delimiter=';')
    CAR_table = CAR_table[['cod_imovel', 'area_inter', 'proc']]
    cpf_table = pd.read_excel(tabela_cpf, dtype={"Imovel Pessoa → Cod Cpf Cnpj": str})
    cpf_table = cpf_table.rename(columns={'Imovel Pessoa → Cod Cpf Cnpj': 'Cpf-Cnpj', 'ID Queimada': 'idtxt', 'Cod Imovel': 'cod_imovel', 
                                          'Imovel Pessoa → Nom Completo': "nome", 'Endereco Imovel → Des Email': 'E-mail'})
    cpf_table = cpf_table[['idtxt', 'cod_imovel', 'nome', 'Cpf-Cnpj', 'E-mail']]
    CAR_DF = pd.merge(cpf_table, CAR_table, on= 'cod_imovel')

    try:
        if not CAR_DF.empty:
            # Filtra o DataFrame para pegar apenas a linha onde o idtxt é igual ao definido
            linha_selecionada = CAR_DF[(CAR_DF['idtxt'] == idtxt) & (CAR_DF['nome'] == nome_pessoa)].head(1)
            linha_selecionada = clean_data(linha_selecionada)
            if not linha_selecionada.empty:
                elements.append(Paragraph("Tabela de informações do responsável:", styles['Heading2']))
                elements.append(Spacer(1, 0.2 * inch))
                # Converte a linha filtrada para uma lista de listas (como uma tabela)
                table_data = [linha_selecionada.columns.tolist()] + linha_selecionada.values.tolist()
                colunas = table_data[0]  # Primeira linha contém os nomes das colunas
                # Renomeia as colunas
                colunas_renomeadas = {'cod_imovel': 'Código CAR', 'area_inter': 'Área da interseção(m2)', 
                                    'proc': 'Porcentagem', 'nome': 'Nome', 'email': 'E-mail'}
                # Aplica os novos nomes às colunas
                colunas = [colunas_renomeadas.get(col, col) for col in colunas]
                table_data[0] = colunas
                # Remove a coluna 'idtxt' da lista de dados da tabela
                idtxt_index = table_data[0].index('idtxt')
                for row in table_data:
                    del row[idtxt_index]
                # Encontra os índices das colunas para arredondamento
                porcentagem_index = table_data[0].index('Porcentagem') if 'Porcentagem' in table_data[0] else None
                area_intersecao_index = table_data[0].index('Área da interseção(m2)') if 'Área da interseção(m2)' in table_data[0] else None
                # Itera sobre as linhas (ignorando o cabeçalho) e arredonda os valores
                for row in table_data[1:]:  # Ignora o cabeçalho
                    if porcentagem_index is not None and row[porcentagem_index]:
                        try:
                            row[porcentagem_index] = f"{float(str(row[porcentagem_index]).replace(',', '.')):.2f}"
                        except ValueError:
                            row[porcentagem_index] = "0.00"  # Valor padrão se não for possível converter
                    if area_intersecao_index is not None and row[area_intersecao_index]:
                        try:
                            row[area_intersecao_index] = f"{float(str(row[area_intersecao_index]).replace(',', '.')):.2f}"
                        except ValueError:
                            row[area_intersecao_index] = "0.00"  # Valor padrão se não for possível converter
                # Divide a tabela em sub-tabelas de 3 colunas
                columns_per_table = 3  # Número de colunas por sub-tabela
                num_tables = (len(table_data[0]) + columns_per_table - 1) // columns_per_table  # Número de sub-tabelas
                for i in range(num_tables):
                    start_col = i * columns_per_table
                    end_col = min(start_col + columns_per_table, len(table_data[0]))
                    # Cria uma sub-tabela com 3 colunas
                    sub_table_data = [table_data[0][start_col:end_col]] + [row[start_col:end_col] for row in table_data[1:]]
                    
                    # Cria a sub-tabela
                    sub_table = Table(sub_table_data, colWidths=(A4[0] - 0.8 * inch) / columns_per_table)
                    sub_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Fundo cinza para os títulos
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),    # Negrito nos títulos
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),        # Fonte normal para o restante
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),       # Linhas da grade
                        ('FONTSIZE', (0, 0), (-1, -1), 8),                 # Tamanho da fonte
                        ('FONTSIZE', (0, 1), (0, -1), 7),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),             # Alinhamento central
                    ]))
                    elements.append(sub_table)
                    elements.append(Spacer(1, 0.2 * inch))
            else:
                print(f"Combinação não encontrada para a linha do {idtxt} {nome_pessoa}")
        else:
            print("Tabela CAR")
    except Exception as e:
        print(f"Erro ao processar o CAR/ Tabela de informações do responsável: {str(e)}")

    introducao = """O Programa Olho no Verde realiza o monitoramento por intermédio de disponibilização sistemática e contínua de 
        produtos espectrais, fruto de uma constelação de satélites, que geram imagens de alta resolução espacial. 
        O método de aquisição das informações se dá por meio do processamento automático e semiautomático utilizando técnicas de 
        sensoriamento remoto e aprendizagem de máquina. Detectada a mudança na vegetação, a partir da comparação de imagens de diferentes datas, 
        é materializado o polígono resultante do processamento. """
    
    link_imagem = f"Link para imagens de antes e depois: {link_imagemAD}"
    link_poligono = f"Link para o polígono georeferenciado: {link_poligono}"

    # Adiciona a string 'link_imagem' como um parágrafo ao documento
    elements.append(Paragraph(link_imagem, styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Adiciona a string 'link_poligono' como um parágrafo ao documento
    elements.append(Paragraph(link_poligono, styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # Adiciona a string 'introducao' como um parágrafo ao documento
    elements.append(Paragraph(introducao, styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # Adiciona um salto de página
    elements.append(PageBreak())

    # Começa a parte do layout
    elements.append(Paragraph("Do Local e da Avaliação", styles['Title']))
    png_file = f"{idtxt}.png"
    png_path = os.path.join(png_folder, png_file)

    # Verifica se a imagem existe e adiciona ao PDF - MAPA
    if os.path.exists(png_path):
        img = RLImage(png_path)  
        img.drawHeight = 4 * inch
        img.drawWidth = 4 * inch
        elements.append(img)
        elements.append(Spacer(0.8, 0.2 * inch))
    else:
        print(f"Imagem PNG não encontrada para ID: {idtxt}")

    # Encontrar o arquivo correspondente
    antes_file = next((f for f in os.listdir(pasta_antes) if f.endswith(f"{idtxt}.jpg")), None)
    antes_path = os.path.join(pasta_antes, antes_file) if antes_file else None
    if antes_path and os.path.exists(antes_path):
        None
    else:
        antes_file = next((f for f in os.listdir(pasta_antes) if f.endswith(f"{idtxt}.jpeg")), None)
        antes_path = os.path.join(pasta_antes, antes_file) if antes_file else None

    depois_file = next((f for f in os.listdir(pasta_depois) if f.endswith(f"{idtxt}.jpg")), None)
    depois_path = os.path.join(pasta_depois, depois_file) if depois_file else None
    if depois_path and os.path.exists(depois_path):
        None
    else:
        depois_file = next((f for f in os.listdir(pasta_depois) if f.endswith(f"{idtxt}.jpeg")), None)
        depois_path = os.path.join(pasta_depois, depois_file) if depois_file else None

    imagens_AD = []
    
    # Verifica se a imagem existe e adiciona ao PDF - Antes
    if antes_path and os.path.exists(antes_path):
        img_A = RLImage(antes_path)  
        img_A.drawHeight = 3.5 * inch
        img_A.drawWidth = 3.5 * inch
        imagens_AD.append(img_A)

    # Verifica se a imagem existe e adiciona ao PDF - Depois
    if depois_path and os.path.exists(depois_path):
        img_D = RLImage(depois_path)  
        img_D.drawHeight = 3.5 * inch
        img_D.drawWidth = 3.5 * inch
        imagens_AD.append(img_D)

    # Se ambas as imagens existirem, adiciona-as lado a lado centralizadas
    if imagens_AD:
        elements.append(Paragraph(f"Antes e depois:", styles['Title']))
        elements.append(Spacer(1, 0.2 * inch))
        tabela_imagens_AD = Table([[img_A,' ', img_D]], colWidths=[3.5 * inch, 0.2 * inch, 3.5 * inch], hAlign='CENTER')
        elements.append(tabela_imagens_AD)
        elements.append(Spacer(0.5, 0.2 * inch))
    else:
        print(f"Imagens AD não encontradas para ID: {idtxt}")

    elements.append(PageBreak())

    # Adiciona o título após o salto de página
    elements.append(Paragraph("Interseções do alerta com outras camadas:", styles['Title']))
    elements.append(Spacer(1, 0.2 * inch))

    add_tables_by_columns(inter_data, " ", 'CENTER', 3, 1)

    # Adiciona textos após as tabelas
    conclusao = """A supressão de vegetação detectada no Alerta em epígrafe configura queimada e/ou incêndio florestal 
        realizado em desconformidade com a Lei Federal n° 12.651/2012, impondo a lavratura de Embargo Remoto Cautelar, 
        nos termos do art. 11 §3º, c/c art. 29 c/c art. 2º, inciso VII, ambos da Lei Estadual nº 3.467/2000 
        e Decreto Estadual nº 48.691 de 14 de setembro de 2023."""
    
    observacao = """Observações: Todas as informações estão disponíveis em acesso aberto para consulta a processos 
        no Portal do SEI (https://portalsei.rj.gov.br/), sob número do processo constante do Auto de Embargo Cautelar Remoto."""
    
    obs_2 = "OBS2: As camadas aqui listadas que não foram apresentadas no ítem de interseções do alerta com outras camadas não apresentam interseção espacial com o alerta em questão."
    
    # Adiciona a string 'conclusao' como um parágrafo ao documento
    elements.append(Paragraph(conclusao, styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Adiciona a string 'observacao' como um parágrafo ao documento
    elements.append(Paragraph(observacao, styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # Adiciona a tabela de referencia
    referencia_DF = pd.read_csv(referencias, delimiter=';', encoding='latin1')

    # Verifica se o DataFrame não está vazio
    if not referencia_DF.empty:
        # Converte o DataFrame para uma lista de listas (como uma tabela)
        table_data = [referencia_DF.columns.tolist()] + referencia_DF.values.tolist()

        # Divide a tabela em sub-tabelas de 3 colunas
        columns_per_table = 2  # Número de colunas por sub-tabela
        num_tables = (len(table_data[0]) + columns_per_table - 1) // columns_per_table  # Número de sub-tabelas
        elements.append(Paragraph("Tabela de referências:", styles['Heading2']))
        elements.append(Spacer(1, 0.2 * inch))
        for i in range(num_tables):
            start_col = i * columns_per_table
            end_col = min(start_col + columns_per_table, len(table_data[0]))

            # Cria uma sub-tabela com 2 colunas
            sub_table_data = [table_data[0][start_col:end_col]] + [row[start_col:end_col] for row in table_data[1:]]
            sub_table = Table(sub_table_data, colWidths=(A4[0] - 0.8 * inch) / columns_per_table)
            sub_table.setStyle(TableStyle([
                # Estilo dos títulos (primeira linha)
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Fundo cinza para os títulos
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),    # Negrito nos títulos
                ('FONTSIZE', (0, 0), (-1, 0), 8),                  # Tamanho maior para os títulos
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),              # Alinhamento dos títulos
                # Estilo para as colunas específicas (não inclui a linha de título)
                ('FONTSIZE', (0, 1), (0, -1), 8),                 # Coluna 1 (primeira) - maior
                ('FONTSIZE', (2, 1), (2, -1), 8),                 # Coluna 3 - maior
                ('FONTSIZE', (1, 1), (1, -1), 5),                  # Coluna 2 - menor
                ('FONTSIZE', (3, 1), (3, -1), 5),                  # Coluna 4 - menor
                # Linhas da grade e alinhamento geral
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),       # Linhas da grade
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),             # Alinhamento dos dados
            ]))
            elements.append(sub_table)
            elements.append(Spacer(1, 0.2 * inch))

    # Adiciona a obs2
    elements.append(Paragraph(obs_2, styles['Normal']))
    elements.append(Spacer(1, 0.5 * inch))

    if os.path.exists(imagem_cbc2):
        img_cbc2 = RLImage(imagem_cbc2)
        img_cbc2.drawHeight = 2 * inch
        img_cbc2.drawWidth = 5 * inch
        elements.append(img_cbc2)

    # Cria o PDF após a adição dos elementos
    doc.build(elements)
    print(f"{cntd} PDFs gerados, ID: {idtxt}, CAR {nome_car}, Nome {nome_pessoa}")

# Carrega o arquivo `cicatriz`
cicatriz_file = next((f for f in os.listdir(csv_folder) if f.startswith(cicatriz_prefix) and f.endswith('.csv')), None)
if cicatriz_file:
    cicatriz_path = os.path.join(csv_folder, cicatriz_file)
    cicatriz_df = pd.read_csv(cicatriz_path, sep=';', on_bad_lines='skip')
else:
    raise FileNotFoundError("Arquivo de cicatriz não encontrado.")

# Carrega todos os arquivos `inter` que começam com `tabela_Intersecao`
inter_files = [f for f in os.listdir(csv_folder) if f.startswith(inter_prefix) and f.endswith('.csv')]
inter_dfs = [pd.read_csv(os.path.join(csv_folder, f), sep=';', on_bad_lines='skip') for f in inter_files]

# Processamento de interseção
valid_inter_dfs = []
for df in inter_dfs:
    if id_column in df.columns:
        valid_inter_dfs.append(df)
    else:
        print(f"Coluna {id_column} não encontrada em um dos arquivos de interseção.")

manter_colunas =['idtxt', 'apps', 'area_inter', 'porc', 'classe', 'Cicatriz_9', 'municipio', 'CLASSE',
                 "zona", "grau", "Tipo_4", "Nome", "vegetacao2", "NOME", 'NomeOficia', 'Tipo_16', 'Tipo_6',
                 "rotulo", "Tipo_8", "Tipo_7", "Tipo_5", "tipo_5", "Tipo_3", "Tipo1", "nm_municip", 'nome_uce']

lista_ids = ['ONVC202409740', 'ONVC2024092227', 'ONVC2024092215', 'ONVC2024091968', 'ONVC2024091593', 'ONVC202405048']

campos_interesse_car = ['idtxt', 'cod_imovel', 'nome'] #, 'area_inter', 'proc', 'nome', 'cpf', 'email'

CAR_table = pd.read_csv(tabela_CAR, delimiter=';', dtype={"cpf": str})
CAR_DF = CAR_table[campos_interesse_car]

# Processar a tabela de nomes
nome_table = pd.read_excel(tabela_cpf, dtype={"Imovel Pessoa → Cod Cpf Cnpj": str})
nome_table = nome_table.rename(columns={
    'Imovel Pessoa → Cod Cpf Cnpj': 'Cpf-Cnpj',
    'ID Queimada': 'idtxt',
    'Imovel Pessoa → Nom Completo': 'Nome_completo',
    'Cod Imovel': 'cod_imovel'
})[['idtxt', 'cod_imovel', 'Cpf-Cnpj', 'Nome_completo']]

for filename in os.listdir(input_folder):
    if filename.endswith(".shp"):
        shapefile_path = os.path.join(input_folder, filename)
        gdf = gpd.read_file(shapefile_path)
        
        # Iterar sobre cada combinação única
        for _, row in nome_table.iterrows():
            current_idtxt = row['idtxt']
            current_car = row['cod_imovel']
            current_nome = row['Nome_completo']
            cpf = row['Cpf-Cnpj']
            nome_pessoa = current_nome
            nome_car = current_car
            idtxt = current_idtxt
            
            try:
                plot_map_for_idtxt_satellite(gdf, current_idtxt, png_folder) # Gerar mapa para o idtxt (usando geometria do shapefile)
            except Exception as e:
                print(f"Erro ao gerar a imagem no ID {current_idtxt}: {str(e)}")
                continue
            # Filtrando os dados de cicatriz e interseção
            cicatriz_filtered = cicatriz_df[cicatriz_df[id_column] == idtxt]
            link_poligono = cicatriz_filtered['link_kml'].astype(str).tolist()  # Armazena os links como uma lista de strings
            link_imagemAD = cicatriz_filtered['ant_dep'].astype(str).tolist()
            cic_colunas = ['idtxt', 'area_ha', 'area_m2', 'data_refer', 'data_ocorr', 'centro_x', 'centro_y']
            cicatriz_filtered = cicatriz_filtered.drop(columns=[column for column in cicatriz_filtered.columns if column not in cic_colunas], axis=1)
            columns = ['idtxt'] + [col for col in cicatriz_filtered.columns if col != 'idtxt'] # Reordenando para idtxt ficar em primeiro
            cicatriz_filtered = cicatriz_filtered[columns]
            cicatriz_filtered = cicatriz_filtered.rename(columns={'idtxt': 'ID da Queimada', 'area_ha': 'Área(ha)', 'area_m2': 'Área(m2)', 'data_refer': 'Data antes',
                                                                'data_ocorr': 'Data depois', 'centro_x': 'Centróide X', 'centro_y': 'Centróide Y'})
            # PARA OS DADOS DO INTERSECT:
            if valid_inter_dfs:
                inter_filtered = pd.concat(
                    [df[df[id_column] == idtxt] for df in valid_inter_dfs], 
                    ignore_index=True
                )
                try:
                    inter_filtered = inter_filtered.drop(columns=[column for column in inter_filtered.columns if column not in manter_colunas], axis=1)
                    inter_filtered = inter_filtered.rename(columns={'area_inter': 'Área da interseção(m2)', 'porc': 'Porcentagem', 'classe': 'Classe', 'apps': 'APPs', 
                                                                    'municipio': 'Municipio', 'vegetacao2': 'Vegetação', 'NOME': 'Restinga', 
                                                                    'NomeOficia': 'Nome UCM', 'Tipo_16': 'Nome UCF', 'nome_uce': 'Nome UCE', 'rotulo': 'ZA UCE',
                                                                    'Tipo_8': 'FMP', 'Tipo_7': 'Mangue', 'tipo_5': 'Rio', 'Tipo_3': 'Lagos e lagoas', 'Tipo1': 'Altitude', 
                                                                    'nm_municip': 'Nome município', 'zona': 'Zona UCE', 'grau': 'Uso restrito', 'Tipo_6': 'Topo de Morro', 
                                                                    'Tipo_4': 'Nascente', 'Nome': 'Declividade', 'label': 'label UCE'})
                except Exception as e:
                    print(f"Ocorreu um erro: {e}")
            else:
                inter_filtered = pd.DataFrame()
                inter_filtered = inter_filtered.drop(columns=[column for column in inter_filtered.columns if column not in manter_colunas], axis=1)
                inter_filtered = inter_filtered.rename(columns={'area_inter': 'Área da interseção(m2)', 'porc': 'Porcentagem', 'classe': 'Classe', 'apps': 'APPs', 
                                                                    'municipio': 'Municipio', 'vegetacao2': 'Vegetação', 'NOME': 'Restinga', 
                                                                    'NomeOficia': 'Nome UCM', 'Tipo_16': 'Nome UCF', 'nome_uce': 'Nome UCE', 'rotulo': 'ZA UCE',
                                                                    'Tipo_8': 'FMP', 'Tipo_7': 'Mangue', 'tipo_5': 'Rio', 'Tipo_3': 'Lagos e lagoas', 'Tipo1': 'Altitude', 
                                                                    'nm_municip': 'Nome município', 'zona': 'Zona UCE', 'grau': 'Uso restrito', 'Tipo_6': 'Topo de Morro', 
                                                                    'Tipo_4': 'Nascente', 'Nome': 'Declividade', 'label': 'label UCE'})
            
            try: # Geração do PDF para o idtxt e car atual e por nome
                print(f"Gerando layout para: ID {current_idtxt}, CAR {current_car}, Nome {current_nome}")
                create_pdf_for_idtxt(idtxt, cicatriz_filtered, inter_filtered, png_folder, cntd, link_poligono, nome_car, nome_pessoa)
            except Exception as e:
                print(f"Ocorreu um erro ao gerar PDF para {idtxt}: {e}")
            finally:
                cntd += 1

def delete_files(directory, condition):
    # Apaga todas as imagens geradas para economizar memória
    files = os.listdir(directory)
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and not file.startswith(condition):
            os.remove(file_path)
    print(f"Arquivos excluídos: {directory}")
delete_files(png_folder, "APAGAR")

print("Fim do processamento")