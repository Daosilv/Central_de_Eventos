import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import sys

# --- Configurações ---
FONTE_PADRAO = ("Times New Roman", 12)
FONTE_PEQUENA = ("Times New Roman", 10)
SIDEBAR_WIDTH = 300 

class MemorialCalculoFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent_window = parent

        style = ttk.Style()
        style.configure('.', background='white', foreground='black')
        # Mantém a configuração para o fundo da lista suspensa
        style.configure('TListbox', selectbackground='white', selectforeground='black')
        
        style.layout('Arrowless.TCombobox',
            [('Combobox.padding', {'expand': '1', 'sticky': 'nswe', 'children':
                [('Combobox.focus', {'expand': '1', 'sticky': 'nswe', 'children':
                    [('Combobox.text', {'sticky': 'nswe'})]
                })]
            })]
        )
        style.configure("TCombobox", justify="center")
        
        self.busca_ajustes_var = tk.StringVar()
        self.lista_ajustes_completa = []
        self.busca_ajustes_var.trace_add("write", self._filtrar_ajustes_recentes)
        self.busca_rascunhos_var = tk.StringVar()
        self.lista_rascunhos_completa = []
        self.rascunho_check_vars = {} 
        self.selecionar_tudo_rascunhos_var = tk.BooleanVar()
        self.busca_rascunhos_var.trace_add("write", lambda *args: self.atualizar_lista_rascunhos())
        
        self.campos_dict = { "Autor": tk.StringVar(), "Eqpto": tk.StringVar(), "Malha": tk.StringVar(), "Condição": tk.StringVar(), "Motivador": tk.StringVar(), "Alimentador": tk.StringVar(), "NS": tk.StringVar(), "Siom": tk.StringVar(), "Data": tk.StringVar(value=datetime.now().strftime('%d/%m/%Y')), "Coord": tk.StringVar(), "Endereço": tk.StringVar(), "Mídia": tk.StringVar(), "Fabricante": tk.StringVar(), "Modelo": tk.StringVar(), "Comando": tk.StringVar(), "Telecontrolado": tk.StringVar(value="sim"), "Bypass_1": tk.StringVar(), "Bypass_2": tk.StringVar() }
        self.campos_dict["Condição"].trace_add("write", self._gerenciar_bloco_tabelas_replicado)
        self.vars_grupos = {}
        self.col_widths = [90, 70, 85, 120, 120, 70, 85, 120, 120]
        self.tabelas_grupo_frames = []
        self.ref_cells = []
        self.vars_grupos_rep = {}
        self.tabelas_grupo_frames_rep = []
        self.ref_cells_rep = []
        self.frame_tabela_header = None
        self.frame_tabela_header_rep = None
        self.vcmd_4 = self.register(self.limitar_4_caracteres)
        self.campos_dict["Siom"].trace_add("write", self.formatar_siom)
        self.campos_dict["Coord"].trace_add("write", self.formatar_coord)
        self.criar_layout_principal()
        self.criar_layout_formulario()
        if 'grupo_1' in self.vars_grupos and 'grupo_3' in self.vars_grupos:
            self.vars_grupos['grupo_1']['sequencia'].trace_add("write", self._replicar_sequencia_g1_para_g3)
        self.atualizar_todas_as_listas()

    @staticmethod
    def get_db_columns():
        """Método estático para que o Controller possa saber as colunas sem instanciar a View."""
        colunas_dict = { "Autor": "", "Eqpto": "", "Malha": "", "Condição": "", "Motivador": "", "Alimentador": "", "NS": "", "Siom": "", "Data": "", "Coord": "", "Endereço": "", "Mídia": "", "Fabricante": "", "Modelo": "", "Comando": "", "Telecontrolado": "", "Bypass_1": "", "Bypass_2": "" }
        colunas_db = list(colunas_dict.keys())
        for i in range(1, 4):
            for campo in ["pickup_fase", "sequencia", "curva_lenta_tipo", "curva_lenta_dial", "curva_lenta_tadic", "curva_rapida_dial", "curva_rapida_tadic", "pickup_terra", "sequencia_terra", "terra_tempo_lenta", "terra_tempo_rapida"]:
                colunas_db.append(f'g{i}_{campo}')
        colunas_db.append('observacoes')
        return colunas_db

    def criar_layout_principal(self):
        self.configure(bg='white')
        scroll_container = tk.Frame(self, bg='white')
        scroll_container.pack(fill="both", expand=True)
        scroll_container.grid_rowconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(scroll_container, highlightthickness=0, bg='white')
        v_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(scroll_container, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.content_holder_frame = tk.Frame(self.canvas, bg='white')
        self.canvas_window_id = self.canvas.create_window((0, 0), window=self.content_holder_frame, anchor="nw")
        
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.content_holder_frame.bind("<Configure>", self.on_frame_configure)

        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        self.content_holder_frame.grid_columnconfigure(0, weight=1)
        self.content_holder_frame.grid_columnconfigure(1, weight=0)
        self.main_form_frame = tk.Frame(self.content_holder_frame, bd=1, bg='white')
        self.main_form_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        sidebar_frame = tk.LabelFrame(self.content_holder_frame, text="Histórico", width=SIDEBAR_WIDTH, padx=5, pady=5, bg='white')
        sidebar_frame.grid(row=0, column=1, sticky="nsew", pady=10)
        sidebar_frame.pack_propagate(False)
        btn_atualizar_listas = ttk.Button(sidebar_frame, text="Atualizar Listas", command=self.atualizar_todas_as_listas)
        btn_atualizar_listas.pack(fill='x', pady=(0, 10))
        ajustes_container = tk.LabelFrame(sidebar_frame, text="Ajustes Recentes", padx=5, pady=5, bg='white'); ajustes_container.pack(fill='both', expand=True, pady=(0, 5))
        frame_busca_ajustes = tk.Frame(ajustes_container, bg='white'); frame_busca_ajustes.pack(fill='x')
        tk.Label(frame_busca_ajustes, text="Buscar:", bg='white').pack(side='left')
        tk.Entry(frame_busca_ajustes, textvariable=self.busca_ajustes_var).pack(side='left', fill='x', expand=True, padx=5)
        frame_local_list = tk.Frame(ajustes_container, bg='white'); frame_local_list.pack(fill='both', expand=True, pady=(5,0))
        scrollbar_local = ttk.Scrollbar(frame_local_list); scrollbar_local.pack(side='right', fill='y')
        self.listbox_local = tk.Listbox(frame_local_list, yscrollcommand=scrollbar_local.set); self.listbox_local.pack(side='left', fill='both', expand=True)
        scrollbar_local.config(command=self.listbox_local.yview)
        self.listbox_local.bind("<Double-1>", self.carregar_ficha_selecionada)
        rascunhos_container = tk.LabelFrame(sidebar_frame, text="Rascunhos", padx=5, pady=5, bg='white'); rascunhos_container.pack(fill='both', expand=True, pady=(5, 5))
        frame_busca_rascunhos = tk.Frame(rascunhos_container, bg='white'); frame_busca_rascunhos.pack(fill='x')
        tk.Label(frame_busca_rascunhos, text="Buscar:", bg='white').pack(side='left')
        tk.Entry(frame_busca_rascunhos, textvariable=self.busca_rascunhos_var).pack(side='left', fill='x', expand=True, padx=5)
        frame_rascunhos_actions = tk.Frame(rascunhos_container, bg='white'); frame_rascunhos_actions.pack(fill='x', pady=(5,0))
        ttk.Checkbutton(frame_rascunhos_actions, text="Selecionar Tudo", variable=self.selecionar_tudo_rascunhos_var, command=self._toggle_selecionar_tudo_rascunhos).pack(side='left')
        tk.Button(frame_rascunhos_actions, text="X", fg="red", font=("Helvetica", 10, "bold"), command=self.deletar_rascunhos_selecionados, width=2, relief="flat", cursor="hand2", bg='white').pack(side='right', padx=(0,5))
        rascunhos_canvas_frame = tk.Frame(rascunhos_container, bg='white'); rascunhos_canvas_frame.pack(fill='both', expand=True, pady=5)
        self.rascunhos_canvas = tk.Canvas(rascunhos_canvas_frame, highlightthickness=0, bg='white')
        rascunhos_scrollbar = ttk.Scrollbar(rascunhos_canvas_frame, orient="vertical", command=self.rascunhos_canvas.yview)
        self.rascunhos_items_frame = tk.Frame(self.rascunhos_canvas, bg='white')
        self.rascunhos_canvas.create_window((0, 0), window=self.rascunhos_items_frame, anchor="nw")
        self.rascunhos_canvas.configure(yscrollcommand=rascunhos_scrollbar.set)
        rascunhos_scrollbar.pack(side="right", fill="y"); self.rascunhos_canvas.pack(side="left", fill="both", expand=True)
        self.rascunhos_items_frame.bind("<Configure>", lambda e: self.rascunhos_canvas.configure(scrollregion=self.rascunhos_canvas.bbox("all")))

    def on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window_id, width=canvas_width)

    def criar_layout_formulario(self):
        frame_campos = tk.Frame(self.main_form_frame, bg='white')
        frame_campos.pack(pady=10, padx=10, fill="x")
        wrap_tabelas = tk.Frame(self.main_form_frame, bg='white')
        wrap_tabelas.pack(pady=10, anchor="center")
        btn_voltar = ttk.Button(frame_campos, text="< Fechar Módulo", command=self.parent_window.destroy)
        btn_voltar.pack(anchor='nw', pady=(0, 10))
        row1_frame = tk.Frame(frame_campos, bg='white'); row1_frame.pack(fill="x", pady=1)
        tk.Label(row1_frame, text="Autor", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        tk.Entry(row1_frame, textvariable=self.campos_dict["Autor"], relief="solid", bd=1, font=FONTE_PADRAO, width=40).pack(side="left", padx=(0,5))
        tk.Label(row1_frame, text="Data", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        tk.Entry(row1_frame, textvariable=self.campos_dict["Data"], relief="solid", bd=1, font=FONTE_PADRAO, width=11).pack(side="left", padx=(0,5))
        tk.Label(row1_frame, text="NS", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        tk.Entry(row1_frame, textvariable=self.campos_dict["NS"], relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left", padx=(0,5))
        row2_frame = tk.Frame(frame_campos, bg='white'); row2_frame.pack(fill="x", pady=1)
        tk.Label(row2_frame, text="Eqpto", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        tk.Entry(row2_frame, textvariable=self.campos_dict["Eqpto"], relief="solid", bd=1, font=FONTE_PADRAO, width=10).pack(side="left", padx=(0,5))
        opcoes_condicao = ["", "Acess Inv", "Acess s/Inv", "NA", "NF", "NA ABR", "NF LS", "P.O. NA", "P.O. NF", "P.O. SECC NA", "P.O. SECC NF", "SECC NA", "SECC NF", "PRIM", "SE RELI", "SE SECI", "MONOF. NF", "MONOF. NA", "MONOF. SECC NA", "MONOF. SECC NF"]
        tk.Label(row2_frame, text="Condição", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        self.create_bordered_combobox(row2_frame, self.campos_dict["Condição"], opcoes_condicao, 16).pack(side="left", padx=(0,5))
        tk.Label(row2_frame, text="Coord", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        tk.Entry(row2_frame, textvariable=self.campos_dict["Coord"], relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left", padx=(0,5))
        opcoes_malha = ["", "Centro", "Leste", "Mantiqueira", "Norte", "Sul"]
        tk.Label(row2_frame, text="Malha", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        self.create_bordered_combobox(row2_frame, self.campos_dict["Malha"], opcoes_malha, 16).pack(side="left", padx=(0,5))
        tk.Label(row2_frame, text="Alimentador", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        tk.Entry(row2_frame, textvariable=self.campos_dict["Alimentador"], relief="solid", bd=1, font=FONTE_PADRAO, width=10).pack(side="left", padx=(0,5))
        row3_frame = tk.Frame(frame_campos, bg='white'); row3_frame.pack(fill="x", pady=1)
        opcoes_motivador = ["", "Instalação", "Reajuste", "Relocação"]
        tk.Label(row3_frame, text="Motivador", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        self.create_bordered_combobox(row3_frame, self.campos_dict["Motivador"], opcoes_motivador, 14).pack(side="left", padx=(0,5))
        tk.Label(row3_frame, text="Endereço", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        tk.Entry(row3_frame, textvariable=self.campos_dict["Endereço"], relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left", padx=(0,5), fill="x", expand=True)
        opcoes_midia = ["", "Celular", "Satélite", "Rádio", "Desconhecido", "Não enc."]
        tk.Label(row3_frame, text="Mídia", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        self.create_bordered_combobox(row3_frame, self.campos_dict["Mídia"], opcoes_midia, 14).pack(side="left", padx=(0,5))
        row4_frame = tk.Frame(frame_campos, bg='white'); row4_frame.pack(fill="x", pady=1)
        opcoes_fabricante = ["", "ABB", "AMPERA", "ARTECHE", "BRUSH", "COOPER", "GeW", "HSS", "McGRAW_EDISON", "NOJA", "NU_LEC", "REYROLLE", "ROMAGNOLE", "SIEMENS", "SCHNEIDER", "TAVRIDA", "WESTINGHOUSE", "WHIPP_BOURNE", "DESCONHECIDO", "SC_ElectricCompany"]
        tk.Label(row4_frame, text="Fabricante", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        self.create_bordered_combobox(row4_frame, self.campos_dict["Fabricante"], opcoes_fabricante, 28).pack(side="left", padx=(0,5))
        tk.Label(row4_frame, text="Modelo", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        tk.Entry(row4_frame, textvariable=self.campos_dict["Modelo"], relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left", padx=(0,5))
        tk.Label(row4_frame, text="Comando", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        tk.Entry(row4_frame, textvariable=self.campos_dict["Comando"], relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left", padx=(0,5))
        opcoes_telecontrolado = ["", "sim", "não"]
        tk.Label(row4_frame, text="Telecontrolado", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        self.create_bordered_combobox(row4_frame, self.campos_dict["Telecontrolado"], opcoes_telecontrolado, 8).pack(side="left", padx=(0,5))
        tk.Label(row4_frame, text="Siom", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO, bg='white').pack(side="left")
        tk.Entry(row4_frame, textvariable=self.campos_dict["Siom"], relief="solid", bd=1, font=FONTE_PADRAO, width=10).pack(side="left", padx=(0,5))
        row_bypass_frame = tk.Frame(frame_campos, bg='white'); row_bypass_frame.pack(fill="x", pady=1)
        tk.Label(row_bypass_frame, text="Bypass", relief="solid", bd=1, font=FONTE_PADRAO, bg='white').pack(side="left")
        opcoes_bypass = ["", "6", "8", "10", "12", "15", "20", "25", "30"]
        bypass1_cell = tk.Frame(row_bypass_frame, relief="solid", bd=1, bg='white')
        bypass1_combo = ttk.Combobox(bypass1_cell, textvariable=self.campos_dict["Bypass_1"], values=opcoes_bypass, state="readonly", width=8, font=FONTE_PADRAO, style='Arrowless.TCombobox', justify="center")
        bypass1_combo.bind("<Button-1>", self.open_dropdown_on_click)
        bypass1_combo.bind("<<ComboboxSelected>>", self._remove_focus)
        bypass1_combo.pack(fill='both', expand=True); bypass1_cell.pack(side="left", padx=(0,2))
        tk.Label(row_bypass_frame, text="-", bd=0, font=FONTE_PADRAO, bg='white').pack(side="left", padx=2)
        tk.Entry(row_bypass_frame, textvariable=self.campos_dict["Bypass_2"], width=10, relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left")
        self._construir_bloco_tabelas(wrap_tabelas, self.vars_grupos, self.tabelas_grupo_frames, self.ref_cells, "original")
        botoes_frame = tk.Frame(self.main_form_frame, bg='white')
        botoes_frame.pack(pady=20)
        btn_buscar = ttk.Button(botoes_frame, text="Buscar", command=self.abrir_janela_busca)
        btn_buscar.pack(side="left", padx=5)
        btn_salvar_rascunho = ttk.Button(botoes_frame, text="Salvar Rascunho", command=self.salvar_rascunho)
        btn_salvar_rascunho.pack(side="left", padx=5)
        btn_salvar_enviar = ttk.Button(botoes_frame, text="Salvar e Enviar", command=self.salvar_e_enviar)
        btn_salvar_enviar.pack(side="left", padx=5)
        btn_limpar = ttk.Button(botoes_frame, text="Limpar", command=self.limpar_formulario)
        btn_limpar.pack(side="left", padx=5)
        frame_obs = tk.Frame(self.main_form_frame, bg='white')
        frame_obs.pack(pady=(10, 5), padx=10, fill='x', expand=False)
        lbl_obs = tk.Label(frame_obs, text="Observações:", font=FONTE_PADRAO, bg='white'); lbl_obs.pack(anchor='w')
        text_container = tk.Frame(frame_obs, height=120, relief="solid", bd=1); text_container.pack(fill='x', expand=False)
        text_container.pack_propagate(False)
        self.text_obs = tk.Text(text_container, relief="flat", bd=0, font=FONTE_PADRAO); self.text_obs.pack(fill="both", expand=True)
        self.frame_bloco_tabelas_replicado = tk.Frame(self.main_form_frame, bg='white')
        self.frame_bloco_tabelas_replicado.pack(pady=(20, 10), anchor="center")

    def _construir_bloco_tabelas(self, parent, vars_storage, tables_storage, refs_storage, tipo_bloco):
        header = tk.Frame(parent, bd=1, relief="solid", bg='white')
        for c, minsize in enumerate(self.col_widths): header.grid_columnconfigure(c, minsize=minsize)
        for r in range(3): header.grid_rowconfigure(r, minsize=30, weight=1)
        self._cell(header, 0, 0, "Grupo Normal = Grupo de Consumo", cs=9); self._cell(header, 1, 0, "  Grupos  ", rs=2)
        self._cell(header, 1, 1, "FASE", cs=4); self._cell(header, 1, 5, "TERRA", cs=4)
        self._cell(header, 2, 1, "Pickup"); self._cell(header, 2, 2, "Sequência"); self._cell(header, 2, 3, "Curva Lenta")
        self._cell(header, 2, 4, "Curva Rápida"); self._cell(header, 2, 5, "Pickup"); self._cell(header, 2, 6, "Sequência")
        self._cell(header, 2, 7, "Curva Lenta"); self._cell(header, 2, 8, "Curva Rápida")
        header.pack(pady=5)
        if tipo_bloco == "original": self.frame_tabela_header = header
        else: self.frame_tabela_header_rep = header
        tables_storage.clear()
        refs_storage.clear()
        tables_storage.append(header)
        for i in range(1, 4):
            tabela_frame, ref_cell, group_vars = self.criar_tabela_grupo(parent, f"  Grupo {i}  ")
            vars_storage[f'grupo_{i}'] = group_vars
            tables_storage.append(tabela_frame)
            refs_storage.append(ref_cell)
        self.criar_tabela_grupo4(parent, tables_storage)

    def criar_tabela_grupo4(self, parent, tables_storage):
        frame_tabela4 = tk.Frame(parent, bd=1, relief="solid")
        for c, minsize in enumerate(self.col_widths): frame_tabela4.grid_columnconfigure(c, minsize=minsize)
        frame_tabela4.grid_rowconfigure(0, minsize=60, weight=1)
        self._cell(frame_tabela4, 0, 0, "Grupo 4"); self._cell(frame_tabela4, 0, 1, ""); self._cell(frame_tabela4, 0, 2, ""); self._cell(frame_tabela4, 0, 3, "")
        subframe_4 = tk.Frame(frame_tabela4, bd=0, bg='white'); subframe_4.grid(row=0, column=4, sticky="nsew")
        subframe_4.grid_columnconfigure(0, weight=1); subframe_4.grid_columnconfigure(1, weight=1); subframe_4.grid_rowconfigure(0, weight=1)
        self._cell(subframe_4, 0, 0, ""); self._cell(subframe_4, 0, 1, "")
        self._cell(frame_tabela4, 0, 5, ""); self._cell(frame_tabela4, 0, 6, ""); self._cell(frame_tabela4, 0, 7, "")
        subframe_8 = tk.Frame(frame_tabela4, bd=0, bg='white'); subframe_8.grid(row=0, column=8, sticky="nsew")
        subframe_8.grid_columnconfigure(0, weight=1); subframe_8.grid_columnconfigure(1, weight=1); subframe_8.grid_rowconfigure(0, weight=1)
        self._cell(subframe_8, 0, 0, ""); self._cell(subframe_8, 0, 1, "")
        frame_tabela4.pack(pady=(0, 5))
        tables_storage.append(frame_tabela4)

    def _gerenciar_bloco_tabelas_replicado(self, *args):
        condicao = self.campos_dict["Condição"].get()
        for widget in self.frame_bloco_tabelas_replicado.winfo_children():
            widget.destroy()
        if condicao in ["Acess Inv", "Acess s/Inv"]:
            self.vars_grupos_rep.clear()
            self._construir_bloco_tabelas(self.frame_bloco_tabelas_replicado, self.vars_grupos_rep, self.tabelas_grupo_frames_rep, self.ref_cells_rep, "replicado")

    def _filtrar_lista(self, termo_busca, lista_completa, listbox):
        termo = termo_busca.get().lower()
        listbox.delete(0, tk.END)
        if not termo:
            for item in lista_completa: listbox.insert(tk.END, item)
        else:
            for item in lista_completa:
                if termo in item.lower(): listbox.insert(tk.END, item)

    def _filtrar_ajustes_recentes(self, *args):
        self._filtrar_lista(self.busca_ajustes_var, self.lista_ajustes_completa, self.listbox_local)

    def _toggle_selecionar_tudo_rascunhos(self):
        estado_selecao = self.selecionar_tudo_rascunhos_var.get()
        for var in self.rascunho_check_vars.values(): var.set(estado_selecao)

    def _replicar_sequencia_g1_para_g3(self, *args):
        try:
            valor_g1 = self.vars_grupos['grupo_1']['sequencia'].get()
            self.vars_grupos['grupo_3']['sequencia'].set(valor_g1)
        except KeyError: pass

    def deletar_rascunhos_selecionados(self):
        para_deletar = [eqpto for eqpto, var in self.rascunho_check_vars.items() if var.get()]
        if not para_deletar:
            messagebox.showwarning("Nenhuma Seleção", "Nenhum rascunho selecionado para deletar.")
            return
        self.controller.deletar_rascunhos(self, para_deletar)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mouse_wheel(self, event):
        if sys.platform == "win32": self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif sys.platform == "darwin": self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else:
            if event.num == 4: self.canvas.yview_scroll(-1, "units")
            elif event.num == 5: self.canvas.yview_scroll(1, "units")

    def open_dropdown_on_click(self, event):
        event.widget.after(5, lambda: event.widget.event_generate('<Down>'))

    def _cell(self, frame, r, c, txt="", rs=1, cs=1, sticky="nsew", width=None):
        label = tk.Label(frame, text=txt, font=FONTE_PADRAO, bg='white', relief="solid", bd=1)
        if width: label.config(width=width)
        label.grid(row=r, column=c, rowspan=rs, columnspan=cs, sticky=sticky)
        return label
    
    def _remove_focus(self, event):
        self.parent_window.focus_set()

    def limitar_4_caracteres(self, P): return len(P) <= 4

    def formatar_siom(self, *args):
        var = self.campos_dict["Siom"]; trace_info = var.trace_info()
        if trace_info: var.trace_remove("write", trace_info[0][1])
        valor = ''.join(filter(str.isdigit, var.get())); valor = valor[:7]
        formatado = f"{valor[:5]}-{valor[5:]}" if len(valor) > 5 else valor
        var.set(formatado); var.trace_add("write", self.formatar_siom)

    def formatar_coord(self, *args):
        var = self.campos_dict["Coord"]; trace_info = var.trace_info()
        if trace_info: var.trace_remove("write", trace_info[0][1])
        valor = ''.join(filter(str.isdigit, var.get())); valor = valor[:13]
        formatado = f"{valor[:6]}:{valor[6:]}" if len(valor) > 6 else valor
        var.set(formatado); var.trace_add("write", self.formatar_coord)

    def create_bordered_combobox(self, parent, var, values, width):
        cell_frame = tk.Frame(parent, relief="solid", bd=1, bg='white')
        combobox = ttk.Combobox(cell_frame, textvariable=var, values=values, state="readonly", width=width, font=FONTE_PADRAO, style='Arrowless.TCombobox', justify="center")
        combobox.bind("<Button-1>", self.open_dropdown_on_click)
        combobox.bind("<<ComboboxSelected>>", self._remove_focus)
        combobox.pack(fill="both", expand=True)
        return cell_frame

    def create_bordered_entry(self, parent, var, width, vcmd=None):
        cell_frame = tk.Frame(parent, relief="solid", bd=1, bg='white')
        entry = tk.Entry(cell_frame, textvariable=var, width=width, font=FONTE_PADRAO, justify="center", bd=0)
        if vcmd:
            entry.config(validate="key", validatecommand=vcmd)
        entry.pack(fill="both", expand=True)
        return cell_frame

    def criar_tabela_grupo(self, parent, group_name):
        group_vars = { "pickup_fase": tk.StringVar(), "sequencia": tk.StringVar(), "curva_lenta_tipo": tk.StringVar(), "curva_lenta_dial": tk.StringVar(), "curva_lenta_tadic": tk.StringVar(), "curva_rapida_dial": tk.StringVar(), "curva_rapida_tadic": tk.StringVar(), "pickup_terra": tk.StringVar(), "sequencia_terra": tk.StringVar(), "terra_tempo_lenta": tk.StringVar(), "terra_tempo_rapida": tk.StringVar() }
        frame_tabela = tk.Frame(parent, bd=1, relief="solid", bg='white')
        
        for c, minsize in enumerate(self.col_widths): frame_tabela.grid_columnconfigure(c, minsize=minsize)
        
        for r in range(1, 4): frame_tabela.grid_rowconfigure(r, minsize=30, weight=1)
        entry_fase_rapida_dial, entry_fase_rapida_tadic, entry_terra_rapida_tempo = None, None, None
        def _atualizar_sequencia_terra(*args): group_vars["sequencia_terra"].set(group_vars["sequencia"].get())
        def _gerenciar_campos_curva_rapida(*args):
            sequencia = group_vars["sequencia"].get()
            novo_estado = 'disabled' if sequencia in ['1L', '2L', '3L'] else 'normal'
            if entry_fase_rapida_dial: entry_fase_rapida_dial.config(state=novo_estado)
            if entry_fase_rapida_tadic: entry_fase_rapida_tadic.config(state=novo_estado)
            if entry_terra_rapida_tempo: entry_terra_rapida_tempo.config(state=novo_estado)
            if novo_estado == 'disabled': group_vars["curva_rapida_dial"].set(''); group_vars["curva_rapida_tadic"].set(''); group_vars["terra_tempo_rapida"].set('')
        group_vars["sequencia"].trace_add("write", _atualizar_sequencia_terra)
        group_vars["sequencia"].trace_add("write", _gerenciar_campos_curva_rapida)
        self._cell(frame_tabela, 1, 0, group_name, rs=3)
        self._cell(frame_tabela, 1, 1, "FASE", cs=2)
        opcoes_curva_lenta = ["", "IEC Muito Inversa", "IEC Ext. Inversa"]
        lenta_fase_cell = self.create_bordered_combobox(frame_tabela, group_vars["curva_lenta_tipo"], opcoes_curva_lenta, 0)
        lenta_fase_cell.grid(row=1, column=3, sticky="nsew")
        combobox_lenta_fase = lenta_fase_cell.winfo_children()[0]
        combobox_lenta_fase.config(font=FONTE_PEQUENA, justify="center")
        self._cell(frame_tabela, 1, 4, "IEC Inversa")
        self._cell(frame_tabela, 1, 5, "TERRA", cs=2)
        self._cell(frame_tabela, 1, 7, "T. Definido"); self._cell(frame_tabela, 1, 8, "T. Definido")
        
        pickup_fase_cell = self.create_bordered_entry(frame_tabela, group_vars["pickup_fase"], width=4, vcmd=(self.vcmd_4, "%P"))
        pickup_fase_cell.grid(row=1, column=1, rowspan=3, sticky="nsew")

        opcoes_sequencia = ["", "1L", "2L", "3L", "1R+3L", "1R+2L", "2R+2L"]
        cell_sequencia = self.create_bordered_combobox(frame_tabela, group_vars["sequencia"], opcoes_sequencia, 8); cell_sequencia.grid(row=1, column=2, rowspan=3, sticky="nsew")

        pickup_terra_cell = self.create_bordered_entry(frame_tabela, group_vars["pickup_terra"], width=4, vcmd=(self.vcmd_4, "%P"))
        pickup_terra_cell.grid(row=1, column=5, rowspan=3, sticky="nsew")

        self._cell(frame_tabela, 1, 6, "", rs=3).configure(bg='white')
        tk.Label(frame_tabela.grid_slaves(row=1, column=6)[0], textvariable=group_vars["sequencia_terra"], font=FONTE_PADRAO, justify="center", bg='white').pack(fill="both", expand=True)
        subframe_lenta = tk.Frame(frame_tabela, bd=0, bg='white'); subframe_lenta.grid(row=2, column=3, rowspan=2, sticky="nsew")
        for r in range(2): subframe_lenta.grid_rowconfigure(r, weight=1);
        for c in range(2): subframe_lenta.grid_columnconfigure(c, weight=1)
        self._cell(subframe_lenta, 0, 0, "Dial", sticky="nsew"); self._cell(subframe_lenta, 0, 1, "T. Adic.", sticky="nsew")
        tk.Entry(subframe_lenta, textvariable=group_vars["curva_lenta_dial"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=1, column=0, sticky="nsew")
        tk.Entry(subframe_lenta, textvariable=group_vars["curva_lenta_tadic"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=1, column=1, sticky="nsew")
        subframe_rapida = tk.Frame(frame_tabela, bd=0, bg='white'); subframe_rapida.grid(row=2, column=4, rowspan=2, sticky="nsew")
        for r in range(2): subframe_rapida.grid_rowconfigure(r, weight=1)
        for c in range(2): subframe_rapida.grid_columnconfigure(c, weight=1)
        self._cell(subframe_rapida, 0, 0, "Dial", sticky="nsew"); self._cell(subframe_rapida, 0, 1, "T. Adic.", sticky="nsew")
        entry_fase_rapida_dial = tk.Entry(subframe_rapida, textvariable=group_vars["curva_rapida_dial"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_fase_rapida_dial.grid(row=1, column=0, sticky="nsew")
        entry_fase_rapida_tadic = tk.Entry(subframe_rapida, textvariable=group_vars["curva_rapida_tadic"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_fase_rapida_tadic.grid(row=1, column=1, sticky="nsew")
        self._cell(frame_tabela, 2, 7, "Tempo (s)"); self._cell(frame_tabela, 2, 8, "Tempo (s)")
        
        terra_tempo_lenta_cell = self.create_bordered_entry(frame_tabela, group_vars["terra_tempo_lenta"], width=4, vcmd=(self.vcmd_4, "%P"))
        terra_tempo_lenta_cell.grid(row=3, column=7, sticky="nsew")

        entry_terra_rapida_tempo_cell = self.create_bordered_entry(frame_tabela, group_vars["terra_tempo_rapida"], width=4, vcmd=(self.vcmd_4, "%P"))
        entry_terra_rapida_tempo = entry_terra_rapida_tempo_cell.winfo_children()[0]
        entry_terra_rapida_tempo_cell.grid(row=3, column=8, sticky="nsew")

        frame_tabela.pack(pady=(0, 5))
        return frame_tabela, lenta_fase_cell, group_vars

    def get_form_data(self):
        data = {key.lower(): var.get() for key, var in self.campos_dict.items()}
        for i in range(1, 4):
            grupo_key = f'grupo_{i}'
            if grupo_key in self.vars_grupos:
                for var_name, var in self.vars_grupos[grupo_key].items():
                    data[f'g{i}_{var_name}'] = var.get()
        data['observacoes'] = self.text_obs.get("1.0", "end-1c")
        return data

    def preencher_formulario(self, dados_dict):
        self.limpar_formulario()
        for nome_campo, var in self.campos_dict.items():
            var.set(dados_dict.get(nome_campo.lower(), ""))
        for i in range(1, 4):
            grupo_key = f'grupo_{i}'
            if grupo_key in self.vars_grupos:
                for nome_var, var_tk in self.vars_grupos[grupo_key].items():
                    var_tk.set(dados_dict.get(f"g{i}_{nome_var}", ""))
        self.text_obs.insert("1.0", dados_dict.get("observacoes", ""))

    def limpar_formulario(self):
        for var in self.campos_dict.values(): var.set("")
        self.campos_dict["Data"].set(datetime.now().strftime('%d/%m/%Y'))
        self.campos_dict["Telecontrolado"].set("sim")
        for i in range(1, 4):
            if f'grupo_{i}' in self.vars_grupos:
                for var in self.vars_grupos[f'grupo_{i}'].values(): var.set("")
        self.text_obs.delete("1.0", "end")
        
    def salvar_rascunho(self):
        form_data = self.get_form_data()
        if not form_data.get("eqpto", "").strip():
            messagebox.showwarning("Campo Obrigatório", "O campo 'Eqpto' é obrigatório.", parent=self.parent_window)
            return
        self.controller.salvar_rascunho(self, form_data)

    def salvar_e_enviar(self):
        form_data = self.get_form_data()
        if not form_data.get("eqpto", "").strip():
            messagebox.showwarning("Campo Obrigatório", "O campo 'Eqpto' é obrigatório.", parent=self.parent_window)
            return
        self.controller.salvar_e_enviar(self, form_data)

    def atualizar_lista_local(self, equipamentos):
        self.listbox_local.delete(0, tk.END)
        self.lista_ajustes_completa = [eq['eqpto'] for eq in equipamentos] if equipamentos else []
        self._filtrar_ajustes_recentes()

    def reconstruir_lista_rascunhos(self, rascunhos_data=None):
        rascunhos = rascunhos_data if rascunhos_data is not None else self.controller.get_all_draft_equipments()
        self.lista_rascunhos_completa = [r['eqpto'] for r in rascunhos] if rascunhos else []
        for widget in self.rascunhos_items_frame.winfo_children(): widget.destroy()
        self.rascunho_check_vars.clear()
        
        termo_busca = self.busca_rascunhos_var.get().lower()
        rascunhos_filtrados = [r for r in self.lista_rascunhos_completa if termo_busca in r.lower()]
        for eqpto in rascunhos_filtrados:
            var = tk.BooleanVar()
            self.rascunho_check_vars[eqpto] = var
            row = tk.Frame(self.rascunhos_items_frame, bg='white'); row.pack(fill='x', expand=True, pady=1)
            ttk.Checkbutton(row, variable=var).pack(side='left')
            lbl = tk.Label(row, text=eqpto, anchor='w', bg='white'); lbl.pack(side='left', fill='x', expand=True)
            lbl.bind("<Double-1>", lambda e, eq=eqpto: self.carregar_rascunho_pelo_nome(eq))
            tk.Button(row, text="X", fg="red", relief="flat", cursor="hand2", font=("Helvetica", 8, "bold"), command=lambda e=eqpto: self.deletar_rascunho_individual(e), bg='white').pack(side='right')
        self.selecionar_tudo_rascunhos_var.set(False)
        self.rascunhos_canvas.yview_moveto(0)

    def atualizar_todas_as_listas(self):
        self.controller.atualizar_listas_memorial(self)

    def carregar_ficha_selecionada(self, event=None):
        if not self.listbox_local.curselection(): return
        eqpto = self.listbox_local.get(self.listbox_local.curselection()[0])
        self.controller.carregar_ficha_pelo_nome(self, eqpto, 'cadastros')

    def carregar_rascunho_pelo_nome(self, eqpto):
        self.controller.carregar_ficha_pelo_nome(self, eqpto, 'rascunhos')
        
    def abrir_janela_busca(self):
        messagebox.showinfo("Info", "Funcionalidade de busca detalhada em desenvolvimento.")

if __name__ == '__main__':
    class DummyController(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Teste do Módulo Memorial de Cálculo")
            self.geometry("1400x900")
        def show_frame(self, page_name):
            print(f"Simulando navegação para: {page_name}")
            self.destroy()
        def salvar_rascunho(self, view, data): print("Controller: Salvar Rascunho", data)
        def salvar_e_enviar(self, view, data): print("Controller: Salvar e Enviar", data)
        def atualizar_listas_memorial(self, view): print("Controller: Atualizando listas")
        def carregar_ficha_pelo_nome(self, view, eqpto, tabela): print(f"Controller: Carregando {eqpto} de {tabela}")
        def deletar_rascunhos(self, view, eq_list): print(f"Controller: Deletando rascunhos {eq_list}")
        def get_all_draft_equipments(self): return [{'eqpto':'RASCUNHO-TESTE-1'}, {'eqpto':'RASCUNHO-TESTE-2'}]
    app = DummyController()
    memorial_frame = MemorialCalculoFrame(app, app)
    memorial_frame.pack(fill="both", expand=True)
    app.mainloop()
