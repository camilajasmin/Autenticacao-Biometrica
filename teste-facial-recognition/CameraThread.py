
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from Reconhecedor import Reconhecedor

class CameraThread(QThread):

    change_pixmap_signal = pyqtSignal(np.ndarray)
    resultado_reconhecimento_signal = pyqtSignal(tuple)

    def __init__(self, recon_engine: Reconhecedor, id_esperado: str, nivel_desejado: int):
        super().__init__()
        self._run_flag = True
        self.recon_engine = recon_engine

        self.id_esperado = id_esperado
        self.nivel_desejado = nivel_desejado

        self.acesso_finalizado = False

    def run(self):
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Erro: Não foi possível acessar a webcam.")
            self._run_flag = False
            self.resultado_reconhecimento_signal.emit(("Erro", 0, "WEBCAM_FALHA"))
            return

        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                id_rec, nivel_max, status, bbox = self.recon_engine.autenticar(
                    frame,
                    self.nivel_desejado,
                    self.id_esperado
                )

                if bbox:
                    x, y, w, h = bbox
                    cor = (0, 0, 255)

                    if status == "ACESSO CONCEDIDO":
                        cor = (0, 255, 0)  # Verde


                    cv2.rectangle(frame, (x, y), (x + w, y + h), cor, 2)
                    cv2.putText(frame, status, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, cor, 2)

                self.change_pixmap_signal.emit(frame)

                self.resultado_reconhecimento_signal.emit((id_rec, nivel_max, status))


                if status == "ACESSO CONCEDIDO":
                    self.acesso_finalizado = True
                    self.stop()
                elif "NEGADO" in status:
                    self.acesso_finalizado = True
                    self.stop()

            cv2.waitKey(1)


        cap.release()

    def stop(self):
        """Método para parar o loop da thread de forma segura."""
        self._run_flag = False
        self.wait()
        print("CameraThread parada.")