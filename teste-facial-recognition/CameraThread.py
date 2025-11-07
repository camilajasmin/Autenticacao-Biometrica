# CameraThread.py

import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, Qt

# Importamos o Reconhecedor que acabamos de criar
from Reconhecedor import Reconhecedor


class CameraThread(QThread):
    # Sinal 1: Envia o frame de vídeo (com o rosto marcado) para exibição na UI
    # O frame é um array NumPy (np.ndarray)
    change_pixmap_signal = pyqtSignal(np.ndarray)

    # Sinal 2: Envia o resultado do reconhecimento para a UI
    # Contém: ID (str), Nível Máximo (int), Status (str)
    resultado_reconhecimento_signal = pyqtSignal(tuple)

    def __init__(self, recon_engine: Reconhecedor, id_esperado: str, nivel_desejado: int):
        super().__init__()
        self._run_flag = True
        self.recon_engine = recon_engine

        # Parâmetros de autenticação baseados na seleção da usuária na UI (Figma)
        self.id_esperado = id_esperado
        self.nivel_desejado = nivel_desejado

        # Flag para parar a thread após um acesso CONCEDIDO ou NEGADO
        self.acesso_finalizado = False

    def run(self):
        # 0 geralmente se refere à webcam padrão
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Erro: Não foi possível acessar a webcam.")
            self._run_flag = False
            self.resultado_reconhecimento_signal.emit(("Erro", 0, "WEBCAM_FALHA"))
            return

        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                # 1. Chama a Lógica de Biometria (Reconhecedor.py)
                id_rec, nivel_max, status, bbox = self.recon_engine.autenticar(
                    frame,
                    self.nivel_desejado,
                    self.id_esperado
                )

                # 2. Desenha a Bounding Box e o Status no Frame

                # Se houver uma face detectada (bbox não é None)
                if bbox:
                    x, y, w, h = bbox
                    cor = (0, 0, 255)  # Vermelho (Padrão: Acesso Negado)

                    if status == "ACESSO CONCEDIDO":
                        cor = (0, 255, 0)  # Verde

                    # Desenha o retângulo ao redor do rosto
                    cv2.rectangle(frame, (x, y), (x + w, y + h), cor, 2)

                    # Coloca o texto do status
                    cv2.putText(frame, status, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)

                # 3. Emite os resultados para a Interface Principal

                # Envia o frame de vídeo para exibição
                self.change_pixmap_signal.emit(frame)

                # Envia o resultado do login (ID, Nível, Status)
                self.resultado_reconhecimento_signal.emit((id_rec, nivel_max, status))

                # 4. Lógica de Encerramento (Conforme seu Fluxo Figma)
                if status == "ACESSO CONCEDIDO":
                    self.acesso_finalizado = True
                    self.stop()
                elif "NEGADO" in status:
                    self.acesso_finalizado = True
                    self.stop()

            cv2.waitKey(1)  # Aguarda um milissegundo

        # Libera a câmera ao sair do loop
        cap.release()

    def stop(self):
        """Método para parar o loop da thread de forma segura."""
        self._run_flag = False
        self.wait()
        print("CameraThread parada.")