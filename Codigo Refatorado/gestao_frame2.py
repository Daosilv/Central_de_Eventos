import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

FONTE_PADRAO = ("Times New Roman", 12)

class MultiAddDialog(tk.Toplevel):
    def __init__(self, parent, categoria):
        super().__init__(parent)
        self.parent = parent
        self.categoria = categoria
        self.result = None

        self.title(f"Adicionar Múltiplos em '{self.categoria}'")
        self.geometry("400x400") # Aumentei a altura padrão
        self.minsize(300, 250)   # Defini um tamanho mínimo
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True) # Agora a janela é redimensionável

        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="Cole a lista de itens abaixo (um por linha):", font=FONTE_PADRAO).pack(side="top", anchor="w")

        # --- LÓGICA DE LAYOUT CORRIGIDA ---
        # 1. Criar o frame dos botões primeiro
        button_frame = tk.Frame(main_frame)
        # 2. Empacotar o frame dos botões na parte de baixo da janela (footer)
        button_frame.pack(side="bottom", fill="x", pady=(5,0))
        
        # 3. Criar e empacotar o frame do texto para preencher o espaço restante
        text_frame = tk.Frame(main_frame, bd=1, relief="solid")
        text_frame.pack(side="top", fill="both", expand=True, pady=5)
        
        self.text_widget = tk.Text(text_frame, wrap="word", font=FONTE_PADRAO)
        self.text_widget.pack(fill="both", expand=True, padx=2, pady=2)

        # 4. Adicionar os botões ao frame de botões (que já está no lugar certo)
        ttk.Button(button_frame, text="Adicionar", command=self.adicionar).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side="right")
        # --- FIM DA CORREÇÃO ---

    def adicionar(self):
        texto = self.text_widget.get("1.0", "end-1c")
        self.result = [line.strip() for line in texto.splitlines() if line.strip()]
        
        if not self.result:
            messagebox.showwarning("Nenhum item", "A lista está vazia.", parent=self)
            return

        self.destroy()

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

        frame_superior = tk.LabelFrame(self, text="Gerenciar Opções das Listas", padx=10, pady=10)
        frame_superior.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        frame_superior.grid_columnconfigure(1, weight=1)

        tk.Label(frame_superior, text="Selecione a Categoria:", font=FONTE_PADRAO).grid(row=0, column=0, padx=(0, 5), sticky='w')
        self.combo_categorias = ttk.Combobox(frame_superior, state="readonly", font=FONTE_PADRAO)
        self.combo_categorias.grid(row=0, column=1, sticky="ew")
        self.combo_categorias.bind("<<ComboboxSelected>>", self.carregar_opcoes)

        frame_central = tk.Frame(self)
        frame_central.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        frame_central.grid_rowconfigure(0, weight=1)
        frame_central.grid_columnconfigure(0, weight=1)

        list_frame = tk.LabelFrame(frame_central, text="Opções", padx=5, pady=5)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky='ns')
        self.listbox_opcoes = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=FONTE_PADRAO)
        self.listbox_opcoes.grid(row=0, column=0, sticky='nsew')
        scrollbar.config(command=self.listbox_opcoes.yview)

        botoes_frame = tk.Frame(frame_central)
        botoes_frame.grid(row=0, column=1, sticky="ns")

        style = ttk.Style()
        style.configure("Gestao.TButton", font=("Times New Roman", 11), padding=5)

        btn_adicionar = ttk.Button(botoes_frame, text="Adicionar", width=15, style="Gestao.TButton", command=self.adicionar_opcao)
        btn_adicionar.pack(pady=5, fill='x')

        btn_adicionar_multiplos = ttk.Button(botoes_frame, text="Adicionar Múltiplos", width=15, style="Gestao.TButton", command=self.adicionar_multiplas_opcoes)
        btn_adicionar_multiplos.pack(pady=5, fill='x')

        btn_editar = ttk.Button(botoes_frame, text="Editar", width=15, style="Gestao.TButton", command=self.editar_opcao)
        btn_editar.pack(pady=5, fill='x')

        btn_remover = ttk.Button(botoes_frame, text="Remover", width=15, style="Gestao.TButton", command=self.remover_opcao)
        btn_remover.pack(pady=5, fill='x')
        
        btn_remover_tudo = ttk.Button(botoes_frame, text="Remover Tudo", width=15, style="Gestao.TButton", command=self.remover_todas_opcoes)
        btn_remover_tudo.pack(pady=(15, 5), fill='x')
        
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

    def adicionar_multiplas_opcoes(self):
        categoria = self.combo_categorias.get()
        if not categoria:
            messagebox.showwarning("Nenhuma Categoria", "Por favor, selecione uma categoria primeiro.", parent=self.parent_window)
            return

        dialog = MultiAddDialog(self.parent_window, categoria)
        self.parent_window.wait_window(dialog)

        if dialog.result:
            count = 0
            for valor in dialog.result:
                self.controller.adicionar_opcao(categoria, valor)
                count += 1
            
            self.carregar_opcoes()
            messagebox.showinfo("Sucesso", f"{count} opções foram adicionadas com sucesso!", parent=self.parent_window)

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

    def remover_todas_opcoes(self):
        categoria = self.combo_categorias.get()
        if not categoria:
            messagebox.showwarning("Nenhuma Categoria", "Por favor, selecione uma categoria para remover.", parent=self.parent_window)
            return

        confirm = messagebox.askyesno(
            "Confirmar Remoção em Massa",
            f"ATENÇÃO!\n\nVocê tem certeza que deseja remover TODAS as opções da categoria '{categoria}'?\n\nEsta ação não pode ser desfeita.",
            icon='warning',
            parent=self.parent_window
        )

        if confirm:
            self.controller.deletar_opcoes_por_categoria(categoria)
            self.carregar_opcoes()
            messagebox.showinfo("Sucesso", f"Todas as opções da categoria '{categoria}' foram removidas.", parent=self.parent_window)
