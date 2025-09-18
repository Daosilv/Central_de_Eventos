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
        self.geometry("400x400")
        self.minsize(300, 250)
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)

        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="Cole a lista de itens abaixo (um por linha):", font=FONTE_PADRAO).pack(side="top", anchor="w")

        button_frame = tk.Frame(main_frame)
        button_frame.pack(side="bottom", fill="x", pady=(5,0))
        
        text_frame = tk.Frame(main_frame, bd=1, relief="solid")
        text_frame.pack(side="top", fill="both", expand=True, pady=5)
        
        self.text_widget = tk.Text(text_frame, wrap="word", font=FONTE_PADRAO)
        self.text_widget.pack(fill="both", expand=True, padx=2, pady=2)

        ttk.Button(button_frame, text="Adicionar", command=self.adicionar).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side="right")
        
        self.wait_window(self)

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
        self.controller = controller
        
        notebook = ttk.Notebook(self)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)

        tab1 = TabListasGerais(notebook, controller)
        tab2 = TabHierarquia(notebook, controller)
        tab3 = TabCabos(notebook, controller)

        notebook.add(tab1, text='Listas Gerais')
        notebook.add(tab2, text='Hierarquia (Fabricante/Modelo/Comando)')
        notebook.add(tab3, text='Cabos Críticos')

