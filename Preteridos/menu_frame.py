import tkinter as tk
from tkinter import ttk

class MenuFrame(tk.Frame):
    """
    A tela de menu principal da aplicação.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Estilo para os botões do menu
        style = ttk.Style()
        style.configure("Menu.TButton", font=("Helvetica", 14), padding=(20, 10))

        # Container para centralizar os botões
        button_container = tk.Frame(self)
        button_container.place(relx=0.5, rely=0.5, anchor="center")

        # Título do Menu
        label_titulo = ttk.Label(button_container, text="Central de Eventos", font=("Helvetica", 24, "bold"))
        label_titulo.pack(pady=(0, 40))

        # --- Botões de Navegação ---
        btn_memorial = ttk.Button(
            button_container,
            text="Memorial de Cálculo",
            style="Menu.TButton",
            command=lambda: self.controller.show_frame("MemorialCalculoFrame")
        )
        btn_memorial.pack(pady=10, fill='x')

        btn_ajustes = ttk.Button(
            button_container,
            text="Ajustes",
            style="Menu.TButton",
            command=lambda: self.controller.show_frame("AjustesFrame")
        )
        btn_ajustes.pack(pady=10, fill='x')

        btn_visualizacao = ttk.Button(
            button_container,
            text="Visualização",
            style="Menu.TButton",
            # Exibe um popup de login simulado ao tentar acessar
            command=lambda: self.controller.show_login_popup("VisualizacaoFrame")
        )
        btn_visualizacao.pack(pady=10, fill='x')
