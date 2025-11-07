# MainWindow.py
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

# Importamos a lógica e o motor assíncrono
from Reconhecedor import Reconhecedor
from CameraThread import CameraThread

# --- CONFIGURAÇÕES GLOBAIS ---
# Mapeamento para exibição na UI (Nome Longo vs. ID do sistema)
ID_USUARIOS = {
    "C.J.E.C": "camila",
    "D.S.A": "dafny",
    "S.M.S": "sabrina",
    "Q.A.S": "quezia",
    "V.S.L": "vanessa"
}

# --- CAMINHOS DE MÍDIA (CORRIGIR SE NECESSÁRIO) ---
PATH_ICONS = "imgsprojeto/icons/"
PATH_LOGO = "imgsprojeto/loguinho/logobioaccess.png"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BioAccess - Sistema de Autenticação Biometrica")
        self.setGeometry(100, 100, 800, 600)

        # Inicializa o motor de reconhecimento
        self.recon_engine = Reconhecedor()

        # Variáveis de estado
        self.current_thread = None
        self.id_selecionado = None
        self.nivel_acesso_desejado = 1

        # --- Configura o Stacked Widget para gerenciar as telas do Figma ---
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

        # Mostra a Tela Inicial ao iniciar
        self.stack.setCurrentIndex(0)

    # --- FUNÇÕES DE NAVEGAÇÃO ---

    def goto_tela_inicial(self):
        self.stack.setCurrentIndex(0)

    def goto_selecao(self, nivel):
        # Vai para o índice da tela de seleção com base no nível
        # Índices: 1 (Seleção N1), 2 (Seleção N2), 3 (Seleção N3)
        self.nivel_acesso_desejado = nivel
        self.stack.setCurrentIndex(nivel)

    def goto_autenticacao(self):
        # Tela de autenticação está no índice 4
        self.stack.setCurrentIndex(4)
        self.iniciar_autenticacao()

    def goto_sucesso(self, nivel):
        # Índices de Sucesso: 5 (Sucesso N1), 6 (Sucesso N2), 7 (Sucesso N3)
        self.stack.setCurrentIndex(4 + nivel)

    def goto_negado(self):
        # Tela de Alerta Negado está no índice 8
        self.stack.setCurrentIndex(8)
        # Conforme o Figma, o sistema encerra automaticamente após a negação
        QTimer.singleShot(3000, self.close)  # Encerra após 3 segundos

    # --- FLUXO DE THREAD E BIOMETRIA ---

    def iniciar_autenticacao(self):
        """Inicia a QThread da câmera para o ID e Nível selecionados."""
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.stop()

        # Garante que o ID foi selecionado
        if not self.id_selecionado:
            print("Erro: ID de usuário não selecionada.")
            self.goto_selecao(self.nivel_acesso_desejado)
            return

        # Atualiza o QLabel da Tela de Autenticação
        self.findChild(QLabel, "lbl_status_autenticacao").setText("Analisando...")
        self.findChild(QLabel, "lbl_video_feed").setText("Aguardando ativação da webcam...")

        # Cria e inicia a thread da câmera
        self.current_thread = CameraThread(
            self.recon_engine,
            self.id_selecionado,
            self.nivel_acesso_desejado
        )
        # Conecta os sinais da thread aos slots da Main Window
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

        # Atualiza o status na tela de Autenticação
        lbl_status = self.findChild(QLabel, "lbl_status_autenticacao")
        lbl_status.setText(f"Analisando: {status}")

        if status == "ACESSO CONCEDIDO":
            # Para a thread e navega para a tela de sucesso
            self.current_thread.stop()
            self.goto_sucesso(self.nivel_acesso_desejado)

        elif "NEGADO" in status or status == "WEBCAM_FALHA":
            # Para a thread e navega para a tela de alerta
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

        # Carrega a logo a partir do caminho
        if os.path.exists(PATH_LOGO):
            pixmap = QPixmap(PATH_LOGO).scaledToHeight(60)  # Ajuste o tamanho se precisar
            lbl_logo.setPixmap(pixmap)
        else:
            lbl_logo.setText("BioAccess Logo")  # Texto de fallback se não encontrar
            lbl_logo.setStyleSheet("color: white;")

        header.addWidget(lbl_logo)
        # Remova ou ajuste o addStretch se quiser o logo sempre na esquerda superior
        # header.addStretch(1)
        return header

    def create_tela_inicial(self):
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        # Use um layout horizontal para o cabeçalho
        header_layout = self.create_header()

        # Cria um widget para o cabeçalho para poder alinhar
        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(80)  # Altura fixa para o cabeçalho
        vbox.addWidget(header_widget, alignment=Qt.AlignLeft | Qt.AlignTop)

        # Adiciona um espaçador para empurrar o conteúdo para baixo
        vbox.addSpacing(50)  # Espaço entre o cabeçalho e o texto principal

        # "Seja bem-vinda ao"
        lbl_titulo = QLabel("Seja bem-vinda ao")
        lbl_titulo.setFont(QFont("Arial", 16))
        lbl_titulo.setStyleSheet("color: white;")
        vbox.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        # "BioAccess"
        lbl_bioaccess = QLabel("BioAccess")
        lbl_bioaccess.setFont(QFont("Arial", 48, QFont.Bold))
        lbl_bioaccess.setStyleSheet("color: #4CAF50;")
        vbox.addWidget(lbl_bioaccess, alignment=Qt.AlignCenter)

        # NOVO: Texto adicional "O sistema de informação..."
        lbl_subtitulo = QLabel("O sistema de informação do Ministério do Meio Ambiente")
        lbl_subtitulo.setFont(QFont("Arial", 14))
        lbl_subtitulo.setStyleSheet("color: #4CAF50;")  # Cor verde
        vbox.addWidget(lbl_subtitulo, alignment=Qt.AlignCenter)

        vbox.addStretch(1)  # Espaço expansível

        # Botão Entrar
        btn_entrar = QPushButton("Entrar")
        btn_entrar.setFont(QFont("Arial", 18, QFont.Bold))
        btn_entrar.setStyleSheet("background-color: #388E3C; color: white; padding: 10px; border-radius: 5px;")
        btn_entrar.setFixedSize(200, 60)
        btn_entrar.clicked.connect(lambda: self.goto_selecao(nivel=1))

        vbox.addWidget(btn_entrar, alignment=Qt.AlignCenter)
        vbox.addStretch(2)  # Mais espaço expansível para empurrar o botão para cima

        widget.setStyleSheet("background-color: black;")
        self.stack.addWidget(widget)

    def create_tela_selecao(self, nivel):
        # Baseado nas Telas de Seleção Nível 1, 2 e 3 do Figma
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.addLayout(self.create_header())

        lbl_titulo = QLabel(f"Seleção de usuário para entrar no nível {nivel}")
        lbl_titulo.setFont(QFont("Arial", 24, QFont.Bold))
        lbl_titulo.setStyleSheet("color: white;")
        vbox.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        lbl_quem = QLabel("Quem está acessando?")
        lbl_quem.setFont(QFont("Arial", 18))
        lbl_quem.setStyleSheet("color: #4CAF50;")
        vbox.addWidget(lbl_quem)

        list_widget = QListWidget()
        list_widget.setStyleSheet("background-color: black; border: 1px solid #333; color: white;")

        # Popula a lista de usuários
        for nome_curto, id_sistema in ID_USUARIOS.items():
            # Apenas usuários com nível de acesso suficiente aparecem na lista
            # Como a lógica de acesso só está no .pkl, vamos mostrar todos por enquanto
            # A lógica de Nível é verificada no Reconhecedor, não na seleção
            item = QListWidgetItem(list_widget)
            item_widget = self.create_user_list_item(nome_curto, id_sistema)
            item.setSizeHint(item_widget.sizeHint())
            list_widget.setItemWidget(item, item_widget)

        # Conecta o clique da lista à função que inicia a autenticação
        def on_item_clicked(item):
            # Obtém o nome curto e faz o mapeamento para a ID do sistema
            selected_widget = list_widget.itemWidget(item)
            nome_curto = selected_widget.findChild(QLabel, "lbl_nome_curto").text()
            self.id_selecionado = ID_USUARIOS[nome_curto]
            self.goto_autenticacao()  # Vai para a tela da webcam

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
            pixmap = QPixmap(icon_path).scaledToHeight(40)
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
        # Baseado na Tela de Autenticação do Usuário Selecionado do Figma
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
        # Baseado na Tela de Alerta NEGADO do Figma (Encerra o programa)
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.addLayout(self.create_header())

        vbox.addStretch(1)

        lbl_alerta = QLabel("ALERTA")
        lbl_alerta.setFont(QFont("Arial", 36, QFont.Bold))
        lbl_alerta.setStyleSheet("color: #D32F2F;")  # Vermelho para negação
        vbox.addWidget(lbl_alerta, alignment=Qt.AlignCenter)

        # Placeholder para o ícone de cadeado grande
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

    # --- Utilitário de Conversão OpenCV para Qt ---
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

    # Define o estilo da aplicação
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())