
import pickle
import numpy as np
import face_recognition
import cv2


class Reconhecedor:

    def __init__(self, caminho_pkl="dados_biometricos.pkl"):
        """Carrega os embeddings (encodings) e os dados de acesso do arquivo PKL."""
        self.dados = self._carregar_dados(caminho_pkl)


        self.TOLERANCIA = 0.6

        self.face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def _carregar_dados(self, caminho):
        """Método interno para carregar o arquivo pickle."""
        try:
            with open(caminho, 'rb') as f:
                dados = pickle.load(f)
                print(f"✅ Dados biométricos carregados. Total de encodings: {len(dados['encodings'])}")
                return dados
        except FileNotFoundError:
            print(f"❌ Erro: Arquivo de dados biométricos não encontrado em {caminho}")
            return {"encodings": np.array([]), "ids": [], "niveis_acesso": []}

    def autenticar(self, frame_camera: np.ndarray, nivel_desejado: int, id_esperado: str):
        """
        Tenta autenticar um rosto no frame.
        Retorna: ID_reconhecida (str), Nivel_max_acesso (int), Status (str), bbox (tuple)
        """

        # 1. Detecção da Face
        cinza = cv2.cvtColor(frame_camera, cv2.COLOR_BGR2GRAY)
        # Tenta encontrar a face na imagem
        faces = self.face_detector.detectMultiScale(cinza, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        bbox = None

        if len(faces) == 0:
            return "Nenhum", 0, "Nenhuma Face Detectada", None


        (x, y, w, h) = faces[0]
        bbox = (x, y, w, h)


        face_rect = [(y, x + w, y + h, x)]

        # 2. Extração e Encoding
        try:
            encoding_camera = face_recognition.face_encodings(frame_camera, face_rect)
        except Exception:
            return "Erro", 0, "Erro ao gerar encoding da face", bbox

        if not encoding_camera:
            return "Desconhecido", 0, "Face Válida não encontrada", bbox

        # 3. Comparação Biometrica


        comparacoes = face_recognition.compare_faces(
            self.dados["encodings"],
            encoding_camera[0],
            self.TOLERANCIA
        )


        face_distances = face_recognition.face_distance(self.dados["encodings"], encoding_camera[0])
        best_match_index = np.argmin(face_distances)

        id_reconhecida = "Desconhecido"
        nivel_max_acesso = 0

        if comparacoes[best_match_index]:
            id_match = self.dados["ids"][best_match_index]
            niveis_match = self.dados["niveis_acesso"][best_match_index]

            # 1. Verifica se a pessoa reconhecida é a pessoa que CLICOU no botão
            if id_match.lower() == id_esperado.lower():

                id_reconhecida = id_match
                nivel_max_acesso = max(niveis_match)

                # 2. Verifica se o nível de acesso da pessoa é suficiente para a TELA atual
                if nivel_desejado in niveis_match:
                    return id_reconhecida, nivel_max_acesso, "ACESSO CONCEDIDO", bbox
                else:
                    return id_reconhecida, nivel_max_acesso, "NEGADO: Nível Insuficiente", bbox

        # Se saiu do loop sem conceder acesso (Usuário Incorreto ou Não Reconhecido)
        return "Desconhecido", 0, "ACESSO NEGADO: Usuário Incorreto", bbox