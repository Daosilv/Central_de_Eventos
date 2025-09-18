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

# --- JANELA POP-UP PARA OBSERVAÇÕES ---
class ObsWindow(tk.Toplevel):
    def __init__(self, parent, eqpto):
        super().__init__(parent)
        self.eqpto = eqpto
        
        self.title(f"Observação para {eqpto}")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        
        self.resizable(False, False)

        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(main_frame, text="Insira a observação:", font=FONTE_PADRAO).pack(anchor="w")
        
        text_frame = tk.Frame(main_frame, bd=1, relief="solid")
        self.text_obs = tk.Text(text_frame, wrap="word", font=FONTE_PADRAO, height=15)
        self.text_obs.pack(fill="both", expand=True)
        text_frame.pack(fill="both", expand=True, pady=5)
        
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(5,0))
        
        ttk.Button(button_frame, text="Salvar", command=self.salvar_e_fechar).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side="right")

        self.carregar_obs_existente()
        
    def carregar_obs_existente(self):
        try:
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                cursor.execute("SELECT observacao FROM ajustes WHERE eqpto = ?", (self.eqpto,))
                resultado = cursor.fetchone()
                if resultado and resultado[0]:
                    self.text_obs.insert("1.0", resultado[0])
        except sqlite3.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar a observação: {e}", parent=self)

    def salvar_e_fechar(self):
        texto = self.text_obs.get("1.0", "end-1c")
        try:
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                cursor.execute("UPDATE ajustes SET observacao = ? WHERE eqpto = ?", (texto, self.eqpto))
            messagebox.showinfo("Sucesso", "Observação salva com sucesso.", parent=self)
            self.destroy()
        except sqlite3.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível salvar a observação: {e}", parent=self)


