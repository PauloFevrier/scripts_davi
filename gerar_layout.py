import geopandas as gpd
import matplotlib.pyplot as plt
import os
import contextily as ctx
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image, ImageDraw
from reportlab.platypus import PageBreak
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from PIL import Image as PILImage
from reportlab.lib.enums import TA_CENTER
import logging
from logging.handlers import RotatingFileHandler
from funcoes_script import setup_logging, send_email
import configparser
setup_logging()

config_path = os.path.join('config', "config.ini") # Caminho do arquivo de configuração
config = configparser.ConfigParser() # Ler o arquivo de configuração
config.read(config_path)

def create_pdf_for_idtxt(id, camada_linha, linha_link, repeat_rl_fotografico_linha, auto_const_linha, assinaturas_linha, notificacao_linha, medida_cautelar_linha, camada_DF, cntd):
    pdf_file = os.path.join(layout_folder, f"{nome_rz}.pdf")
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, leftMargin=0.4 * inch, rightMargin=0.4 * inch,
                            topMargin=0.2 * inch, bottomMargin=0.3 * inch)
    def clean_data(data):
        data = data.dropna(how='all')  # Remove linhas totalmente vazias
        data = data.dropna(axis=1, how='all')  # Remove colunas totalmente vazias
        data = data.fillna('-')  # Preenche valores NaN restantes com marcador
        data = data[~(data == '-').all(axis=1)]  # Remove linhas onde todos os valores são '-'
        return data
    def add_table_with_split(data, title, qtd_colunas, remover_id):
        data = pd.DataFrame(data)
        try:
            data = clean_data(data)
        except Exception as e:
            None
        if data.empty:
            return
        elements.append(Paragraph(title, styles['Heading2']))
        if remover_id == 1:
            data = data.drop(columns=['globalid'])
        columns = data.columns.tolist()
        num_tables = (len(columns) + qtd_colunas - 1) // qtd_colunas
        for i in range(num_tables):
            start_col = i * qtd_colunas
            end_col = min(start_col + qtd_colunas, len(columns))
            sub_data = data.iloc[:, start_col:end_col]
            sub_data = clean_data(sub_data)
            if sub_data.empty:
                continue
            table_data = [sub_data.columns.tolist()] + sub_data.values.tolist()
            sub_table = Table(table_data, colWidths=(A4[0] - 0.8 * inch) / len(sub_data.columns))
            sub_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#adcb56')),  # Cor do Fundo para os títulos
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),    # Negrito nos títulos
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),        # Fonte normal para o restante
            ('GRID', (0, 0), (-1, -1), 0.5, colors.green),       # Linhas da grade
            ('FONTSIZE', (0, 0), (-1, -1), 8),                 # Tamanho da fonte
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),             # Alinhamento central
        ]))
            elements.append(sub_table)
            elements.append(Spacer(1, 0.2 * inch))
    
    # Renomeando as colunas dos DataFrames:
    notificacao_linha = notificacao_linha.rename(columns={'disp_legais_not': 'Artigos infrigidos da Lei 3.467/2000', 'enquadramento_not': 'Enquadramento', 'enquadramento1_not': 'Artigos infrigidos da Lei 3.467/2000', 
                                                'enquadramento2_not': 'Artigos da Lei 3.467/2000 relacionados à temas gerais', 'enquadramento3_not': 'Outros artigos da Lei 3.467/2000', 
                                                'lei_not': 'O município utiliza legislação estadual 3.467/2000 ou alguma outra legislação?', 
                                                'n_notificacao': 'Nº/código da Notificação', 'outra_lei_not': 'Outros'})
    auto_const_linha = auto_const_linha.rename(columns={'n_auto_const': 'N°/código do Auto de Constatação / Infração', 'disp_legais_const': 'Artigos infrigidos da Lei 3.467/2000', 'enquadramento_const': 'Enquadramento', 
                                        'lei_const': 'O município utiliza legislação estadual 3.467/2000 ou alguma outra legislação?', 'enquadramento2_const': 'Artigos da Lei 3.467/2000 relacionados à temas gerais', 
                                        'outra_lei_const': 'Instância, número, ano e artigos infringidos da legislação utilizada', 'enquadramento1_const': 'Artigos infrigidos da Lei 3.467/2000', 'enquadramento3_const': 'Outros artigos da Lei 3.467/2000'})
    medida_cautelar_linha = medida_cautelar_linha.rename(columns={'num_cautelar': 'N°/código da Medida Cautelar', 'disp_legais_mc': 'Artigos infrigidos da Lei 3.467/2000', 'enquadramento_mc': 'Enquadramento', 
                                                    'lei_mc': 'O município utiliza legislação estadual 3.467/2000 ou alguma outra legislação?', 
                                                    'enquadramento2_mc': 'Artigos da Lei 3.467/2000 relacionados à temas gerais', 'outra_lei_mc': 'Tipo, instância, número, ano e artigos', 
                                                    'enquadramento1_mc': 'Artigos infrigidos da Lei 3.467/2000', 'enquadramento3_mc': 'Outros artigos da Lei 3.467/2000'})
    nomes_das_colunas= {'obs': 'Observação', 'telefone': 'Telefone', 'sig_risc_saude_pop': 'Risco a saúde da população', 'descritivo': 'Descritivo da inspeção', 'id_fiscalizacao': 'ID Funcional',
                        'id': 'Id da queimada', 'detalhe': 'Justificativa da impossibilidade de vistoriar', 'bairro': 'Bairro', 'fonte': 'Fonte', 'municipio_imovel': 'Município do imóvel',
                        'conclusao': 'Conclusão', 'tipo_apoio': 'Tipo de apoio', 'necess_apoio': 'Necessário apoio', 'status': 'Status do alerta', 'confirmacao_uc': 'Confirma interseção com UC?',
                        'atenuante04': 'Colaboração com os agentes', 'atenuante03': 'Comunicação prévia do infrator', 'atenuante02': 'Reparação espontânea', 'atenuante01': 'Baixo grau de escolaridade', 
                        'atenuante06': 'Implementação de  planos de gestão ambiental por parte do infrator', 'cep': 'CEP', 'data_fisc': 'Data da fiscalização', 'num_rv': 'N° do RV',
                        'atenuante05': 'Promoção de educação ambiental por parte do infrator', 'objetivo': 'Objetivo', 'fisico_juridico': 'Pessoa física ou jurídica', 'rel_motiv': 'Relação de motivos', 
                        'ato_admnist': 'Tipo de Ato Adm.', 'car_sim_nao': 'Há CAR', 'responsavel': 'Nome do responsável', 'placa': 'Colocada placa do Olho No Verde', 
                        'agravante': 'Ausência de comunicação', 'quant_auto': 'Quantidade de autos', 'permanencia': 'Prazo de permanência', 'distribuicao_dano': 'Distributividade do dano', 
                        'outra_infracao': 'Houve outra infração associada?',  'agenda2': 'Classificação', 'nota01': 'Agravantes', 'agravante13': 'Mediante fraude', 'id_alerta': 'ID do alerta',
                        'agravante12': 'Método cruel para captura animal', 'id_car': 'Número de registro do CAR', 'agravante15': 'Incentivo fiscal', 'area_ha': 'Área em hectares', 'agravante14': 'Abuso de licença', 
                        'agravante17': 'Facilitado por funcionário público', 'agenda': 'Classificação (categoria)', 'agravante16': 'Atingiu espécies ameaçadas', 'agravante18': 'Obra que desreipeite a licença', 
                        'nota03': 'Atenuantes', 'nota02': 'Agente cometido infração', 'quant_notificacao': 'Quantidade de notificações', 'pras': 'Número/código da notificação de recuperação ambiental',
                        'quant_mc': 'Quantidade de medidas cautelares', 'agravante09': 'À noite', 'teste': 'Teste', 'telefone_resp': 'Telefone (responsável)', 'confirmacao_app': 'Confirma interseção com APP?',
                        'nome_rzsocial': 'Nome ou razão social', 'data': 'Data da fiscalização', 'agravante02': 'Coagiu outrem',  'agravante01': 'Para obter vantagem', 'muni': 'Selecione o município',
                        'agravante04': 'Danos a propriedade alheia', 'num_asv': 'Número da autorização', 'agravante03': 'Expondo ao perigo', 'agravante06': 'Atingiu área urbana', 
                        'agravante05': 'Atingiu área de preservação',  'agravante08': 'Domingo ou feriado', 'agravante07':'Período de defesa a fauna', 'email_resp': 'E-mail do responsável',
                        'autorizacao': 'Apresentou autorização para supressão', 'sup_irreg': 'Atestada supressão irregular', 'agravante11': 'Espaço protegido', 'chave_acesso': 'Chave de acesso fornecida',
                        'agravante10': 'Em época de seca ou inundação', 'categ_denu2': 'Categoria da infração', 'endereco_imovel': 'Endereço do imóvel e descrição de acesso', 'cpf_respon': 'CPF do responsável',
                        'atividade': 'Atividade', 'motiv_mc': 'Categorização ambiental do dano',  'nome_operacao': 'Nome da operação', 'telefone_cad_car': 'Telefone', 
                        'sub_cat2': 'Sub. Categoria', 'processo_origem': 'Processo SEI',  'infracao': 'Infração observada', 'relevancia': 'Relevância', 'cpf_cnpj': 'CPF-CNPJ', 
                        'modo_atend': 'Forma de atendimento', 'reversibilidade': 'Reversibilidade', 'area_m2': 'Área em m2',  'data_refer': 'Data de referência', 'email_cad_car': 'Email',
                        'prasn': 'O proprietário foi notificado à aderir à recuperação ambiental do dano', 'emissao_ato': 'Emissão de Ato Adm.', 'municip_imvl': 'Município de localização do imóvel',
                        'categoria_denuncia': 'Categoria da infração', 'endereco': 'Endereço', 'orgao_apoio': 'Instituição de apoio',  'todos_enquadramentos': 'Todos os enquadramentos', 
                        'endereco_corresp': 'Endereço para correspondência', 'data_atual': 'Data atual', 'ente': 'Ente', 'data_rv': 'Data', 'equipe': 'Equipe', 'sub_cat_denuncia': 'Sub. categoria', 'objectid': 'Id',
                        'uc_federal': 'Interseção com UC federal', 'uc_municip': 'Interseção com UC municipal', 'apps': 'Interseção com APPs', 'uc_estadua': 'Interseção com UC estadual'}
    camada_linha = camada_linha.rename(columns=nomes_das_colunas)
    linha_link = linha_link.rename(columns=nomes_das_colunas)
    assinaturas_linha = assinaturas_linha.rename(columns={'email_fisc01': 'Email do responsável', 'cargo_fisc01': 'Cargo', 'lotacao_fisc01': 'Lotação', 'nomes': 'Nomes dos fiscais', 'id_fisc01': 'ID funcional'})
    
    elements = []

    if os.path.exists(logo_olho_no_verde_caminho):
        img_olho_no_verde = RLImage(logo_olho_no_verde_caminho)
        img_olho_no_verde.drawHeight = 1.2 * inch
        img_olho_no_verde.drawWidth = 2.5 * inch
        elements.append(img_olho_no_verde)
        elements.append(Spacer(1, 0.12 * inch))
    else:
        logging.error(f"Logo Olho no Verde não encontrada para ID: {idtxt}")

    elements.append(Paragraph(f"Relatório de Atendimento aos Alertas", styles['Title']))
    elements.append(Spacer(1, 0.12 * inch))

    subtitulo = "Documento automatizado gerado a partir do sistema de detecção de alertas"

    # Cria um estilo com alinhamento centralizado
    centered_style = styles['Normal'].clone('CenteredStyle')  # Clona o estilo existente
    centered_style.alignment = TA_CENTER  # Define o alinhamento como centralizado

    # Adiciona o subtítulo com o estilo centralizado
    elements.append(Paragraph(subtitulo, centered_style))
    elements.append(Spacer(1, 0.2 * inch))

    introducao = """O Programa Olho no Verde realiza o monitoramento por intermédio de disponibilização sistemática e contínua de 
        produtos espectrais, fruto de uma constelação de satélites, que geram imagens de alta resolução espacial. 
        O método de aquisição das informações se dá por meio do processamento automático e semiautomático utilizando técnicas de 
        sensoriamento remoto e aprendizagem de máquina. Detectada a mudança na vegetação, a partir da comparação de imagens de diferentes datas, 
        é materializado o polígono resultante do processamento. """

    # Adiciona a string 'introducao' como um parágrafo ao documento
    elements.append(Paragraph(introducao, styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # ---------- Aqui a tabela do responsável 
    Informacoes_iniciais = camada_linha[['ID do alerta', 'Status do alerta', 'Data da fiscalização', 'Colocada placa do Olho No Verde', 'Justificativa da impossibilidade de vistoriar', 'Processo SEI', 
                                 'N° do RV', 'Forma de atendimento', 'Ente', 'Equipe', 'Nome do responsável', 'ID Funcional', 'Objetivo']] # número RV; Fiscais; id funcional, 'Data de referência'
    add_table_with_split(Informacoes_iniciais, "Informações iniciais da fiscalização", 3, 0)
    informacoes_alerta = linha_link[['Id da queimada', 'Data de referência', 'Área em m2', 'Área em hectares', 'Interseção com APPs', 'Interseção com UC federal', 'Interseção com UC municipal', 'Interseção com UC estadual']]
    add_table_with_split(informacoes_alerta, "Informações do alerta", 2, 0)

    informacoes_CAR = camada_linha[['Número de registro do CAR', 'Nome ou razão social', 'CPF-CNPJ', 'Email', 'Telefone', 'Endereço', 'CEP', 'Bairro', 'Município do imóvel']]
    add_table_with_split(informacoes_CAR, "Dados do CAR", 3, 0) 

    #elements.append(PageBreak()) # Salto de página

    # Adiciona o título após o salto de página
    elements.append(Paragraph("Informações da Fiscalização", styles['Title']))
    elements.append(Spacer(1, 0.2 * inch))

    # imagem do ponto 
    png_ilustrativo = f"Output\\Pontos\\ponto_{mapa}.png"
    if os.path.exists(png_ilustrativo):
        img = RLImage(png_ilustrativo)
        img.drawHeight = 3.5 * inch
        img.drawWidth = 3.5 * inch
        elements.append(img)
        elements.append(Spacer(0.8, 0.2 * inch))
    
    elements.append(Paragraph(f"Link para imagens de antes e depois: {link_imagemAD}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph(f"Link para o polígono georeferenciado: {link_poligono}", styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    informacoes_fiscalizacao = camada_linha[['Processo SEI', 'N° do RV', 'Nome da operação', 'Necessário apoio', 'Tipo de apoio', 'Instituição de apoio', 'Forma de atendimento', 
                                         'Justificativa da impossibilidade de vistoriar', 'Colocada placa do Olho No Verde', 'Apresentou autorização para supressão', 'Número da autorização', 
                                         'Atestada supressão irregular', 'Infração observada', 'Observação', 'Emissão de Ato Adm.', 'Tipo de Ato Adm.', 'Quantidade de autos']]
    add_table_with_split(informacoes_fiscalizacao, " ", 2, 0)

    # TABELA DO SUB CAT
    if not camada_linha['Sub. categoria'].empty and pd.notna(camada_linha['Sub. categoria'].iloc[0]):
        subcategorias_str = camada_linha['Sub. categoria'].iloc[0]  # Pega o valor da primeira linha
        lista_subcat = subcategorias_str.split(',')  # Divide a string em uma lista
        sub_cat_DF = pd.DataFrame(lista_subcat, columns=['Sub. categoria'])
        sub_cat_DF['Categoria da infração'] = camada_linha['Categoria da infração'].iloc[0]
        sub_cat_DF = sub_cat_DF[['Categoria da infração', 'Sub. categoria']]
        add_table_with_split(sub_cat_DF, " ", 2, 0)

    add_table_with_split(notificacao_linha, " ", 2, 0)

    add_table_with_split(auto_const_linha, " ", 2, 0)
    
    add_table_with_split(medida_cautelar_linha, " ", 2, 0)

    dados_do_autuado = camada_linha[['Nome ou razão social', 'CPF-CNPJ', 'Email', 'Telefone', 'Endereço para correspondência', 'Bairro', 'CEP', 'Município do imóvel']]
    add_table_with_split(dados_do_autuado, "Dados do autuado", 3, 0)

    informacoes_responsavel = assinaturas_linha[['Nomes dos fiscais', 'Email do responsável']]
    add_table_with_split(informacoes_responsavel, "Informações do responsável pelo recebimento da autuação", 2, 0)

    recuperação_ambiental = camada_linha[['O proprietário foi notificado à aderir à recuperação ambiental do dano', 'Número/código da notificação de recuperação ambiental']]
    add_table_with_split(recuperação_ambiental, "Recuperação do dano ambiental", 1, 0)
    
    # Adiciona a string 'conclusao' como um parágrafo ao documento
    conclusao = camada_linha['Conclusão'].astype(str).iloc[0]
    if conclusao != 'nan':
        elements.append(Paragraph(f"Conclusão", styles['Title']))
        elements.append(Paragraph(conclusao, styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))

    arquivos_assinatura = [] # Lista para armazenar arquivos de assinatura encontrados

    for arquivo in os.listdir(r"Output/assinaturas"):
        caminho_completo = os.path.join("Output", "assinaturas", arquivo)
        if os.path.isfile(caminho_completo) and arquivo.startswith(f"Assinatura_{imagem_assinatura}_"):
            arquivos_assinatura.append(caminho_completo)
    if arquivos_assinatura:
        elements.append(Paragraph("Assinaturas dos Fiscais", styles['Title']))
        for caminho_assinatura in arquivos_assinatura:
            img = RLImage(caminho_assinatura)
            img.drawHeight = 1.5 * inch
            img.drawWidth = 2.5 * inch
            elements.append(Paragraph("Assinatura do fiscal:", styles['Normal']))
            elements.append(img)
            elements.append(Spacer(0.8, 0.2 * inch))
    #else:
    #    logging.error(f"⚠️  Nenhuma assinatura encontrada para o fiscal: {imagem_assinatura}")

    # Cria o PDF após a adição dos elementos
    doc.build(elements)
    logging.info(f"✅ {cntd} PDFs gerados: {pdf_file}")

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
    cntd += 1
except Exception as e:
    logging.error(f"❌ Ocorreu um erro: {id} {e}")