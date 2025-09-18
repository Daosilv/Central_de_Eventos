import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
from datetime import datetime

# --- Configurações ---
FONTE_PADRAO = ("Times New Roman", 12)
# Caminho para o banco de dados (deve ser o mesmo dos outros módulos)
diretorio_local_ativo = r'C:\BD_APP_Cemig'
nome_arquivo_bd = 'Primeiro_banco.db'
caminho_bd_ativo = os.path.join(diretorio_local_ativo, nome_arquivo_bd)


class AjustesFrame(tk.Frame):
    """
    Tela para exibir a lista de equipamentos pendentes de ajuste,
    buscando os dados de forma persistente do banco de dados e mostrando
    informações detalhadas e botões de ação para cada item.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Dicionário para guardar referências aos widgets de cada linha
        self.linhas_widgets = {}

        self.criar_layout()
        # Carrega a lista assim que o frame é criado
        self.carregar_equipamentos_pendentes()

    def criar_layout(self):
        """Cria os widgets da tela de Ajustes."""
        
        frame_superior = tk.Frame(self)
        frame_superior.pack(fill='x', padx=10, pady=10)

        # --- Botão de Navegação ---
        btn_voltar = ttk.Button(frame_superior, text="< Voltar ao Menu Principal",
                                command=lambda: self.controller.show_frame("MenuFrame"))
        btn_voltar.pack(side='left', anchor='nw')
        
        # Frame para os botões de ação globais (à direita)
        botoes_globais_frame = tk.Frame(frame_superior)
        botoes_globais_frame.pack(side='right', anchor='ne')

        # --- O botão "Iniciar Selecionados" foi REMOVIDO daqui ---
        
        # --- Botão de Atualizar ---
        btn_atualizar = ttk.Button(botoes_globais_frame, text="Atualizar Lista",
                                   command=self.carregar_equipamentos_pendentes)
        btn_atualizar.pack(side='left', padx=5)

        # --- INÍCIO DA MODIFICAÇÃO ---
        # Novo frame para o botão 'Iniciar', posicionado abaixo do cabeçalho
        start_action_frame = tk.Frame(self)
        start_action_frame.pack(fill='x', padx=20, pady=(0, 5))

        # Novo botão 'Iniciar' com a mesma função do botão anterior
        btn_iniciar = ttk.Button(start_action_frame, text="Iniciar",
                                 command=self.iniciar_selecionados)
        btn_iniciar.pack(side='left')
        # --- FIM DA MODIFICAÇÃO ---

        # --- Container Principal ---
        main_container = tk.LabelFrame(self, text="AJUSTES PENDENTES", font=("Helvetica", 16, "bold"), padx=10, pady=10)
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # --- ESTRUTURA DE LISTA CUSTOMIZADA COM SCROLL ---
        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        self.items_frame = tk.Frame(canvas)
        
        self.items_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.items_frame.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))


    def carregar_equipamentos_pendentes(self):
        """
        Lê o banco de dados com JOIN para buscar informações detalhadas
        e popula a lista customizada na tela.
        """
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self.linhas_widgets.clear()

        if not os.path.exists(caminho_bd_ativo):
            messagebox.showwarning("Banco de Dados", "Arquivo de banco de dados não encontrado.", parent=self)
            return

        try:
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                query = """
                SELECT
                    a.eqpto,
                    c.autor,
                    c.data,
                    c.malha,
                    c.alimentador
                FROM
                    ajustes a
                JOIN
                    (SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn FROM cadastros) c
                ON
                    a.eqpto = c.eqpto
                WHERE
                    c.rn = 1
                ORDER BY
                    a.data_adicao DESC
                """
                cursor.execute(query)
                equipamentos = cursor.fetchall()
                
                for dados_equipamento in equipamentos:
                    self._criar_linha_equipamento(self.items_frame, dados_equipamento)

        except sqlite3.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar a lista de ajustes: {e}", parent=self)

    def iniciar_selecionados(self):
        """
        Verifica quais equipamentos estão selecionados e executa a ação 'Iniciar'.
        """
        equipamentos_a_iniciar = []
        # Itera sobre o dicionário de widgets para encontrar os selecionados
        for eqpto, widgets in self.linhas_widgets.items():
            if widgets["check_var"].get():  # .get() retorna o estado (True/False) da checkbutton
                equipamentos_a_iniciar.append(eqpto)
        
        if not equipamentos_a_iniciar:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione pelo menos um equipamento para iniciar.")
            return

        # Lógica de "Iniciar" (atualmente, apenas exibe os selecionados)
        msg = "Os seguintes equipamentos foram 'Iniciados':\n\n- " + "\n- ".join(equipamentos_a_iniciar)
        messagebox.showinfo("Ação Executada", msg)

    def _criar_linha_equipamento(self, parent, dados):
        """Cria um frame (linha) com todos os widgets para um único equipamento."""
        eqpto, autor, data, malha, alimentador = dados
        
        row_frame = tk.Frame(parent, bd=1, relief="solid")
        row_frame.pack(fill="x", expand=True, pady=1, padx=2)
        
        # --- 1. Caixa de Seleção (Tick) à esquerda ---
        check_var = tk.BooleanVar()
        check = ttk.Checkbutton(row_frame, variable=check_var)
        check.pack(side="left", padx=10, pady=5)
        
        # --- 3. Ícones de Ação (à direita, para alinhamento correto) ---
        actions_frame = tk.Frame(row_frame)
        actions_frame.pack(side="right", padx=10, pady=5)
        
        folder_button = tk.Button(actions_frame, text="📁", relief="flat", cursor="hand2")
        folder_button.pack(side="left", padx=5)

        play_button = tk.Button(actions_frame, text="▶️", relief="flat", cursor="hand2")
        play_button.pack(side="left", padx=5)

        obs_button = tk.Button(actions_frame, text="Obs", font=("Arial", 8), width=4)
        obs_button.pack(side="left", padx=5)

        concluir_button = tk.Button(actions_frame, text="Concluir", font=("Arial", 9))
        concluir_button.pack(side="left", padx=5)
        
        # --- 2. Frame de Informações (no meio, preenchendo o espaço) ---
        info_frame = tk.Frame(row_frame)
        info_frame.pack(side="left", fill="x", expand=True, padx=5)

        # Labels em colunas com largura fixa para alinhamento
        tk.Label(info_frame, text=eqpto, width=15, anchor="w", font=("Courier", 10)).pack(side="left")
        tk.Label(info_frame, text=autor, width=25, anchor="w", font=("Courier", 10)).pack(side="left")
        tk.Label(info_frame, text=data, width=12, anchor="w", font=("Courier", 10)).pack(side="left")
        tk.Label(info_frame, text=malha, width=15, anchor="w", font=("Courier", 10)).pack(side="left")
        tk.Label(info_frame, text=alimentador, width=15, anchor="w", font=("Courier", 10)).pack(side="left")

        # Armazena as referências, incluindo a variável da checkbutton
        self.linhas_widgets[eqpto] = {
            "frame": row_frame,
            "check_var": check_var,
            "folder_button": folder_button,
            "play_button": play_button,
            "obs_button": obs_button,
            "concluir_button": concluir_button
        }


if __name__ == '__main__':
    class DummyController(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Teste do Módulo de Ajustes")
            self.geometry("1200x600")

        def show_frame(self, page_name):
            print(f"Simulando navegação para: {page_name}")
            self.destroy()

    app = DummyController()
    ajustes_frame = AjustesFrame(app, app)
    ajustes_frame.pack(fill="both", expand=True)
    app.mainloop()
