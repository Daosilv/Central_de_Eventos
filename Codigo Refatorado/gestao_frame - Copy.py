import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

FONTE_PADRAO = ("Times New Roman", 12)

class GestaoFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent_window = parent
        self.controller = controller
        self.id_map = {}
        self.criar_widgets()
        self.carregar_categorias()
        
    def criar_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Frame Superior (Seleção de Categoria) ---
        frame_superior = tk.LabelFrame(self, text="Gerenciar Opções das Listas", padx=10, pady=10)
        frame_superior.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        frame_superior.grid_columnconfigure(1, weight=1)

        tk.Label(frame_superior, text="Selecione a Categoria:", font=FONTE_PADRAO).grid(row=0, column=0, padx=(0, 5), sticky='w')
        self.combo_categorias = ttk.Combobox(frame_superior, state="readonly", font=FONTE_PADRAO)
        self.combo_categorias.grid(row=0, column=1, sticky="ew")
        self.combo_categorias.bind("<<ComboboxSelected>>", self.carregar_opcoes)

        # --- Frame Central (Lista de Opções e Botões de Ação) ---
        frame_central = tk.Frame(self)
        frame_central.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        frame_central.grid_rowconfigure(0, weight=1)
        frame_central.grid_columnconfigure(0, weight=1)

        # --- Lista ---
        list_frame = tk.LabelFrame(frame_central, text="Opções", padx=5, pady=5)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.listbox_opcoes = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=FONTE_PADRAO)
        self.listbox_opcoes.grid(row=0, column=0, sticky='nsew')
        scrollbar.config(command=self.listbox_opcoes.yview)

        # --- Botões ---
        botoes_frame = tk.Frame(frame_central)
        botoes_frame.grid(row=0, column=1, sticky="ns")

        style = ttk.Style()
        style.configure("Gestao.TButton", font=("Times New Roman", 11), padding=5)

        btn_adicionar = ttk.Button(botoes_frame, text="Adicionar", width=12, style="Gestao.TButton", command=self.adicionar_opcao)
        btn_adicionar.pack(pady=5, fill='x')

        btn_editar = ttk.Button(botoes_frame, text="Editar", width=12, style="Gestao.TButton", command=self.editar_opcao)
        btn_editar.pack(pady=5, fill='x')

        btn_remover = ttk.Button(botoes_frame, text="Remover", width=12, style="Gestao.TButton", command=self.remover_opcao)
        btn_remover.pack(pady=5, fill='x')
        
        btn_fechar = ttk.Button(self, text="Fechar Módulo", command=self.parent_window.destroy)
        btn_fechar.grid(row=2, column=0, padx=10, pady=10, sticky="e")

    def carregar_categorias(self):
        categorias = self.controller.get_categorias()
        self.combo_categorias['values'] = categorias
        if categorias:
            self.combo_categorias.set(categorias[0])
            self.carregar_opcoes()

    def carregar_opcoes(self, event=None):
        categoria_selecionada = self.combo_categorias.get()
        if not categoria_selecionada:
            return

        self.listbox_opcoes.delete(0, tk.END)
        self.id_map.clear()
        
        opcoes = self.controller.get_opcoes_por_categoria(categoria_selecionada)
        if opcoes:
            for item in opcoes:
                id_opcao, valor = item['id'], item['valor']
                self.listbox_opcoes.insert(tk.END, valor)
                self.id_map[self.listbox_opcoes.size() - 1] = id_opcao

    def adicionar_opcao(self):
        categoria = self.combo_categorias.get()
        if not categoria:
            messagebox.showwarning("Nenhuma Categoria", "Por favor, selecione uma categoria primeiro.", parent=self.parent_window)
            return

        novo_valor = simpledialog.askstring("Adicionar Opção", f"Digite o novo valor para a categoria '{categoria}':", parent=self.parent_window)
        if novo_valor and novo_valor.strip():
            self.controller.adicionar_opcao(categoria, novo_valor.strip())
            self.carregar_opcoes()
            messagebox.showinfo("Sucesso", "Opção adicionada com sucesso!", parent=self.parent_window)
        elif novo_valor is not None:
             messagebox.showerror("Erro", "O valor não pode ser vazio.", parent=self.parent_window)

    def editar_opcao(self):
        indices_selecionados = self.listbox_opcoes.curselection()
        if not indices_selecionados:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione uma opção para editar.", parent=self.parent_window)
            return
        
        index = indices_selecionados[0]
        id_opcao = self.id_map.get(index)
        valor_atual = self.listbox_opcoes.get(index)

        novo_valor = simpledialog.askstring("Editar Opção", "Digite o novo valor:", initialvalue=valor_atual, parent=self.parent_window)

        if novo_valor and novo_valor.strip():
            self.controller.editar_opcao(id_opcao, novo_valor.strip())
            self.carregar_opcoes()
            messagebox.showinfo("Sucesso", "Opção editada com sucesso!", parent=self.parent_window)
        elif novo_valor is not None:
             messagebox.showerror("Erro", "O valor não pode ser vazio.", parent=self.parent_window)
    
    def remover_opcao(self):
        indices_selecionados = self.listbox_opcoes.curselection()
        if not indices_selecionados:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione uma opção para remover.", parent=self.parent_window)
            return

        index = indices_selecionados[0]
        id_opcao = self.id_map.get(index)
        valor_selecionado = self.listbox_opcoes.get(index)

        if messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover a opção '{valor_selecionado}'?", parent=self.parent_window):
            self.controller.deletar_opcao(id_opcao)
            self.carregar_opcoes()
            messagebox.showinfo("Sucesso", "Opção removida com sucesso!", parent=self.parent_window)
