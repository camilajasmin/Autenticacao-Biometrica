import numpy as np
import sys
import os
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QListWidget, QListWidgetItem, QScrollArea
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

        self.current_thread = None
        self.id_selecionado = None
        self.nivel_acesso_desejado = 1

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.create_tela_inicial()
        self.create_tela_selecao(nivel=1)
        self.create_tela_selecao(nivel=2)
        self.create_tela_selecao(nivel=3)
        self.create_tela_autenticacao()
        self.create_tela_acesso_concedido(nivel=1)
        self.create_tela_acesso_concedido(nivel=2)
        self.create_tela_acesso_concedido(nivel=3)
        self.create_tela_alerta_negado()

        self.stack.setCurrentIndex(0)

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
        QTimer.singleShot(5000, self.close)

    def iniciar_autenticacao(self):
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.stop()

        if not self.id_selecionado:
            print("Erro: ID de usuário não selecionada.")
            self.goto_selecao(self.nivel_acesso_desejado)
            return

        self.findChild(QLabel, "lbl_status_autenticacao").setText("Analisando...")
        self.findChild(QLabel, "lbl_video_feed").setText("Aguardando ativação da webcam...")

        self.current_thread = CameraThread(
            self.recon_engine,
            self.id_selecionado,
            self.nivel_acesso_desejado
        )

        self.current_thread.change_pixmap_signal.connect(self.update_image)
        self.current_thread.resultado_reconhecimento_signal.connect(self.handle_resultado_biometria)

        self.current_thread.start()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.findChild(QLabel, "lbl_video_feed").setPixmap(qt_img)

    @pyqtSlot(tuple)
    def handle_resultado_biometria(self, resultado):
        id_reconhecida, nivel_max, status = resultado

        lbl_status = self.findChild(QLabel, "lbl_status_autenticacao")
        lbl_status.setText(f"Analisando: {status}")

        if status == "ACESSO CONCEDIDO":

            self.current_thread.stop()
            self.goto_sucesso(self.nivel_acesso_desejado)

        elif "NEGADO" in status or status == "WEBCAM_FALHA":

            self.current_thread.stop()
            self.goto_negado()

    def closeEvent(self, event):
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.stop()
        event.accept()

    def create_header(self):
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

        header_layout = self.create_header()

        header_widget = QWidget()
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(150)
        vbox.addWidget(header_widget, alignment=Qt.AlignLeft | Qt.AlignTop)

        vbox.addSpacing(10)

        lbl_titulo = QLabel("Seja bem-vinda ao")
        lbl_titulo.setFont(QFont("Arial", 16))
        lbl_titulo.setStyleSheet("color: #2C5C12;")
        vbox.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        lbl_bioaccess = QLabel("BioAccess")
        lbl_bioaccess.setFont(QFont("Inter", 48))
        lbl_bioaccess.setStyleSheet("color: #B1FF87;")
        vbox.addWidget(lbl_bioaccess, alignment=Qt.AlignCenter)

        lbl_subtitulo = QLabel("O sistema de informação do Ministério do Meio Ambiente")
        lbl_subtitulo.setFont(QFont("Arial", 14))
        lbl_subtitulo.setStyleSheet("color: #5F9F3D;")
        vbox.addWidget(lbl_subtitulo, alignment=Qt.AlignCenter)

        vbox.addStretch(1)

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

        lbl_quem_header = QLabel(f" Quem está acessando o nível {nivel}?")
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
        item_widget = QWidget()
        hbox = QHBoxLayout(item_widget)
        hbox.setContentsMargins(5, 5, 5, 5)

        lbl_icon = QLabel()
        icon_path = os.path.join(PATH_ICONS, f"{id_sistema}icon.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaledToHeight(97)
            lbl_icon.setPixmap(pixmap)
        else:
            lbl_icon.setText("[Icon]")

        lbl_nome = QLabel(nome_curto)
        lbl_nome.setObjectName("lbl_nome_curto")
        lbl_nome.setFont(QFont("Arial", 16))
        lbl_nome.setStyleSheet("color: white;")

        hbox.addWidget(lbl_icon)
        hbox.addWidget(lbl_nome)
        hbox.addStretch(1)

        return item_widget

    def create_tela_autenticacao(self):

        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.addLayout(self.create_header())

        lbl_status = QLabel("Analisando...")
        lbl_status.setObjectName("lbl_status_autenticacao")
        lbl_status.setFont(QFont("Arial", 20, QFont.Bold))
        lbl_status.setStyleSheet("color: yellow;")
        vbox.addWidget(lbl_status, alignment=Qt.AlignCenter)

        lbl_video = QLabel("Aguardando ativação da webcam...")
        lbl_video.setObjectName("lbl_video_feed")
        lbl_video.setFixedSize(640, 480)
        lbl_video.setStyleSheet("background-color: #333; border: 2px dashed #666; color: white;")
        vbox.addWidget(lbl_video, alignment=Qt.AlignCenter)

        vbox.addStretch(1)

        widget.setStyleSheet("background-color: black;")
        self.stack.addWidget(widget)

    def create_tela_acesso_concedido(self, nivel):

        mensagens_ambientais = {

            1: (
                "A Dimensão e Riqueza dos Biomas Brasileiros\n\n"
                "O Brasil abriga seis biomas continentais, com destaque para a Amazônia, que cobre cerca de 49% do território nacional e é reconhecida mundialmente como a maior floresta tropical e a maior reserva de diversidade biológica do planeta.\n\n"
                "A Amazônia não é apenas vital pela sua biodiversidade (que se estima abrigar pelo menos a metade de todas as espécies vivas), mas também por sua importância hídrica global, contendo 20% da disponibilidade mundial de água. Outro bioma de importância singular é o Cerrado, que, embora esteja majoritariamente no Planalto Central e ocupe aproximadamente 24% do território, é reconhecido como a savana mais rica do mundo em biodiversidade. O equilíbrio ecológico dessas vastas áreas é sensível à interferência humana, com o Cerrado enfrentando intensas alterações devido à pecuária e agricultura desde os anos 1960.\n\n"
                "Ameaça e Devastação da Mata Atlântica\n\n"
                "Em contraste com a Amazônia, a Mata Atlântica (que ocupa cerca de 13% do país) é consistentemente citada como o bioma mais ameaçado do Brasil. Essa vulnerabilidade é histórica e geográfica: por se localizar na região litorânea, concentra mais de 50% da população brasileira.\n\n"
                "Devido à expansão urbana, ciclos econômicos e agropecuária ao longo de cinco séculos, a Mata Atlântica apresenta os piores índices de perda de cobertura vegetal, com apenas 27% de sua cobertura florestal original preservada. Embora o bioma seja dotado de uma lei específica de proteção e contenha uma biodiversidade ímpar, essa redução drástica de área e a fragmentação colocam em risco milhares de espécies endêmicas e comprometem serviços ambientais vitais.\n\n"
                "O Papel do MMA e o Desafio do Carbono\n\n"
                "O Ministério do Meio Ambiente e Mudança do Clima (MMA) atua como um pilar na proteção dos biomas, focando em controle do desmatamento, queimadas e na elaboração de políticas de biodiversidade e clima. A importância da Amazônia transcende a esfera nacional, pois a floresta atua como um gigantesco reservatório de carbono, com cerca de 20 Gigatoneladas estocadas no solo, fundamental para a mitigação das mudanças climáticas.\n\n"
                "No entanto, o avanço da degradação e o desmatamento colocam em risco essa função ecológica, com projeções indicando que o bioma pode deixar de capturar bilhões de toneladas de carbono nos próximos anos. O MMA e os governos estaduais buscam enfrentar esses desafios com programas como o Projeto Floresta+ Amazônia e a regulamentação do mercado de carbono, elementos cruciais para o desenvolvimento sustentável e o cumprimento das metas climáticas do Brasil."
            ),

            2: (
                'Biomas, Biodiversidade e o Desafio da Devastação\n'
                'O Brasil é um país de megadiversidade, com a Amazônia destacando-se como o maior bioma e um ecossistema crucial para o clima global e a biodiversidade. O Ministério do Meio Ambiente e Mudança do Clima (MMA) enfatiza a importância de todos os biomas brasileiros na conservação da biodiversidade.\n'
                'Contudo, a conservação é um desafio, especialmente na Mata Atlântica, que é classificada como o bioma mais devastado do Brasil. A Mata Atlântica, apesar de sua importância global no combate às crises de biodiversidade e clima, exige urgentes esforços de conservação e restauração. Além disso, dados do MapBiomas indicam que o desmatamento em biomas no Brasil continua a ser uma preocupação crescente.\n\n'
                'Metas Nacionais e Acordos Climáticos\n'
                'Em resposta ao desafio do desmatamento, o governo brasileiro estabeleceu a meta ambiciosa de alcançar o Desmatamento Ilegal Zero no Brasil até 2030. Essa meta é operacionalizada por planos como a 5ª Fase do Plano de Prevenção e Controle do Desmatamento na Amazônia Legal (PPCDAm).\n'
                'No âmbito internacional, o Brasil possui compromissos climáticos robustos, como a meta de Redução de Emissões de 67% até 2035 (NDC revisada do Acordo de Paris) e o foco estratégico no Sequestro de Carbono da Amazônia, reconhecido como um ativo crucial para a mitigação das mudanças climáticas. A Amazônia, em particular, é o bioma que o MMA destaca como um pilar da política climática e de desenvolvimento sustentável.\n\n'
                'Inovação e Inteligência Artificial na Fiscalização\n'
                'A tecnologia está se tornando uma ferramenta indispensável no combate aos crimes ambientais e na proteção dos biomas. A Inteligência Artificial (IA) é uma peça-chave para a prevenção, com o desenvolvimento de novos mapeamentos que ajudam a prever e prevenir o desmatamento na Amazônia.\n'
                'Além da prevenção, o IBAMA (Instituto Brasileiro do Meio Ambiente e dos Recursos Naturais Renováveis) está implementando soluções inovadoras de automação e IA no seu processo sancionador ambiental. O objetivo é aumentar a eficiência, agilidade e imparcialidade na aplicação de multas e penalidades, reforçando o controle e o ordenamento ambiental territorial.'
            ),

            3: (
                'Metas Nacionais e Compromissos Climáticos (NDC)\n\n'
                'O Brasil estabeleceu compromissos climáticos globais (NDC) e internos de grande alcance, definindo a trajetória ambiental do país para as próximas décadas:\n\n'
                'Redução de Emissões: O país apresentou a meta de reduzir as emissões em 67% até 2035, um compromisso revisado apresentado para a COP30.\n'
                'Desmatamento Zero: Uma comissão governamental foi instalada com o objetivo de zerar o desmatamento ilegal no Brasil até 2030.\n'
                'Plano de Ação: O combate ao desmatamento é guiado por planos como a 5ª fase do PPCDAm (Plano de Ação para Prevenção e Controle do Desmatamento na Amazônia Legal).\n'
                'Sequestro de Carbono: A estratégia é baseada no papel crucial da Amazônia (o maior bioma brasileiro, ocupando 49% do território), que atua no sequestro de carbono, com estimativas de até 70 bilhões de toneladas de CO2 equivalente.\n\n'
                'Tecnologia Avançada na Fiscalização e Gestão\n\n'
                'A fiscalização e o controle ambiental são realizados com tecnologia de ponta, essenciais para o cumprimento das metas:\n\n'
                'Inteligência Artificial (IA) e Automação: Há um investimento crescente no uso de IA e automação para:\n'
                '    Prevenir o desmatamento na Amazônia através de novos mapeamentos preditivos.\n'
                '    Acelerar o processo sancionador ambiental (multas e penalidades), como evidenciado pelo acordo de cooperação firmado entre o IBAMA e o Funbio para implementar soluções inovadoras.\n'
                '    Transformar a gestão ambiental, incluindo a análise de conformidade legal e a otimização de rotinas.\n'
                'Monitoramento por Satélite: O sistema de monitoramento da Amazônia, liderado por instituições como o INPE, é considerado vanguarda mundial na detecção de alterações da cobertura vegetal, fornecendo os dados cruciais para as ações de fiscalização e para a validação das metas.'
            )
        }

        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.addLayout(self.create_header())

        vbox.addSpacing(0)

        lbl_titulo = QLabel(f"Nível {nivel}")
        lbl_titulo.setFont(QFont("Arial", 15))
        lbl_titulo.setStyleSheet("color: #B1FF87;")
        vbox.addWidget(lbl_titulo, alignment=Qt.AlignCenter)

        vbox.addSpacing(5)

        lbl_info_ambiental = QLabel(mensagens_ambientais.get(nivel, "Informação ambiental não disponível."))
        lbl_info_ambiental.setFont(QFont("Arial", 10))

        lbl_info_ambiental.setStyleSheet("color: black; background-color: #F0EEE0; padding: 15px;")
        lbl_info_ambiental.setWordWrap(True)
        lbl_info_ambiental.setAlignment(Qt.AlignJustify | Qt.AlignTop)

        scroll_area = QScrollArea()

        scroll_area.setWidgetResizable(True)

        scroll_area.setWidget(lbl_info_ambiental)

        scroll_area.setStyleSheet("border-radius: 10px; border: 0px;")

        scroll_area.setFixedSize(750, 450)

        vbox.addWidget(scroll_area, alignment=Qt.AlignCenter)

        vbox.addStretch(1)

        if nivel < 3:
            btn_proximo = QPushButton(f"Ir para Nível {nivel + 1}")
            btn_proximo.setFont(QFont("Arial", 10))
            btn_proximo.setStyleSheet("background-color: #244B0E; color: white; padding: 10px; border-radius: 5px;")
            btn_proximo.setFixedSize(250, 60)
            btn_proximo.clicked.connect(lambda: self.goto_selecao(nivel=nivel + 1))
            vbox.addWidget(btn_proximo, alignment=Qt.AlignCenter)
        else:
            btn_fechar = QPushButton("Fechar")
            btn_fechar.setFont(QFont("Arial", 10))
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