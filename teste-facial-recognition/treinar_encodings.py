import face_recognition  # Necessário para gerar os embeddings
import pickle
import os
import numpy as np
import time

# --- 1. CONFIGURAÇÃO DE DIRETÓRIOS E ACESSO ---


DIR_FACES = "C:\\Users\\Camila\\PycharmProjects\\Autenticacao-Biometrica\\teste-facial-recognition\\rostos\\faces\\"

FILE_OUTPUT = "dados_biometricos.pkl"

NIVEIS_DE_ACESSO = {
    "camila": [1, 2, 3],  # Camila: Nível 1, 2 e 3
    "vanessa": [1, 2],  # Vanessa: Nível 1 e 2
    "quezia": [1],  # Quezia: Nível 1
    "sabrina": [1],  # Sabrina: Nível 1
    "dafny": [1]  # Dafny: Nível 1
}

# Inicializa
conhecidos_encodings = []
conhecidos_ids = []
conhecidos_niveis = []


# --- 2.  PROCESSAMENTO ---

def treinar_e_salvar_encodings():
    start_time = time.time()
    print("Iniciando Embedding e Treinamento Biométrico...")


    for nome_usuario in os.listdir(DIR_FACES):
        path_usuario = os.path.join(DIR_FACES, nome_usuario)

        # Verifica se é um diretório e se é um usuário autorizado
        if os.path.isdir(path_usuario) and nome_usuario.lower() in NIVEIS_DE_ACESSO:

            niveis_acesso = NIVEIS_DE_ACESSO[nome_usuario.lower()]
            print(f"-> Processando: {nome_usuario} (Níveis: {niveis_acesso})")


            for filename in os.listdir(path_usuario):
                path_imagem = os.path.join(path_usuario, filename)


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

        dados_finais = {
            "encodings": np.array(conhecidos_encodings),
            "ids": conhecidos_ids,
            "niveis_acesso": conhecidos_niveis
        }


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