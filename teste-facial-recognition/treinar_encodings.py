import face_recognition  # Necessário para gerar os embeddings
import pickle
import os
import numpy as np
import time

# --- 1. CONFIGURAÇÃO DE DIRETÓRIOS E ACESSO ---

# Pasta onde estão os recortes padronizados (Saída do extract-faces.py)
# VERIFIQUE E AJUSTE ESTE CAMINHO SE NECESSÁRIO!
DIR_FACES = "C:\\Users\\Camila\\PycharmProjects\\Autenticacao-Biometrica\\teste-facial-recognition\\rostos\\faces\\"

# Arquivo final onde os dados de biometria e acesso serão salvos
FILE_OUTPUT = "dados_biometricos.pkl"

# Dicionário que define o nível de acesso (Com Camila no Nível 3)
NIVEIS_DE_ACESSO = {
    "camila": [1, 2, 3],  # Camila: Nível 1, 2 e 3
    "vanessa": [1, 2],  # Vanessa: Nível 1 e 2
    "quezia": [1],  # Quezia: Nível 1
    "sabrina": [1],  # Sabrina: Nível 1
    "dafny": [1]  # Dafny: Nível 1
}

# Inicializa as listas
conhecidos_encodings = []
conhecidos_ids = []
conhecidos_niveis = []


# --- 2. FUNÇÃO DE PROCESSAMENTO ---

def treinar_e_salvar_encodings():
    start_time = time.time()
    print("Iniciando Embedding e Treinamento Biométrico...")

    # Percorre as subpastas (que são os IDs dos usuários)
    for nome_usuario in os.listdir(DIR_FACES):
        path_usuario = os.path.join(DIR_FACES, nome_usuario)

        # Verifica se é um diretório e se é um usuário autorizado
        if os.path.isdir(path_usuario) and nome_usuario.lower() in NIVEIS_DE_ACESSO:

            niveis_acesso = NIVEIS_DE_ACESSO[nome_usuario.lower()]
            print(f"-> Processando: {nome_usuario} (Níveis: {niveis_acesso})")

            # Percorre todas as imagens padronizadas do usuário
            for filename in os.listdir(path_usuario):
                path_imagem = os.path.join(path_usuario, filename)

                # Garante que é um arquivo de imagem (p. ex., jpg, jpeg, png)
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    try:
                        # Carrega a imagem e gera o embedding (vetor de 128 dimensões)
                        imagem = face_recognition.load_image_file(path_imagem)
                        encoding = face_recognition.face_encodings(imagem)

                        if len(encoding) > 0:
                            # Armazena os dados
                            conhecidos_encodings.append(encoding[0])
                            conhecidos_ids.append(nome_usuario)
                            conhecidos_niveis.append(niveis_acesso)

                    except Exception as e:
                        print(f"Erro ao processar {filename}: {e}")

    # --- 3. SALVAMENTO DOS DADOS ---

    end_time = time.time()
    tempo_total = end_time - start_time

    if len(conhecidos_encodings) > 0:
        # Organiza todos os dados em um dicionário
        dados_finais = {
            "encodings": np.array(conhecidos_encodings),
            "ids": conhecidos_ids,
            "niveis_acesso": conhecidos_niveis
        }

        # Salva o dicionário usando pickle (serialização)
        with open(FILE_OUTPUT, 'wb') as f:
            pickle.dump(dados_finais, f)

        print("-" * 50)
        print(f"✅ Treinamento concluído em {tempo_total:.2f} segundos.")
        print(f"Total de {len(conhecidos_ids)} embeddings salvos em '{FILE_OUTPUT}'.")
        print("PRÓXIMO PASSO: Integração PyQt em tempo real!")
        print("-" * 50)
    else:
        print("❌ Nenhuma face válida foi encontrada. Verifique os caminhos e as imagens em rostos/faces/.")


if __name__ == '__main__':
    treinar_e_salvar_encodings()