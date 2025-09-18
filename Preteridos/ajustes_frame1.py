import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

# --- Configurações ---
FONTE_PADRAO = ("Times New Roman", 12)
# Caminho para o banco de dados (deve ser o mesmo dos outros módulos)
diretorio_local_ativo = r'C:\BD_APP_Cemig'
nome_arquivo_bd = 'Primeiro_banco.db'
caminho_bd_ativo = os.path.join(diretorio_local_ativo, nome_arquivo_bd)


class AjustesFrame(tk.Frame):
    """
    Tela para exibir a lista de equipamentos pendentes de ajuste,
    buscando os dados de forma persistente do banco de dados.
    """
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

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
        
        # --- Botão de Atualizar ---
        btn_atualizar = ttk.Button(frame_superior, text="Atualizar Lista",
                                   command=self.carregar_equipamentos_pendentes)
        btn_atualizar.pack(side='right', anchor='ne')

        # --- Container Principal ---
        main_container = tk.LabelFrame(self, text="AJUSTES PENDENTES", font=("Helvetica", 16, "bold"), padx=20, pady=20)
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # --- Frame para a lista de equipamentos com scrollbar ---
        list_frame = tk.Frame(main_container)
        list_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        self.listbox_equipamentos = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set,
            font=FONTE_PADRAO,
            height=15
        )
        scrollbar.config(command=self.listbox_equipamentos.yview)

        scrollbar.pack(side="right", fill="y")
        self.listbox_equipamentos.pack(side="left", fill="both", expand=True)

        # --- Espaço inferior (semelhante à imagem) ---
        bottom_frame = tk.Frame(main_container, height=200, bd=1, relief="solid")
        bottom_frame.pack(fill='x', expand=False, pady=(10, 0))
        bottom_frame.pack_propagate(False) # Impede que o frame encolha
        tk.Label(bottom_frame, text="Detalhes do equipamento selecionado aparecerão aqui.", font=FONTE_PADRAO, fg="grey").pack(pady=20)

    def carregar_equipamentos_pendentes(self):
        """
        Lê a tabela 'ajustes' do banco de dados e popula a lista na tela.
        """
        # Limpa a lista atual antes de carregar novos dados
        self.listbox_equipamentos.delete(0, tk.END)

        if not os.path.exists(caminho_bd_ativo):
            messagebox.showwarning("Banco de Dados", "Arquivo de banco de dados não encontrado.", parent=self)
            return

        try:
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                # Busca todos os equipamentos da tabela 'ajustes', ordenando pelos mais recentes
                cursor.execute("SELECT eqpto FROM ajustes ORDER BY data_adicao DESC")
                equipamentos = cursor.fetchall()
                
                for eq in equipamentos:
                    self.listbox_equipamentos.insert(tk.END, f"  {eq[0]}")

        except sqlite3.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível carregar a lista de ajustes: {e}", parent=self)

if __name__ == '__main__':
    class DummyController(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Teste do Módulo de Ajustes")
            self.geometry("800x600")

        def show_frame(self, page_name):
            print(f"Simulando navegação para: {page_name}")
            self.destroy()

    app = DummyController()
    ajustes_frame = AjustesFrame(app, app)
    ajustes_frame.pack(fill="both", expand=True)
    app.mainloop()