class TabListasGerais(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.id_map = {}
        self.criar_widgets()
        self.carregar_categorias()

    def criar_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        frame_superior = tk.LabelFrame(self, text="Gerenciar Opções das Listas Simples", padx=10, pady=10)
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

        ttk.Button(botoes_frame, text="Adicionar", width=15, style="Gestao.TButton", command=self.adicionar_opcao).pack(pady=5, fill='x')
        ttk.Button(botoes_frame, text="Editar", width=15, style="Gestao.TButton", command=self.editar_opcao).pack(pady=5, fill='x')
        ttk.Button(botoes_frame, text="Remover", width=15, style="Gestao.TButton", command=self.remover_opcao).pack(pady=5, fill='x')
        ttk.Button(botoes_frame, text="Remover Tudo", width=15, style="Gestao.TButton", command=self.remover_todas_opcoes).pack(pady=(15, 5), fill='x')

    def carregar_categorias(self):
        categorias = self.controller.get_categorias_gerais()
        self.combo_categorias['values'] = categorias
        if categorias:
            self.combo_categorias.set(categorias[0])
            self.carregar_opcoes()

    def carregar_opcoes(self, event=None):
        categoria = self.combo_categorias.get()
        if not categoria: return
        self.listbox_opcoes.delete(0, tk.END)
        self.id_map.clear()
        opcoes = self.controller.get_opcoes_por_categoria_geral(categoria)
        for item in opcoes:
            self.listbox_opcoes.insert(tk.END, item['valor'])
            self.id_map[self.listbox_opcoes.size() - 1] = item['id']

    def adicionar_opcao(self):
        categoria = self.combo_categorias.get()
        if not categoria:
            messagebox.showwarning("Atenção", "Selecione uma categoria.", parent=self)
            return
        novo_valor = simpledialog.askstring("Adicionar", f"Novo valor para '{categoria}':", parent=self)
        if novo_valor and novo_valor.strip():
            self.controller.adicionar_opcao_geral(categoria, novo_valor.strip())
            self.carregar_opcoes()
    
    def editar_opcao(self):
        idx = self.listbox_opcoes.curselection()
        if not idx:
            messagebox.showwarning("Atenção", "Selecione uma opção para editar.", parent=self)
            return
        id_opcao = self.id_map[idx[0]]
        valor_atual = self.listbox_opcoes.get(idx[0])
        novo_valor = simpledialog.askstring("Editar", "Novo valor:", initialvalue=valor_atual, parent=self)
        if novo_valor and novo_valor.strip():
            self.controller.editar_opcao_geral(id_opcao, novo_valor.strip())
            self.carregar_opcoes()
            
    def remover_opcao(self):
        idx = self.listbox_opcoes.curselection()
        if not idx:
            messagebox.showwarning("Atenção", "Selecione uma opção para remover.", parent=self)
            return
        id_opcao = self.id_map[idx[0]]
        if messagebox.askyesno("Confirmar", "Deseja remover a opção selecionada?", parent=self):
            self.controller.deletar_opcao_geral(id_opcao)
            self.carregar_opcoes()

    def remover_todas_opcoes(self):
        categoria = self.combo_categorias.get()
        if not categoria:
            messagebox.showwarning("Atenção", "Selecione uma categoria.", parent=self)
            return
        if messagebox.askyesno("Confirmar Remoção Total", f"Tem certeza que deseja remover TODAS as opções da categoria '{categoria}'?", icon='warning', parent=self):
            self.controller.deletar_opcoes_por_categoria_geral(categoria)
            self.carregar_opcoes()

class TabHierarquia(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.criar_widgets()
        self.carregar_hierarquia()

    def criar_widgets(self):
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        tree_frame = tk.LabelFrame(main_frame, text="Estrutura")
        tree_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, columns=('valor'), show='tree headings')
        self.tree.heading('#0', text='Item')
        self.tree.heading('valor', text='Categoria')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

        botoes_frame = tk.Frame(main_frame)
        botoes_frame.grid(row=0, column=1, sticky="ns")

        self.btn_add_fab = ttk.Button(botoes_frame, text="Adicionar Fabricante", command=lambda: self.adicionar_item('fabricante'))
        self.btn_add_fab.pack(pady=5, fill='x')
        self.btn_add_mod = ttk.Button(botoes_frame, text="Adicionar Modelo", command=lambda: self.adicionar_item('modelo'), state='disabled')
        self.btn_add_mod.pack(pady=5, fill='x')
        self.btn_add_com = ttk.Button(botoes_frame, text="Adicionar Comando", command=lambda: self.adicionar_item('comando'), state='disabled')
        self.btn_add_com.pack(pady=5, fill='x')
        ttk.Separator(botoes_frame, orient='horizontal').pack(pady=10, fill='x')
        self.btn_edit = ttk.Button(botoes_frame, text="Editar Selecionado", state='disabled', command=self.editar_item)
        self.btn_edit.pack(pady=5, fill='x')
        self.btn_del = ttk.Button(botoes_frame, text="Remover Selecionado", state='disabled', command=self.remover_item)
        self.btn_del.pack(pady=5, fill='x')

    def carregar_hierarquia(self, parent_node="", id_pai=None):
        if parent_node == "":
            self.tree.delete(*self.tree.get_children())
        
        items = self.controller.get_opcoes_hierarquicas(id_pai)
        for item in items:
            node_id = self.tree.insert(parent_node, 'end', iid=item['id'], text=item['valor'], values=(item['categoria'].title(),))
            self.carregar_hierarquia(node_id, item['id'])

    def on_tree_select(self, event):
        selected_id = self.tree.focus()
        if not selected_id:
            self.btn_add_mod.config(state='disabled')
            self.btn_add_com.config(state='disabled')
            self.btn_edit.config(state='disabled')
            self.btn_del.config(state='disabled')
            return

        self.btn_edit.config(state='normal')
        self.btn_del.config(state='normal')
        
        item = self.tree.item(selected_id)
        categoria = item['values'][0].lower()

        if categoria == 'fabricante':
            self.btn_add_mod.config(state='normal')
            self.btn_add_com.config(state='disabled')
        elif categoria == 'modelo':
            self.btn_add_mod.config(state='disabled')
            self.btn_add_com.config(state='normal')
        else:
            self.btn_add_mod.config(state='disabled')
            self.btn_add_com.config(state='disabled')

    def adicionar_item(self, categoria):
        id_pai = None
        prompt = f"Novo valor para {categoria.title()}:"
        
        if categoria != 'fabricante':
            selected_id = self.tree.focus()
            if not selected_id:
                messagebox.showerror("Erro", "Nenhum item pai selecionado.", parent=self)
                return
            id_pai = int(selected_id)

        novo_valor = simpledialog.askstring("Adicionar Item", prompt, parent=self)
        if novo_valor and novo_valor.strip():
            self.controller.adicionar_opcao_hierarquica(categoria, novo_valor.strip(), id_pai)
            self.carregar_hierarquia()
            
    def editar_item(self):
        selected_id = self.tree.focus()
        if not selected_id: return
        
        valor_atual = self.tree.item(selected_id, 'text')
        novo_valor = simpledialog.askstring("Editar", "Novo valor:", initialvalue=valor_atual, parent=self)
        if novo_valor and novo_valor.strip():
            self.controller.editar_opcao_hierarquica(int(selected_id), novo_valor.strip())
            self.carregar_hierarquia()
            
    def remover_item(self):
        selected_id = self.tree.focus()
        if not selected_id: return
        
        if messagebox.askyesno("Confirmar", "Deseja remover o item e todos os seus filhos?", icon='warning', parent=self):
            self.controller.deletar_opcao_hierarquica(int(selected_id))
            self.carregar_hierarquia()

class TabCabos(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.criar_widgets()
        self.carregar_cabos()

    def criar_widgets(self):
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        tree_frame = tk.LabelFrame(main_frame, text="Propriedades dos Cabos Críticos")
        tree_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree = ttk.Treeview(tree_frame, columns=('trecho', 'nominal', 'admissivel'), show='headings')
        self.tree.heading('trecho', text='Trecho')
        self.tree.heading('nominal', text='Nominal (A)')
        self.tree.heading('admissivel', text='Admissível (A)')
        self.tree.pack(fill='both', expand=True)

        botoes_frame = tk.Frame(main_frame)
        botoes_frame.grid(row=0, column=1, sticky="ns")

        ttk.Button(botoes_frame, text="Adicionar Cabo", command=self.adicionar_cabo).pack(pady=5, fill='x')
        ttk.Button(botoes_frame, text="Editar Cabo", command=self.editar_cabo).pack(pady=5, fill='x')
        ttk.Button(botoes_frame, text="Remover Cabo", command=self.remover_cabo).pack(pady=5, fill='x')

    def carregar_cabos(self):
        self.tree.delete(*self.tree.get_children())
        cabos = self.controller.get_todos_cabos()
        for cabo in cabos:
            self.tree.insert('', 'end', iid=cabo['id'], values=(cabo['trecho'], cabo['nominal'], cabo['admissivel']))

    def adicionar_cabo(self):
        dialog = CaboDialog(self, title="Adicionar Cabo")
        if dialog.result:
            trecho, nominal, admissivel = dialog.result
            self.controller.adicionar_cabo(trecho, nominal, admissivel)
            self.carregar_cabos()
            
    def editar_cabo(self):
        selected_id = self.tree.focus()
        if not selected_id:
            messagebox.showwarning("Atenção", "Selecione um cabo para editar.", parent=self)
            return
        
        item = self.tree.item(selected_id, 'values')
        dialog = CaboDialog(self, title="Editar Cabo", initial_data=item)
        if dialog.result:
            trecho, nominal, admissivel = dialog.result
            self.controller.editar_cabo(int(selected_id), trecho, nominal, admissivel)
            self.carregar_cabos()

    def remover_cabo(self):
        selected_id = self.tree.focus()
        if not selected_id:
            messagebox.showwarning("Atenção", "Selecione um cabo para remover.", parent=self)
            return
        
        if messagebox.askyesno("Confirmar", "Deseja remover o cabo selecionado?", parent=self):
            self.controller.deletar_cabo(int(selected_id))
            self.carregar_cabos()

class CaboDialog(tk.Toplevel):
    def __init__(self, parent, title, initial_data=None):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.transient(parent)
        self.grab_set()

        frame = tk.Frame(self, padx=15, pady=15)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Trecho:").grid(row=0, column=0, sticky='w', pady=2)
        self.trecho_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.trecho_var, width=30).grid(row=0, column=1, sticky='ew')
        
        tk.Label(frame, text="Nominal (A):").grid(row=1, column=0, sticky='w', pady=2)
        self.nominal_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.nominal_var, width=30).grid(row=1, column=1, sticky='ew')

        tk.Label(frame, text="Admissível (A):").grid(row=2, column=0, sticky='w', pady=2)
        self.admissivel_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.admissivel_var, width=30).grid(row=2, column=1, sticky='ew')
        
        if initial_data:
            self.trecho_var.set(initial_data[0])
            self.nominal_var.set(initial_data[1])
            self.admissivel_var.set(initial_data[2])

        button_frame = tk.Frame(frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10,0))
        ttk.Button(button_frame, text="Salvar", command=self.on_save).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side='left', padx=5)

        self.wait_window(self)

    def on_save(self):
        trecho = self.trecho_var.get().strip()
        nominal = self.nominal_var.get().strip()
        admissivel = self.admissivel_var.get().strip()

        if not trecho:
            messagebox.showerror("Erro", "O campo 'Trecho' é obrigatório.", parent=self)
            return
        
        self.result = (trecho, nominal, admissivel)
        self.destroy()
