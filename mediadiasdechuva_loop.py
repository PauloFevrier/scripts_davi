# Faz a média mensal de dias de chuva e plota um gráfico com a média
import os
import pandas as pd
import matplotlib.pyplot as plt

# Caminhos de entrada e saída
dados = r"dados_chuvaANA"
output_folder = r"Outputs\media_diaschuva"

# Função para calcular a média mensal agregada (2000-2020)
def calcular_media_mensal_serie(file, df):
    # Convertendo a coluna 'Data' para datetime
    df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
    
    # Filtrando o período de 2000 a 2020
    df = df[(df['Data'].dt.year >= 2000) & (df['Data'].dt.year <= 2020)].copy()
    
    # Adicionando a coluna Mês
    df['Mes'] = df['Data'].dt.month
    
    # Calculando a média mensal agregada
    media_mensal = (
        df.groupby('Mes')['NumDiasDeChuva']
        .mean()
        .reset_index()
        .rename(columns={'NumDiasDeChuva': 'Media'})
    )
    
    # Mapeando números dos meses para nomes (opcional, para o gráfico e CSV)
    meses = {
        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
    }
    media_mensal['Mes'] = media_mensal['Mes'].map(meses)
    #print(media_mensal.head())
    
    return media_mensal

# Função para criar o gráfico e salvar
def salvar_csv_e_grafico(media_mensal, estacao, output_folder):
    # Criando a pasta para a estação
    pasta_estacao = os.path.join(output_folder, estacao)
    if not os.path.exists(pasta_estacao):
        os.makedirs(pasta_estacao)
        print(f"Pasta '{pasta_estacao}' criada.")

    # Salvando o CSV
    csv_path = os.path.join(pasta_estacao, f"{estacao}_media_mensal.csv")
    media_mensal.to_csv(csv_path, index=False)
    print(f"CSV salvo em {csv_path}.")

    # Criando o gráfico de barras
    plt.figure(figsize=(12, 6))
    plt.bar(media_mensal['Mes'], media_mensal['Media'], color='blue', alpha=0.7)
    plt.title(f"Média Mensal de Dias de Chuva (2000-2020) - {estacao}")
    plt.xlabel("Mês")
    plt.ylabel("Média de Dias de Chuva")
    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()

    # Salvando o gráfico
    grafico_path = os.path.join(pasta_estacao, f"{estacao}_media_mensal.png")
    plt.savefig(grafico_path)
    plt.close()
    print(f"Gráfico salvo em {grafico_path}.")

# Lendo os arquivos de dados
files = os.listdir(dados)
acumulados = {
    file: pd.read_csv(
        os.path.join(dados, file), encoding='iso-8859-1', sep=';', skiprows=14, on_bad_lines='skip'
    )
    for file in files
}

# Processando cada arquivo
for file, df in acumulados.items():
    estacao = file.replace("_Chuvas.csv", "")  # Nome da estação com base no nome do arquivo
    try:
        # Calculando a média mensal agregada
        media_mensal = calcular_media_mensal_serie(file, df)
        
        # Salvando CSV e gráfico para a estação
        salvar_csv_e_grafico(media_mensal, estacao, output_folder)
    except Exception as e:
        print(f"Erro ao processar o arquivo {file}: {e}")