class AjustesFrame(tk.Frame):
    """
    Tela para exibir a lista de equipamentos pendentes de ajuste.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.linhas_widgets = {}
        self.criar_layout()
        self.carregar_equipamentos_pendentes()

    def criar_layout(self):
        frame_superior = tk.Frame(self)
        frame_superior.pack(fill='x', padx=10, pady=10)

        btn_voltar = ttk.Button(frame_superior, text="< Voltar ao Menu Principal",
                                command=lambda: self.controller.show_frame("MenuFrame"))
        btn_voltar.pack(side='left', anchor='nw')
        
        botoes_globais_frame = tk.Frame(frame_superior)
        botoes_globais_frame.pack(side='right', anchor='ne')

        btn_atualizar = ttk.Button(botoes_globais_frame, text="Atualizar Lista",
                                   command=self.carregar_equipamentos_pendentes)
        btn_atualizar.pack(side='left', padx=5)

        main_container = tk.LabelFrame(self, text="AJUSTES PENDENTES", font=("Helvetica", 16, "bold"), padx=10, pady=10)
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        btn_iniciar = ttk.Button(main_container, text="Iniciar",
                                 command=self.iniciar_selecionados)
        btn_iniciar.pack(anchor='w', pady=(0, 10))
        
        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        self.items_frame = tk.Frame(canvas)
        
        self.items_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.items_frame.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def carregar_equipamentos_pendentes(self):
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self.linhas_widgets.clear()

        # --- LÓGICA DE LAYOUT DEFINITIVA USANDO UM ÚNICO GRID ---
        
        # 1. Definir as colunas do grid principal e seus pesos relativos
        self.items_frame.columnconfigure(0, weight=0)  # Checkbox
        self.items_frame.columnconfigure(1, weight=3)  # Equipamento
        self.items_frame.columnconfigure(2, weight=5)  # Autor
        self.items_frame.columnconfigure(3, weight=3)  # Data
        self.items_frame.columnconfigure(4, weight=3)  # Malha
        self.items_frame.columnconfigure(5, weight=4)  # Alimentador
        self.items_frame.columnconfigure(6, weight=0)  # Coluna para os 4 botões de ação

        # 2. Criar o cabeçalho na linha 0 do grid
        headers = ["Equipamento", "Autor", "Data", "Malha", "Alimentador"]
        for i, header_text in enumerate(headers):
            label = tk.Label(self.items_frame, text=header_text, font=("Arial", 10, "bold"), relief="solid", bd=1)
            label.grid(row=0, column=i+1, sticky="nsew", padx=1, pady=1)
        
        # Separador horizontal abaixo do cabeçalho
        ttk.Separator(self.items_frame, orient='horizontal').grid(row=1, column=0, columnspan=7, sticky='ew', pady=2)

        # 3. Buscar dados e popular as linhas seguintes do grid
        try:
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                query = """
                SELECT a.eqpto, c.autor, c.data, c.malha, c.alimentador
                FROM ajustes a
                JOIN (SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn FROM cadastros) c
                ON a.eqpto = c.eqpto WHERE c.rn = 1 ORDER BY a.data_adicao DESC
                """
                cursor.execute(query)
                equipamentos = cursor.fetchall()
                
                # O loop começa da linha 2, pois a linha 0 é o header e a 1 é o separador
                for index, dados_equipamento in enumerate(equipamentos, start=2):
                    self._criar_linha_equipamento(self.items_frame, dados_equipamento, index)
        except sqlite3.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar a lista de ajustes: {e}", parent=self)

    def iniciar_selecionados(self):
        equipamentos_a_iniciar = [eqpto for eqpto, widgets in self.linhas_widgets.items() if widgets["check_var"].get()]
        if not equipamentos_a_iniciar:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione pelo menos um equipamento para iniciar.")
            return
        msg = "Os seguintes equipamentos foram 'Iniciados':\n\n- " + "\n- ".join(equipamentos_a_iniciar)
        messagebox.showinfo("Ação Executada", msg)

    def _abrir_janela_obs(self, eqpto):
        ObsWindow(self, eqpto)

    def _concluir_equipamento(self, eqpto_a_concluir):
        confirmar = messagebox.askyesno(
            title="Confirmar Conclusão",
            message=f"Você quer concluir o equipamento {eqpto_a_concluir}?",
            detail="Esta ação removerá o item da lista de pendências."
        )
        if confirmar:
            try:
                with sqlite3.connect(caminho_bd_ativo) as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("DELETE FROM ajustes WHERE eqpto = ?", (eqpto_a_concluir,))
                self.carregar_equipamentos_pendentes()
            except sqlite3.Error as e:
                messagebox.showerror("Erro de Banco de Dados", f"Não foi possível concluir o item: {e}", parent=self)

    def _criar_linha_equipamento(self, parent, dados, row_index):
        """Cria os widgets para uma linha de dados diretamente no grid principal."""
        eqpto, autor, data, malha, alimentador = dados
        
        # Frame para ter a borda em volta da linha inteira
        row_frame = tk.Frame(parent, bd=1, relief="solid")
        row_frame.grid(row=row_index, column=0, columnspan=7, sticky="nsew", pady=(0, 2))

        # Checkbox
        check_var = tk.BooleanVar()
        check = ttk.Checkbutton(row_frame, variable=check_var)
        check.pack(side="left", padx=10)

        # Labels de dados
        labels_data = [eqpto, autor, data, malha, alimentador]
        col_widths = [18, 30, 15, 18, 18]
        
        for i, item in enumerate(labels_data):
            tk.Label(row_frame, text=item, font=("Courier", 10), anchor="w", width=col_widths[i]).pack(side="left", padx=5)

        # Frame para os botões de ação (à direita)
        actions_frame = tk.Frame(row_frame)
        actions_frame.pack(side="right", padx=10)
        
        folder_button = tk.Button(actions_frame, text="📁", relief="flat", cursor="hand2")
        folder_button.pack(side="left")

        play_button = tk.Button(actions_frame, text="▶️", relief="flat", cursor="hand2")
        play_button.pack(side="left")

        obs_button = tk.Button(actions_frame, text="Obs", font=("Arial", 8), width=4,
                               command=lambda eq=eqpto: self._abrir_janela_obs(eq))
        obs_button.pack(side="left")

        concluir_button = tk.Button(actions_frame, text="Concluir", font=("Arial", 9),
                                    command=lambda eq=eqpto: self._concluir_equipamento(eq))
        concluir_button.pack(side="left")
        
        self.linhas_widgets[eqpto] = { "check_var": check_var }


if __name__ == '__main__':
    class DummyController(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Teste do Módulo de Ajustes")
            self.geometry("1400x600")

        def show_frame(self, page_name):
            print(f"Simulando navegação para: {page_name}")
            self.destroy()

    app = DummyController()
    ajustes_frame = AjustesFrame(app, app)
    ajustes_frame.pack(fill="both", expand=True)
    app.mainloop()
