import numpy as np
import sys
import os
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QColor
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
import cv2

from Reconhecedor import Reconhecedor
from CameraThread import CameraThread

ID_USUARIOS = {
    "C.J.E.C": "camila",
    "D.S.A": "dafny",
    "S.M.S": "sabrina",
    "Q.A.S": "quezia",
    "V.S.L": "vanessa"
}

PATH_ICONS = "imgsprojeto/icons/"
PATH_LOGO = "imgsprojeto/loguinho/logobioaccess.png"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BioAccess")
        self.setGeometry(100, 100, 800, 600)


        self.recon_engine = Reconhecedor()

        # Variáveis de estado
        self.current_thread = None
        self.id_selecionado = None
        self.nivel_acesso_desejado = 1

        # Container das telas do sistema
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Cria as telas
        self.create_tela_inicial()
        self.create_tela_selecao(nivel=1)
        self.create_tela_selecao(nivel=2)
        self.create_tela_selecao(nivel=3)
        self.create_tela_autenticacao()
        self.create_tela_acesso_concedido(nivel=1)
        self.create_tela_acesso_concedido(nivel=2)
        self.create_tela_acesso_concedido(nivel=3)
        self.create_tela_alerta_negado()

        # Tela inicial; Boas vindas
        self.stack.setCurrentIndex(0)

    #  NAVEGAÇÃO

    def goto_tela_inicial(self):
        self.stack.setCurrentIndex(0)

    def goto_selecao(self, nivel):
        self.nivel_acesso_desejado = nivel
        self.stack.setCurrentIndex(nivel)

    def goto_autenticacao(self):
        self.stack.setCurrentIndex(4)
        self.iniciar_autenticacao()

    def goto_sucesso(self, nivel):
        self.stack.setCurrentIndex(4 + nivel)

    def goto_negado(self):
        self.stack.setCurrentIndex(8)
        QTimer.singleShot(5000, self.close)  # Encerra após 5 segundos

    # FLUXO

    def iniciar_autenticacao(self):
        """Inicia"""
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.stop()

        if not self.id_selecionado:
            print("Erro: ID de usuário não selecionada.")
            self.goto_selecao(self.nivel_acesso_desejado)
            return

        # Autenticando
        self.findChild(QLabel, "lbl_status_autenticacao").setText("Analisando...")
        self.findChild(QLabel, "lbl_video_feed").setText("Aguardando ativação da webcam...")

        # webcam
        self.current_thread = CameraThread(
            self.recon_engine,
            self.id_selecionado,
            self.nivel_acesso_desejado
        )
        #
        self.current_thread.change_pixmap_signal.connect(self.update_image)
        self.current_thread.resultado_reconhecimento_signal.connect(self.handle_resultado_biometria)

        self.current_thread.start()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Recebe o frame do OpenCV e atualiza o QLabel do vídeo."""
        qt_img = self.convert_cv_qt(cv_img)
        self.findChild(QLabel, "lbl_video_feed").setPixmap(qt_img)

    @pyqtSlot(tuple)
    def handle_resultado_biometria(self, resultado):
        """Recebe o resultado da autenticação e gerencia a navegação."""
        id_reconhecida, nivel_max, status = resultado

        # status autenticação
        lbl_status = self.findChild(QLabel, "lbl_status_autenticacao")
        lbl_status.setText(f"Analisando: {status}")

        if status == "ACESSO CONCEDIDO":
            # SEGUE
            self.current_thread.stop()
            self.goto_sucesso(self.nivel_acesso_desejado)

        elif "NEGADO" in status or status == "WEBCAM_FALHA":
            # ENCERRA
            self.current_thread.stop()
            self.goto_negado()

    def closeEvent(self, event):
        """Garante que a thread da câmera pare ao fechar o programa."""
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.stop()
        event.accept()

    # --- CRIAÇÃO DAS TELAS ---

    def create_header(self):
        """Cria o layout de cabeçalho padrão com o logo."""
        header = QHBoxLayout()
        lbl_logo = QLabel()


        if os.path.exists(PATH_LOGO):
            pixmap = QPixmap(PATH_LOGO).scaledToHeight(90)
            lbl_logo.setPixmap(pixmap)
        else:
            lbl_logo.setText("BioAccess Logo")
            lbl_logo.setStyleSheet("color: white;")

        header.addWidget(lbl_logo)
        return header

    def create_tela_inicial(self):
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        # Use um layout horizontal para o cabeçalho
        header_layout = self.create_header()

        # Cria um widget para o cabeçalho para poder alinhar
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(150)  # Altura fixa para o cabeçalho
        vbox.addWidget(header_widget, alignment=Qt.AlignLeft | Qt.AlignTop)

        # Adiciona um espaçador para empurrar o conteúdo para baixo
        vbox.addSpacing(10)

        # "Seja bem-vinda ao"
        lbl_titulo = QLabel("Seja bem-vinda ao")
        lbl_titulo.setFont(QFont("Arial", 16))
        lbl_titulo.setStyleSheet("color: #2C5C12;")
        vbox.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        # "BioAccess"
        lbl_bioaccess = QLabel("BioAccess")
        lbl_bioaccess.setFont(QFont("Inter", 48))
        lbl_bioaccess.setStyleSheet("color: #B1FF87;")
        vbox.addWidget(lbl_bioaccess, alignment=Qt.AlignCenter)


        lbl_subtitulo = QLabel("O sistema de informação do Ministério do Meio Ambiente")
        lbl_subtitulo.setFont(QFont("Arial", 14))
        lbl_subtitulo.setStyleSheet("color: #5F9F3D;")
        vbox.addWidget(lbl_subtitulo, alignment=Qt.AlignCenter)

        vbox.addStretch(1)

        # Botão Entrar
        btn_entrar = QPushButton("Entrar")
        btn_entrar.setFont(QFont("Inter", 10))
        btn_entrar.setStyleSheet("background-color: #244B0E; color:#B1FF87 ; padding: 3px; border-radius: 100px;")
        btn_entrar.setFixedSize(200, 60)
        btn_entrar.clicked.connect(lambda: self.goto_selecao(nivel=1))

        vbox.addWidget(btn_entrar, alignment=Qt.AlignCenter)
        vbox.addStretch(2)

        widget.setStyleSheet("background-color: black;")
        self.stack.addWidget(widget)

    def create_tela_selecao(self, nivel):
        widget = QWidget()
        vbox = QVBoxLayout(widget)

        top_bar_h_box = QHBoxLayout()

        lbl_logo = QLabel()
        if os.path.exists(PATH_LOGO):
            pixmap = QPixmap(PATH_LOGO).scaledToHeight(95)
            lbl_logo.setPixmap(pixmap)
        else:
            lbl_logo.setText("BioAccess Logo")
            lbl_logo.setStyleSheet("color: white;")

        top_bar_h_box.addWidget(lbl_logo, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        lbl_quem_header = QLabel(" Quem está acessando o nível 1?")
        lbl_quem_header.setFont(QFont("Arial", 20))
        lbl_quem_header.setStyleSheet("color: #2C5C12;")
        top_bar_h_box.addWidget(lbl_quem_header, alignment=Qt.AlignVCenter)

        top_bar_h_box.addStretch(1)
        vbox.addLayout(top_bar_h_box)

        list_widget = QListWidget()
        list_widget.setStyleSheet("background-color: black; border: 0px; color: white;")


        for nome_curto, id_sistema in ID_USUARIOS.items():
            item = QListWidgetItem(list_widget)
            item_widget = self.create_user_list_item(nome_curto, id_sistema)
            item.setSizeHint(item_widget.sizeHint())
            list_widget.setItemWidget(item, item_widget)

        # Conecta o clique (Lógica de navegação mantida)
        def on_item_clicked(item):
            selected_widget = list_widget.itemWidget(item)
            nome_curto = selected_widget.findChild(QLabel, "lbl_nome_curto").text()
            self.id_selecionado = ID_USUARIOS[nome_curto]
            self.goto_autenticacao()

        list_widget.itemClicked.connect(on_item_clicked)
        vbox.addWidget(list_widget)

        widget.setStyleSheet("background-color: black;")
        self.stack.addWidget(widget)

    def create_user_list_item(self, nome_curto, id_sistema):
        """Cria um widget customizado para cada item da lista de seleção."""
        item_widget = QWidget()
        hbox = QHBoxLayout(item_widget)
        hbox.setContentsMargins(5, 5, 5, 5)

        # Ícone do usuário
        lbl_icon = QLabel()
        icon_path = os.path.join(PATH_ICONS, f"{id_sistema}icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaledToHeight(97)
            lbl_icon.setPixmap(pixmap)
        else:
            lbl_icon.setText("[Icon]")

        lbl_nome = QLabel(nome_curto)
        lbl_nome.setObjectName("lbl_nome_curto")  # Para obter o nome curto no clique
        lbl_nome.setFont(QFont("Arial", 16))
        lbl_nome.setStyleSheet("color: white;")

        hbox.addWidget(lbl_icon)
        hbox.addWidget(lbl_nome)
        hbox.addStretch(1)  # Espaço

        return item_widget

    def create_tela_autenticacao(self):

        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.addLayout(self.create_header())

        # Rótulo de Status
        lbl_status = QLabel("Analisando...")
        lbl_status.setObjectName("lbl_status_autenticacao")
        lbl_status.setFont(QFont("Arial", 20, QFont.Bold))
        lbl_status.setStyleSheet("color: yellow;")
        vbox.addWidget(lbl_status, alignment=Qt.AlignCenter)

        # Área de exibição do vídeo (QLabel)
        lbl_video = QLabel("Aguardando ativação da webcam...")
        lbl_video.setObjectName("lbl_video_feed")
        lbl_video.setFixedSize(640, 480)  # Tamanho padrão da webcam
        lbl_video.setStyleSheet("background-color: #333; border: 2px dashed #666; color: white;")
        vbox.addWidget(lbl_video, alignment=Qt.AlignCenter)

        vbox.addStretch(1)

        widget.setStyleSheet("background-color: black;")
        self.stack.addWidget(widget)

    def create_tela_acesso_concedido(self, nivel):
        # Baseado nas Telas 'Você está dentro do Nível X!' do Figma
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.addLayout(self.create_header())

        vbox.addStretch(1)

        lbl_titulo = QLabel(f"Você está dentro do Nível {nivel}!")
        lbl_titulo.setFont(QFont("Arial", 36, QFont.Bold))
        lbl_titulo.setStyleSheet("color: #4CAF50;")  # Verde para sucesso
        vbox.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        vbox.addStretch(1)

        if nivel < 3:
            # Botão para o próximo nível (Nível 1 e 2)
            btn_proximo = QPushButton(f"Ir para Nível {nivel + 1}")
            btn_proximo.setFont(QFont("Arial", 18, QFont.Bold))
            btn_proximo.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
            btn_proximo.setFixedSize(250, 60)
            btn_proximo.clicked.connect(lambda: self.goto_selecao(nivel=nivel + 1))
            vbox.addWidget(btn_proximo, alignment=Qt.AlignCenter)
        else:
            # Botão Fechar (Nível 3)
            btn_fechar = QPushButton("Fechar")
            btn_fechar.setFont(QFont("Arial", 18, QFont.Bold))
            btn_fechar.setStyleSheet("background-color: #D32F2F; color: white; padding: 10px; border-radius: 5px;")
            btn_fechar.setFixedSize(250, 60)
            btn_fechar.clicked.connect(self.close)
            vbox.addWidget(btn_fechar, alignment=Qt.AlignCenter)

        vbox.addStretch(2)
        widget.setStyleSheet("background-color: black;")
        self.stack.addWidget(widget)

    def create_tela_alerta_negado(self):

        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.addLayout(self.create_header())

        vbox.addStretch(1)

        lbl_alerta = QLabel("ALERTA")
        lbl_alerta.setFont(QFont("Arial", 36, QFont.Bold))
        lbl_alerta.setStyleSheet("color: #D32F2F;")
        vbox.addWidget(lbl_alerta, alignment=Qt.AlignCenter)


        lbl_cadeado = QLabel("🛑")
        lbl_cadeado.setFont(QFont("Arial", 100))
        vbox.addWidget(lbl_cadeado, alignment=Qt.AlignCenter)

        lbl_negado = QLabel("ACESSO NEGADO")
        lbl_negado.setFont(QFont("Arial", 24, QFont.Bold))
        lbl_negado.setStyleSheet("color: white; background-color: #D32F2F; padding: 10px; border-radius: 5px;")
        vbox.addWidget(lbl_negado, alignment=Qt.AlignCenter)

        vbox.addStretch(2)

        lbl_info = QLabel("O sistema será encerrado automaticamente.")
        lbl_info.setStyleSheet("color: white;")
        vbox.addWidget(lbl_info, alignment=Qt.AlignCenter)

        widget.setStyleSheet("background-color: black;")
        self.stack.addWidget(widget)

    def convert_cv_qt(self, cv_img):
        """Converte o frame do OpenCV (BGR) para o formato QPixmap para exibição."""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(640, 480, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())