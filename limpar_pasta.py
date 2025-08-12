import os

def delete_files(directory, condition):
    '''Apaga arquivos em uma pasta de acordo com uma condição, se a condição não existir apaga todos os arquivos
    path, str'''
    files = os.listdir(directory) # Lista todos os arquivos no diretório
    # Iterar sobre cada arquivo e excluir se a condição for atendida
    for file in files:
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and not file.endswith(condition):
            os.remove(file_path)
            print(f"Arquivo excluído: {file_path}")

delete_files(r"C:\CSV", ".csv")
print("Fim do processamento")