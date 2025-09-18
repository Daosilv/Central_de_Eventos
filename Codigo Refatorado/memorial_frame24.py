import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import sys
import json

FONTE_PADRAO = ("Times New Roman", 12)
FONTE_PEQUENA = ("Times New Roman", 10)
SIDEBAR_WIDTH = 450

class MemorialCalculoFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent_window = parent

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='white', foreground='black')
        style.map('TCombobox',
                  fieldbackground=[('readonly', 'white')],
                  selectbackground=[('readonly', 'white')],
                  selectforeground=[('readonly', 'black')])
        style.layout('Arrowless.TCombobox',
            [('Combobox.padding', {'expand': '1', 'sticky': 'nswe', 'children':
                [('Combobox.focus', {'expand': '1', 'sticky': 'nswe', 'children':
                    [('Combobox.text', {'sticky': 'nswe'})]
                })]
            })]
        )
        style.configure('Arrowless.TCombobox', justify='center')
        # --- NOVO ESTILO PARA CENTRALIZAR O TEXTO DO COMBOBOX ---
        style.configure('Centered.TCombobox', justify='center')


        self.busca_ajustes_var = tk.StringVar()
        self.lista_ajustes_completa = []
        self.busca_ajustes_var.trace_add("write", self.reconstruir_lista_ajustes)
        
        self.busca_rascunhos_var = tk.StringVar()
        self.lista_rascunhos_completa = []
        self.rascunho_check_vars = {} 
        self.selecionar_tudo_rascunhos_var = tk.BooleanVar()
        self.busca_rascunhos_var.trace_add("write", self.reconstruir_lista_rascunhos)
        
        self.campos_dict = { 
            "Autor": tk.StringVar(), "Eqpto": tk.StringVar(), "Malha": tk.StringVar(), 
            "Condição": tk.StringVar(), "Motivador": tk.StringVar(), "Alimentador": tk.StringVar(), 
            "NS": tk.StringVar(), "Siom": tk.StringVar(), "Data": tk.StringVar(value=datetime.now().strftime('%d/%m/%Y')), 
            "Coord": tk.StringVar(), "Endereço": tk.StringVar(), "Mídia": tk.StringVar(), 
            "Fabricante": tk.StringVar(), "Modelo": tk.StringVar(), "Comando": tk.StringVar(), 
            "Telecontrolado": tk.StringVar(value="sim"), 
            
            "Bypass": tk.StringVar(),
            "Vinculado a Acessante": tk.StringVar(value="Não"),
            "Eqpto Acessante": tk.StringVar(),
            "Manobra Efetiva": tk.StringVar(value="Não"),
            
            "param_consumo_pickup": tk.StringVar(), "param_consumo_curva": tk.StringVar(), "param_consumo_dial": tk.StringVar(),
            "param_consumo_t_adic": tk.StringVar(), "param_consumo_pot_kw": tk.StringVar(),
            "param_injecao_pickup": tk.StringVar(), "param_injecao_curva": tk.StringVar(), "param_injecao_dial": tk.StringVar(),
            "param_injecao_t_adic": tk.StringVar(), "param_injecao_pot_kw": tk.StringVar(),
            
            "tensao_kv_rede": tk.StringVar(), "carga_fase_a": tk.StringVar(), "carga_fase_b": tk.StringVar(), "carga_fase_c": tk.StringVar(),
            
            "cabo_critico_trecho": tk.StringVar(), "cabo_critico_nominal": tk.StringVar(), "cabo_critico_admissivel": tk.StringVar(),

            "corrente_falta_fase_cc_max": tk.StringVar(), "corrente_falta_fase_sens_princ": tk.StringVar(), "corrente_falta_terra_sens_princ": tk.StringVar(),

            "eqpto_montante_numero_l1": tk.StringVar(), "eqpto_montante_numero_l2": tk.StringVar(),
            "eqpto_montante_pickup_fase_g1_l1": tk.StringVar(), "eqpto_montante_pickup_fase_g1_l2": tk.StringVar(),
            "eqpto_montante_pickup_fase_g2_l1": tk.StringVar(), "eqpto_montante_pickup_fase_g2_l2": tk.StringVar(),
            "eqpto_montante_pickup_terra_g1_l1": tk.StringVar(), "eqpto_montante_pickup_terra_g1_l2": tk.StringVar(),
            "eqpto_montante_pickup_terra_g2_l1": tk.StringVar(), "eqpto_montante_pickup_terra_g2_l2": tk.StringVar(),
        }
        self.campos_dict["Condição"].trace_add("write", self._gerenciar_bloco_tabelas_replicado)
        self.campos_dict["Vinculado a Acessante"].trace_add("write", self._gerenciar_campo_acessante)
        
        self.anexos_list = []
        
        self.colunas_db = self.get_db_columns()
        self.vars_grupos = {}
        self.col_widths = [90, 70, 85, 120, 120, 70, 85, 120, 120]
        self.tabelas_grupo_frames = []
        self.ref_cells = []
        self.vars_grupos_rep = {}
        self.tabelas_grupo_frames_rep = []
        self.ref_cells_rep = []
        self.frame_tabela_header_rep = None

        # --- FUNÇÃO DE VALIDAÇÃO GENÉRICA E REGISTROS ---
        self.vcmd_limite = self.register(self._limitar_tamanho)
        self.vcmd_4 = self.register(lambda P: self._limitar_tamanho(P, '4')) # LINHA CORRIGIDA/ADICIONADA
        
        self.campos_dict["Siom"].trace_add("write", self.formatar_siom)
        self.campos_dict["Coord"].trace_add("write", self.formatar_coord)

        self.criar_layout_principal()
        self._criar_layout_cabecalho()
        self.criar_layout_formulario()

        if 'grupo_1' in self.vars_grupos and 'grupo_3' in self.vars_grupos:
            self.vars_grupos['grupo_1']['sequencia'].trace_add("write", self._replicar_sequencia_g1_para_g3)
        self.atualizar_todas_as_listas()
        self.after(150, self.alinhar_coluna_critica)
        self.after(10, self._gerenciar_campo_acessante) 

    @staticmethod
    def get_db_columns():
        colunas_principais = [
            "autor", "eqpto", "malha", "condição", "motivador", "alimentador", 
            "ns", "siom", "data", "coord", "endereço", "mídia", 
            "fabricante", "modelo", "comando", "telecontrolado", 
            "bypass", "vinculado_acessante", "eqpto_acessante", "manobra_efetiva",
            
            "param_consumo_pickup", "param_consumo_curva", "param_consumo_dial",
            "param_consumo_t_adic", "param_consumo_pot_kw",
            "param_injecao_pickup", "param_injecao_curva", "param_injecao_dial",
            "param_injecao_t_adic", "param_injecao_pot_kw",
            
            "tensao_kv_rede", "carga_fase_a", "carga_fase_b", "carga_fase_c",
            
            "cabo_critico_trecho", "cabo_critico_nominal", "cabo_critico_admissivel",

            "corrente_falta_fase_cc_max", "corrente_falta_fase_sens_princ", "corrente_falta_terra_sens_princ",

            "eqpto_montante_numero_l1", "eqpto_montante_numero_l2",
            "eqpto_montante_pickup_fase_g1_l1", "eqpto_montante_pickup_fase_g1_l2",
            "eqpto_montante_pickup_fase_g2_l1", "eqpto_montante_pickup_fase_g2_l2",
            "eqpto_montante_pickup_terra_g1_l1", "eqpto_montante_pickup_terra_g1_l2",
            "eqpto_montante_pickup_terra_g2_l1", "eqpto_montante_pickup_terra_g2_l2",
        ]
        
        campos_grupo = ["pickup_fase", "sequencia", "curva_lenta_tipo", "curva_lenta_dial", "curva_lenta_tadic", "curva_rapida_dial", "curva_rapida_tadic", "pickup_terra", "sequencia_terra", "terra_tempo_lenta", "terra_tempo_rapida"]
        
        colunas_grupos = []
        for i in range(1, 4):
            for campo in campos_grupo:
                colunas_grupos.append(f'g{i}_{campo}')

        colunas_grupos_rep = []
        for i in range(1, 4):
            for campo in campos_grupo:
                colunas_grupos_rep.append(f'g{i}_{campo}_rep')

        colunas_adicionais = ['observacoes', 'anexos']
        return colunas_principais + colunas_grupos + colunas_grupos_rep + colunas_adicionais

    def criar_layout_principal(self):
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
        self.content_holder_frame.grid_rowconfigure(1, weight=1)

        self.header_frame = tk.Frame(self.content_holder_frame, bg='white')
        self.header_frame.grid(row=0, column=0, sticky="new", padx=10, pady=10)
        
        self.main_form_frame = tk.Frame(self.content_holder_frame, bg='white')
        self.main_form_frame.grid(row=1, column=0, sticky="nsew", padx=10)

        sidebar_frame = tk.LabelFrame(self.content_holder_frame, text="Histórico", width=SIDEBAR_WIDTH, padx=5, pady=5, bg='white')
        sidebar_frame.grid(row=0, column=1, rowspan=2, sticky="ns", pady=10)
        
        sidebar_frame.pack_propagate(False)
        btn_atualizar_listas = ttk.Button(sidebar_frame, text="Atualizar Listas", command=self.atualizar_todas_as_listas)
        btn_atualizar_listas.pack(fill='x', pady=(0, 10))
        
        ajustes_container = tk.LabelFrame(sidebar_frame, text="Ajustes Recentes", padx=5, pady=5, bg='white'); ajustes_container.pack(fill='both', expand=True, pady=(0, 5))
        frame_busca_ajustes = tk.Frame(ajustes_container, bg='white'); frame_busca_ajustes.pack(fill='x')
        tk.Label(frame_busca_ajustes, text="Buscar:", bg='white').pack(side='left')
        tk.Entry(frame_busca_ajustes, textvariable=self.busca_ajustes_var).pack(side='left', fill='x', expand=True, padx=5)
        
        ajustes_canvas_frame = tk.Frame(ajustes_container, bg='white', relief="solid", bd=1); ajustes_canvas_frame.pack(fill='both', expand=True, pady=(5,0))
        self.ajustes_canvas = tk.Canvas(ajustes_canvas_frame, highlightthickness=0, bg='white')
        ajustes_scrollbar = ttk.Scrollbar(ajustes_canvas_frame, orient="vertical", command=self.ajustes_canvas.yview)
        self.ajustes_items_frame = tk.Frame(self.ajustes_canvas, bg='white')
        self.ajustes_window_id = self.ajustes_canvas.create_window((0, 0), window=self.ajustes_items_frame, anchor="nw")
        self.ajustes_canvas.bind("<Configure>", self.on_ajustes_canvas_configure)
        self.ajustes_canvas.configure(yscrollcommand=ajustes_scrollbar.set)
        ajustes_scrollbar.pack(side="right", fill="y"); self.ajustes_canvas.pack(side="left", fill="both", expand=True)
        self.ajustes_items_frame.bind("<Configure>", lambda e: self.ajustes_canvas.configure(scrollregion=self.ajustes_canvas.bbox("all")))

        rascunhos_container = tk.LabelFrame(sidebar_frame, text="Rascunhos", padx=5, pady=5, bg='white'); rascunhos_container.pack(fill='both', expand=True, pady=(5, 5))
        frame_busca_rascunhos = tk.Frame(rascunhos_container, bg='white'); frame_busca_rascunhos.pack(fill='x')
        tk.Label(frame_busca_rascunhos, text="Buscar:", bg='white').pack(side='left')
        tk.Entry(frame_busca_rascunhos, textvariable=self.busca_rascunhos_var).pack(side='left', fill='x', expand=True, padx=5)
        frame_rascunhos_actions = tk.Frame(rascunhos_container, bg='white'); frame_rascunhos_actions.pack(fill='x', pady=(5,0))
        ttk.Checkbutton(frame_rascunhos_actions, text="Selecionar Tudo", variable=self.selecionar_tudo_rascunhos_var, command=self._toggle_selecionar_tudo_rascunhos).pack(side='left')
        tk.Button(frame_rascunhos_actions, text="X", fg="red", font=("Helvetica", 10, "bold"), command=self.deletar_rascunhos_selecionados, width=2, relief="flat", cursor="hand2", bg='white').pack(side='right', padx=(0,5))
        
        rascunhos_canvas_frame = tk.Frame(rascunhos_container, bg='white', relief="solid", bd=1); rascunhos_canvas_frame.pack(fill='both', expand=True, pady=5)
        self.rascunhos_canvas = tk.Canvas(rascunhos_canvas_frame, highlightthickness=0, bg='white')
        rascunhos_scrollbar = ttk.Scrollbar(rascunhos_canvas_frame, orient="vertical", command=self.rascunhos_canvas.yview)
        self.rascunhos_items_frame = tk.Frame(self.rascunhos_canvas, bg='white')
        self.rascunhos_window_id = self.rascunhos_canvas.create_window((0, 0), window=self.rascunhos_items_frame, anchor="nw")
        self.rascunhos_canvas.bind("<Configure>", self.on_rascunhos_canvas_configure)
        self.rascunhos_canvas.configure(yscrollcommand=rascunhos_scrollbar.set)
        rascunhos_scrollbar.pack(side="right", fill="y"); self.rascunhos_canvas.pack(side="left", fill="both", expand=True)
        self.rascunhos_items_frame.bind("<Configure>", lambda e: self.rascunhos_canvas.configure(scrollregion=self.canvas.bbox("all")))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window_id, width=event.width)

    def on_ajustes_canvas_configure(self, event):
        canvas_width = event.width
        self.ajustes_canvas.itemconfig(self.ajustes_window_id, width=canvas_width)
        
    def on_rascunhos_canvas_configure(self, event):
        canvas_width = event.width
        self.rascunhos_canvas.itemconfig(self.rascunhos_window_id, width=canvas_width)

    def _criar_layout_cabecalho(self):
        frame_campos = tk.Frame(self.header_frame, bg='white')
        frame_campos.pack(fill="x")
        
        # Linha 1
        row1_frame = tk.Frame(frame_campos, bg='white'); row1_frame.pack(fill="x", expand=True, pady=(0, 2))
        self._criar_celula_cabecalho(row1_frame, "Autor:", self.campos_dict["Autor"], tk.Entry, {}, 4, 40, (self.vcmd_limite, '%P', '40'))
        self._criar_celula_cabecalho(row1_frame, "Data:", self.campos_dict["Data"], tk.Entry, {}, 4, 12, (self.vcmd_limite, '%P', '12'))
        self._criar_celula_cabecalho(row1_frame, "NS:", self.campos_dict["NS"], tk.Entry, {}, 3, 20, (self.vcmd_limite, '%P', '20'))
        self._criar_celula_cabecalho(row1_frame, "Eqpto:", self.campos_dict["Eqpto"], tk.Entry, {}, 5, 10, (self.vcmd_limite, '%P', '10'))
        opcoes_condicao = ["", "Acess Inv", "Acess s/Inv", "NA", "NF", "NA ABR", "NF LS", "P.O. NA", "P.O. NF", "P.O. SECC NA", "P.O. SECC NF", "SECC NA", "SECC NF", "PRIM", "SE RELI", "SE SECI", "MONOF. NF", "MONOF. NA", "MONOF. SECC NA", "MONOF. SECC NF"]
        self._criar_celula_cabecalho(row1_frame, "Condição:", self.campos_dict["Condição"], ttk.Combobox, {"values": opcoes_condicao}, 8, 20)

        # Linha 2
        row2_frame = tk.Frame(frame_campos, bg='white'); row2_frame.pack(fill="x", expand=True, pady=(0, 2))
        opcoes_malha = ["", "Centro", "Leste", "Mantiqueira", "Norte", "Sul"]
        self._criar_celula_cabecalho(row2_frame, "Malha:", self.campos_dict["Malha"], ttk.Combobox, {"values": opcoes_malha}, 6, 10)
        self._criar_celula_cabecalho(row2_frame, "Alimentador:", self.campos_dict["Alimentador"], tk.Entry, {}, 10, 17, (self.vcmd_limite, '%P', '17'))
        opcoes_motivador = ["", "Instalação", "Reajuste", "Relocação"]
        self._criar_celula_cabecalho(row2_frame, "Motivador:", self.campos_dict["Motivador"], ttk.Combobox, {"values": opcoes_motivador}, 8, 8)
        self._criar_celula_cabecalho(row2_frame, "Coord:", self.campos_dict["Coord"], tk.Entry, {}, 5, 20, (self.vcmd_limite, '%P', '20'))
        self._criar_celula_cabecalho(row2_frame, "Endereço:", self.campos_dict["Endereço"], tk.Entry, {}, 8, 45, (self.vcmd_limite, '%P', '45'))

        # Linha 3
        row3_frame = tk.Frame(frame_campos, bg='white'); row3_frame.pack(fill="x", expand=True, pady=(0, 2))
        opcoes_midia = ["", "Celular", "Satélite", "Rádio", "Desconhecido", "Não enc."]
        self._criar_celula_cabecalho(row3_frame, "Mídia:", self.campos_dict["Mídia"], ttk.Combobox, {"values": opcoes_midia}, 6, 10)
        opcoes_fabricante = ["", "ABB", "AMPERA", "ARTECHE", "BRUSH", "COOPER", "GeW", "HSS", "McGRAW_EDISON", "NOJA", "NU_LEC", "REYROLLE", "ROMAGNOLE", "SIEMENS", "SCHNEIDER", "TAVRIDA", "WESTINGHOUSE", "WHIPP_BOURNE", "DESCONHECIDO", "SC_ElectricCompany"]
        self._criar_celula_cabecalho(row3_frame, "Fabricante:", self.campos_dict["Fabricante"], ttk.Combobox, {"values": opcoes_fabricante}, 10, 20)
        self._criar_celula_cabecalho(row3_frame, "Modelo:", self.campos_dict["Modelo"], tk.Entry, {}, 6, 20, (self.vcmd_limite, '%P', '20'))
        self._criar_celula_cabecalho(row3_frame, "Comando:", self.campos_dict["Comando"], tk.Entry, {}, 8, 15, (self.vcmd_limite, '%P', '15'))
        self._criar_celula_cabecalho(row3_frame, "Telecontrolado:", self.campos_dict["Telecontrolado"], ttk.Combobox, {"values": ["sim", "não"]}, 12, 5)
        self._criar_celula_cabecalho(row3_frame, "Siom:", self.campos_dict["Siom"], tk.Entry, {}, 4, 15, (self.vcmd_limite, '%P', '15'))

        # Linha 4
        row4_frame = tk.Frame(frame_campos, bg='white'); row4_frame.pack(fill="x", expand=True)
        self._criar_celula_cabecalho(row4_frame, "By-Pass:", self.campos_dict["Bypass"], tk.Entry, {}, 6, 10, (self.vcmd_limite, '%P', '10'))
        self._criar_celula_cabecalho(row4_frame, "Manobra Efetiva:", self.campos_dict["Manobra Efetiva"], ttk.Combobox, {"values": ["Não", "Sim"]}, 14, 5)
        self._criar_celula_cabecalho(row4_frame, "Vinculado a Acessante:", self.campos_dict["Vinculado a Acessante"], ttk.Combobox, {"values": ["Não", "Sim"]}, 19, 5)
        self.frame_acessante = self._criar_celula_cabecalho(row4_frame, "Eqpto Acessante:", self.campos_dict["Eqpto Acessante"], tk.Entry, {}, 14, 10, (self.vcmd_limite, '%P', '10'))

    def _gerenciar_campo_acessante(self, *args):
        if self.campos_dict["Vinculado a Acessante"].get() == "Sim":
            self.frame_acessante.pack(side='left', fill='y', padx=(0,5))
        else:
            self.frame_acessante.pack_forget()
            self.campos_dict["Eqpto Acessante"].set("")

    def _criar_celula_cabecalho(self, parent, label_text, var, widget_class, widget_options, label_width, entry_width, validate_cmd=None):
        frame = tk.Frame(parent, bg='white')
        frame.pack(side='left', fill='y', padx=(0,5))
        
        label = tk.Label(frame, text=label_text, font=FONTE_PADRAO, anchor="w", bg='white', width=label_width, relief="solid", bd=1, padx=5)
        label.pack(side='left', fill='both')

        widget_container = tk.Frame(frame, relief="solid", bd=1)
        
        options = widget_options.copy()
        options['textvariable'] = var
        options['font'] = FONTE_PADRAO

        if widget_class == ttk.Combobox:
            options['state'] = 'readonly'
            options['style'] = 'Centered.TCombobox'
            widget = widget_class(widget_container, **options)
        else: # tk.Entry
            if validate_cmd:
                options['validate'] = 'key'
                options['validatecommand'] = validate_cmd
            widget = widget_class(widget_container, **options)
        
        widget.config(width=entry_width)
        widget.pack()
        widget_container.pack(side='left', fill='both', expand=True)
        return frame

    def criar_layout_formulario(self):
        # O Checkbox 'Manobra Efetiva' foi removido daqui e movido para o cabeçalho
        self._criar_novas_tabelas_parametros(self.main_form_frame)
        
        frame_anexos = tk.Frame(self.main_form_frame, bg='white')
        frame_anexos.pack(pady=(15, 5), padx=10, anchor='w')
        btn_anexos = tk.Button(frame_anexos, text="+", font=("Helvetica", 10, "bold"), relief="solid", bd=1, command=self.abrir_anexos, cursor="hand2")
        btn_anexos.pack(side="left", padx=(0, 5))
        lbl_anexos = tk.Label(frame_anexos, text="Anexos", font=FONTE_PADRAO, bg='white')
        lbl_anexos.pack(side="left")
        
        wrap_tabelas = tk.Frame(self.main_form_frame, bg='white')
        wrap_tabelas.pack(pady=10, anchor="center")
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
        self._construir_bloco_tabelas(self.frame_bloco_tabelas_replicado, self.vars_grupos_rep, self.tabelas_grupo_frames_rep, self.ref_cells_rep, "replicado")
        self.after(150, self._alinhar_coluna_critica_replicada)
        self._set_widgets_state(self.frame_bloco_tabelas_replicado, 'disabled')

    def _criar_novas_tabelas_parametros(self, parent):
        container_principal = tk.Frame(parent, bg='white')
        container_principal.pack(pady=(10, 10), padx=10, anchor='w')

        # --- REORGANIZAÇÃO DAS COLUNAS E TABELAS ---
        coluna_esquerda = tk.Frame(container_principal, bg='white')
        coluna_esquerda.grid(row=0, column=0, sticky='new', padx=(0, 10))
        
        coluna_meio = tk.Frame(container_principal, bg='white')
        coluna_meio.grid(row=0, column=1, sticky='new', padx=(0, 10))
        
        coluna_direita = tk.Frame(container_principal, bg='white')
        coluna_direita.grid(row=0, column=2, sticky='new')

        # COLUNA 1: Parâmetros do Coordenograma
        frame_coordenograma = tk.Frame(coluna_esquerda, bg='white')
        frame_coordenograma.pack(anchor='w')
        tk.Label(frame_coordenograma, text="Parâmetros do Coordenograma do Cliente", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=0, column=0, columnspan=3, sticky='nsew')
        tk.Label(frame_coordenograma, text="", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=1, column=0, sticky='nsew')
        tk.Label(frame_coordenograma, text="Consumo", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=1, column=1, sticky='nsew')
        tk.Label(frame_coordenograma, text="Injeção", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=1, column=2, sticky='nsew')
        
        labels_coord = ["Pick-up (A)", "Curva", "Dial", "T. Adic.", "Pot. de Consumo (kW)", "Pot. de Injeção (kW)"]
        vars_consumo = ["param_consumo_pickup", "param_consumo_curva", "param_consumo_dial", "param_consumo_t_adic", "param_consumo_pot_kw"]
        vars_injecao = ["param_injecao_pickup", "param_injecao_curva", "param_injecao_dial", "param_injecao_t_adic", "param_injecao_pot_kw"]

        for i, label in enumerate(labels_coord[:4]):
            tk.Label(frame_coordenograma, text=label, font=FONTE_PADRAO, relief="solid", bd=1, anchor='w', width=20).grid(row=i+2, column=0, sticky='nsew')
            tk.Entry(frame_coordenograma, textvariable=self.campos_dict[vars_consumo[i]], font=FONTE_PADRAO, justify='center', relief='solid', bd=1, width=8).grid(row=i+2, column=1, sticky='nsew')
            tk.Entry(frame_coordenograma, textvariable=self.campos_dict[vars_injecao[i]], font=FONTE_PADRAO, justify='center', relief='solid', bd=1, width=8).grid(row=i+2, column=2, sticky='nsew')
        
        tk.Label(frame_coordenograma, text=labels_coord[4], font=FONTE_PADRAO, relief="solid", bd=1, anchor='w').grid(row=6, column=0, sticky='nsew')
        tk.Entry(frame_coordenograma, textvariable=self.campos_dict[vars_consumo[4]], font=FONTE_PADRAO, justify='center', relief='solid', bd=1).grid(row=6, column=1, columnspan=2, sticky='nsew')
        tk.Label(frame_coordenograma, text=labels_coord[5], font=FONTE_PADRAO, relief="solid", bd=1, anchor='w').grid(row=7, column=0, sticky='nsew')
        tk.Entry(frame_coordenograma, textvariable=self.campos_dict[vars_injecao[4]], font=FONTE_PADRAO, justify='center', relief='solid', bd=1).grid(row=7, column=1, columnspan=2, sticky='nsew')

        # COLUNA 2: Tensão e Corrente de Falta
        f3 = tk.Frame(coluna_meio, bg='white') # Tensão
        f3.pack(anchor='w', pady=(0, 10))
        params_tensao = [
            ("Tensão [kV] da rede", self.campos_dict["tensao_kv_rede"]),
            ("Carga - fase A [A]", self.campos_dict["carga_fase_a"]),
            ("Carga - fase B [A]", self.campos_dict["carga_fase_b"]),
            ("Carga - fase C [A]", self.campos_dict["carga_fase_c"])
        ]
        for i, (label, var) in enumerate(params_tensao):
            tk.Label(f3, text=label, font=FONTE_PADRAO, bg='white', relief="solid", bd=1, width=18, anchor='w').grid(row=i, column=0, sticky="nsew")
            tk.Entry(f3, textvariable=var, font=FONTE_PADRAO, justify="center", relief="solid", bd=1, width=8).grid(row=i, column=1, sticky="nsew")

        f5 = tk.Frame(coluna_meio, bg='white') # Corrente de Falta
        f5.pack(anchor='w', pady=(0, 10))
        tk.Label(f5, text="Corrente de Falta", font=FONTE_PADRAO, bg='white', relief="solid", bd=1).grid(row=0, column=0, columnspan=2, sticky='nsew')
        params_corrente = [
            ("FASE - CC máximo [A]", self.campos_dict["corrente_falta_fase_cc_max"]),
            ("FASE - Sensibilidade principal [A]", self.campos_dict["corrente_falta_fase_sens_princ"]),
            ("TERRA - Sensibilidade principal [A]", self.campos_dict["corrente_falta_terra_sens_princ"]),
        ]
        for i, (label, var) in enumerate(params_corrente):
            tk.Label(f5, text=label, font=FONTE_PADRAO, bg='white', relief="solid", bd=1, width=28, anchor='w').grid(row=i+1, column=0, sticky="nsew")
            tk.Entry(f5, textvariable=var, font=FONTE_PADRAO, justify="center", relief="solid", bd=1, width=12).grid(row=i+1, column=1, sticky="nsew")

        # COLUNA 3: Equipamento a Montante e Cabo Crítico
        frame_montante = tk.Frame(coluna_direita, bg='white') # Lado 1 e Lado 2
        frame_montante.pack(anchor='w', pady=(0, 10))
        tk.Label(frame_montante, text="", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=0, column=0, sticky='nsew')
        tk.Label(frame_montante, text="Lado 1\nA montante", font=FONTE_PADRAO, relief="solid", bd=1, wraplength=70, justify="center").grid(row=0, column=1, sticky='nsew')
        tk.Label(frame_montante, text="Lado 2", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=0, column=2, sticky='nsew')
        labels_montante = ["Número do Equipamento", "Pick-up Fase - G1 (A)", "Pick-up Fase - G2 (A)", "Pick-up Terra - G1 (A)", "Pick-up Terra - G2 (A)"]
        vars_montante = ["eqpto_montante_numero", "eqpto_montante_pickup_fase_g1", "eqpto_montante_pickup_fase_g2", "eqpto_montante_pickup_terra_g1", "eqpto_montante_pickup_terra_g2"]
        for i, label in enumerate(labels_montante):
            row_num = i + 1
            tk.Label(frame_montante, text=label, font=FONTE_PADRAO, relief="solid", bd=1, anchor='w', width=20).grid(row=row_num, column=0, sticky='nsew')
            tk.Entry(frame_montante, textvariable=self.campos_dict[f"{vars_montante[i]}_l1"], font=FONTE_PADRAO, justify='center', relief='solid', bd=1, width=8).grid(row=row_num, column=1, sticky='nsew')
            tk.Entry(frame_montante, textvariable=self.campos_dict[f"{vars_montante[i]}_l2"], font=FONTE_PADRAO, justify='center', relief='solid', bd=1, width=8).grid(row=row_num, column=2, sticky='nsew')
        
        f4 = tk.Frame(coluna_direita, bg='white') # Cabo Crítico
        f4.pack(anchor='w', pady=(0, 10))
        tk.Label(f4, text="Cabo crítico no trecho", font=FONTE_PADRAO, bg='white', relief="solid", bd=1).grid(row=0, column=0, sticky='nsew')
        tk.Label(f4, text="Nominal [A]", font=FONTE_PADRAO, bg='white', relief="solid", bd=1).grid(row=0, column=1, sticky='nsew')
        tk.Label(f4, text="Admissível [A]", font=FONTE_PADRAO, bg='white', relief="solid", bd=1).grid(row=0, column=2, sticky='nsew')
        tk.Entry(f4, textvariable=self.campos_dict["cabo_critico_trecho"], font=FONTE_PADRAO, justify="center", relief="solid", bd=1, width=16).grid(row=1, column=0, sticky="nsew")
        tk.Entry(f4, textvariable=self.campos_dict["cabo_critico_nominal"], font=FONTE_PADRAO, justify="center", relief="solid", bd=1, width=12).grid(row=1, column=1, sticky="nsew")
        tk.Entry(f4, textvariable=self.campos_dict["cabo_critico_admissivel"], font=FONTE_PADRAO, justify="center", relief="solid", bd=1, width=12).grid(row=1, column=2, sticky="nsew")
            
    def _construir_bloco_tabelas(self, parent, vars_storage, tables_storage, refs_storage, tipo_bloco):
        header = tk.Frame(parent, bd=1, relief="solid", bg='white')
        for c, minsize in enumerate(self.col_widths): header.grid_columnconfigure(c, minsize=minsize)
        for r in range(3): header.grid_rowconfigure(r, minsize=30, weight=1)
        self._cell(header, 0, 0, "Grupo Normal = Grupo de Consumo", cs=9); self._cell(header, 1, 0, "  Grupos  ", rs=2)
        self._cell(header, 1, 1, "FASE", cs=4); self._cell(header, 1, 5, "TERRA", cs=4)
        self._cell(header, 2, 1, "  Pickup  "); self._cell(header, 2, 2, "  Sequência  "); self._cell(header, 2, 3, "  Curva Lenta  ")
        self._cell(header, 2, 4, "  Curva Rápida  "); self._cell(header, 2, 5, "  Pickup  "); self._cell(header, 2, 6, "  Sequência  ")
        self._cell(header, 2, 7, "  Curva Lenta  "); self._cell(header, 2, 8, "  Curva Rápida  ")
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
        for i, minsize in enumerate(self.col_widths): frame_tabela4.grid_columnconfigure(i, minsize=minsize)
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

    def _set_widgets_state(self, parent, new_state):
        for child in parent.winfo_children():
            if hasattr(child, 'config') and 'state' in child.config():
                widget_class = child.winfo_class()
                if widget_class == 'TCombobox': child.config(state='readonly' if new_state == 'normal' else 'disabled')
                else: child.config(state=new_state)
            self._set_widgets_state(child, new_state)

    def _gerenciar_bloco_tabelas_replicado(self, *args):
        condicao = self.campos_dict["Condição"].get()
        if condicao in ["Acess Inv", "Acess s/Inv"]:
            self._set_widgets_state(self.frame_bloco_tabelas_replicado, 'normal')
        else:
            self._set_widgets_state(self.frame_bloco_tabelas_replicado, 'disabled')
            for grupo_key in self.vars_grupos_rep:
                for var in self.vars_grupos_rep[grupo_key].values(): var.set("")

    def _alinhar_coluna_critica_replicada(self):
        self.update_idletasks()
        if not self.ref_cells_rep or not self.ref_cells_rep[0].winfo_exists(): return
        reference_width = self.ref_cells_rep[0].winfo_width()
        if reference_width > 1:
            if self.frame_tabela_header_rep: self.frame_tabela_header_rep.grid_columnconfigure(3, minsize=reference_width)
            for table in self.tabelas_grupo_frames_rep: table.grid_columnconfigure(3, minsize=reference_width)
    
    def _toggle_selecionar_tudo_rascunhos(self):
        estado_selecao = self.selecionar_tudo_rascunhos_var.get()
        for var in self.rascunho_check_vars.values(): var.set(estado_selecao)

    def _replicar_sequencia_g1_para_g3(self, *args):
        try:
            valor_g1 = self.vars_grupos['grupo_1']['sequencia'].get()
            self.vars_grupos['grupo_3']['sequencia'].set(valor_g1)
        except KeyError: pass

    def deletar_rascunho_individual(self, eqpto_para_deletar):
        if messagebox.askyesno("Confirmar Exclusão", f"Você tem certeza que deseja deletar permanentemente o rascunho para '{eqpto_para_deletar}'?"):
            try:
                self.controller.deletar_rascunhos(self, [eqpto_para_deletar])
            except Exception as e: messagebox.showerror("Erro", f"Não foi possível deletar o rascunho: {e}")

    def deletar_rascunhos_selecionados(self):
        para_deletar = [eqpto for eqpto, var in self.rascunho_check_vars.items() if var.get()]
        if not para_deletar:
            messagebox.showwarning("Nenhuma Seleção", "Nenhum rascunho selecionado para deletar.")
            return
        if messagebox.askyesno("Confirmar Exclusão em Massa", f"Você tem certeza que deseja deletar os {len(para_deletar)} rascunhos selecionados?"):
            try:
                self.controller.deletar_rascunhos(self, para_deletar)
            except Exception as e: messagebox.showerror("Erro", f"Ocorreu um erro ao deletar os rascunhos: {e}")

    def alinhar_coluna_critica(self):
        self.update_idletasks()
        if not self.ref_cells or not self.ref_cells[0].winfo_exists(): return
        reference_width = self.ref_cells[0].winfo_width()
        if reference_width > 1:
            if self.frame_tabela_header: self.frame_tabela_header.grid_columnconfigure(3, minsize=reference_width)
            for table in self.tabelas_grupo_frames: table.grid_columnconfigure(3, minsize=reference_width)

    def on_frame_configure(self, event): self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def _on_mouse_wheel(self, event):
        if sys.platform == "win32": self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            if event.num == 4: self.canvas.yview_scroll(-1, "units")
            elif event.num == 5: self.canvas.yview_scroll(1, "units")

    def open_dropdown_on_click(self, event): event.widget.after(5, lambda: event.widget.event_generate('<Down>'))
    def _cell(self, frame, r, c, txt="", rs=1, cs=1, sticky="nsew"):
        outer = tk.Frame(frame, relief="solid", bd=1, bg='white'); outer.grid(row=r, column=c, rowspan=rs, columnspan=cs, sticky=sticky)
        if txt: tk.Label(outer, text=txt, font=FONTE_PADRAO, bg='white').pack(fill="both", expand=True)
        return outer

    def _limitar_tamanho(self, P, max_len_str):
        max_len = int(max_len_str)
        return len(P) <= max_len

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
        combobox = ttk.Combobox(cell_frame, textvariable=var, values=values, state="readonly", width=width, font=FONTE_PADRAO, style='Arrowless.TCombobox')
        combobox.bind("<Button-1>", self.open_dropdown_on_click)
        combobox.pack(fill="both", expand=True)
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
        tk.Label(frame_tabela, text=group_name, relief="solid", bd=1, font=FONTE_PADRAO, bg='white').grid(row=1, column=0, rowspan=3, sticky="nsew")
        tk.Label(frame_tabela, text="FASE", relief="solid", bd=1, font=FONTE_PADRAO, bg='white').grid(row=1, column=1, columnspan=2, sticky="nsew")
        opcoes_curva_lenta = ["", "IEC Muito Inversa", "IEC Ext. Inversa"]
        lenta_fase_cell = tk.Frame(frame_tabela, relief="solid", bd=1, bg='white')
        combobox_lenta_fase = ttk.Combobox(lenta_fase_cell, textvariable=group_vars["curva_lenta_tipo"], values=opcoes_curva_lenta, state="readonly", font=FONTE_PEQUENA, style='Arrowless.TCombobox')
        combobox_lenta_fase.bind("<Button-1>", self.open_dropdown_on_click); combobox_lenta_fase.pack(fill='both', expand=True); lenta_fase_cell.grid(row=1, column=3, sticky="nsew")
        self._cell(frame_tabela, 1, 4, "IEC Inversa")
        tk.Label(frame_tabela, text="TERRA", relief="solid", bd=1, font=FONTE_PADRAO, bg='white').grid(row=1, column=5, columnspan=2, sticky="nsew")
        tk.Label(frame_tabela, text="T. Definido", relief="solid", bd=1, font=FONTE_PADRAO, bg='white').grid(row=1, column=7, sticky="nsew"); tk.Label(frame_tabela, text="T. Definido", relief="solid", bd=1, font=FONTE_PADRAO, bg='white').grid(row=1, column=8, sticky="nsew")
        entry_pickup_fase = tk.Entry(frame_tabela, textvariable=group_vars["pickup_fase"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_pickup_fase.grid(row=1, column=1, rowspan=3, sticky="nsew")
        opcoes_sequencia = ["", "1L", "2L", "3L", "1R+3L", "1R+2L", "2R+2L"]
        cell_sequencia = tk.Frame(frame_tabela, relief="solid", bd=1, bg='white'); cell_sequencia.grid_propagate(False); cell_sequencia.grid(row=1, column=2, rowspan=3, sticky="nsew")
        combobox_sequencia_fase = ttk.Combobox(cell_sequencia, textvariable=group_vars["sequencia"], values=opcoes_sequencia, state="readonly", font=FONTE_PADRAO, width=8, style='Arrowless.TCombobox')
        combobox_sequencia_fase.bind("<Button-1>", self.open_dropdown_on_click); combobox_sequencia_fase.pack(fill="both", expand=True)
        entry_pickup_terra = tk.Entry(frame_tabela, textvariable=group_vars["pickup_terra"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_pickup_terra.grid(row=1, column=5, rowspan=3, sticky="nsew")
        cell_sequencia_terra = tk.Frame(frame_tabela, relief="solid", bd=1, bg='white'); cell_sequencia_terra.grid_propagate(False); cell_sequencia_terra.grid(row=1, column=6, rowspan=3, sticky="nsew")
        tk.Label(cell_sequencia_terra, textvariable=group_vars["sequencia_terra"], font=FONTE_PADRAO, justify="center", bg='white').pack(fill="both", expand=True)
        subframe_lenta = tk.Frame(frame_tabela, bd=0, bg='white'); subframe_lenta.grid_propagate(False); subframe_lenta.grid(row=2, column=3, rowspan=2, sticky="nsew")
        for r in range(2): subframe_lenta.grid_rowconfigure(r, weight=1);
        for c in range(2): subframe_lenta.grid_columnconfigure(c, weight=1)
        tk.Label(subframe_lenta, text="Dial", font=FONTE_PADRAO, width=8, relief="solid", bd=1, bg='white').grid(row=0, column=0, sticky="nsew"); tk.Label(subframe_lenta, text="T. Adic.", font=FONTE_PADRAO, width=8, relief="solid", bd=1, bg='white').grid(row=0, column=1, sticky="nsew")
        tk.Entry(subframe_lenta, textvariable=group_vars["curva_lenta_dial"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=1, column=0, sticky="nsew")
        tk.Entry(subframe_lenta, textvariable=group_vars["curva_lenta_tadic"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=1, column=1, sticky="nsew")
        subframe_rapida = tk.Frame(frame_tabela, bd=0, bg='white'); subframe_rapida.grid_propagate(False); subframe_rapida.grid(row=2, column=4, rowspan=2, sticky="nsew")
        for r in range(2): subframe_rapida.grid_rowconfigure(r, weight=1)
        for c in range(2): subframe_rapida.grid_columnconfigure(c, weight=1)
        tk.Label(subframe_rapida, text="Dial", font=FONTE_PADRAO, width=8, relief="solid", bd=1, bg='white').grid(row=0, column=0, sticky="nsew"); tk.Label(subframe_rapida, text="T. Adic.", font=FONTE_PADRAO, width=8, relief="solid", bd=1, bg='white').grid(row=0, column=1, sticky="nsew")
        entry_fase_rapida_dial = tk.Entry(subframe_rapida, textvariable=group_vars["curva_rapida_dial"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_fase_rapida_dial.grid(row=1, column=0, sticky="nsew")
        entry_fase_rapida_tadic = tk.Entry(subframe_rapida, textvariable=group_vars["curva_rapida_tadic"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_fase_rapida_tadic.grid(row=1, column=1, sticky="nsew")
        self._cell(frame_tabela, 2, 7, "Tempo (s)"); self._cell(frame_tabela, 2, 8, "Tempo (s)")
        tk.Entry(frame_tabela, textvariable=group_vars["terra_tempo_lenta"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=3, column=7, sticky="nsew")
        entry_terra_rapida_tempo = tk.Entry(frame_tabela, textvariable=group_vars["terra_tempo_rapida"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_terra_rapida_tempo.grid(row=3, column=8, sticky="nsew")
        frame_tabela.pack(pady=(0, 5))
        return frame_tabela, lenta_fase_cell, group_vars

    def _get_form_data(self):
        data = {key.lower(): var.get() for key, var in self.campos_dict.items()}
        
        # Coleta dados do primeiro bloco de tabelas
        for i in range(1, 4):
            grupo_key = f'grupo_{i}'
            if grupo_key in self.vars_grupos:
                for var_name, var in self.vars_grupos[grupo_key].items():
                    data[f'g{i}_{var_name}'] = var.get()
        
        # Coleta dados do segundo bloco de tabelas (replicado), se ativo
        condicao = self.campos_dict["Condição"].get()
        if condicao in ["Acess Inv", "Acess s/Inv"]:
            for i in range(1, 4):
                grupo_key = f'grupo_{i}'
                if grupo_key in self.vars_grupos_rep:
                    for var_name, var in self.vars_grupos_rep[grupo_key].items():
                        data[f'g{i}_{var_name}_rep'] = var.get()

        data['observacoes'] = self.text_obs.get("1.0", "end-1c")
        data['anexos'] = json.dumps(self.anexos_list)
        return data

    def salvar_rascunho(self):
        form_data = self._get_form_data()
        if not form_data.get("eqpto", "").strip():
            messagebox.showwarning("Campo Obrigatório", "O campo 'Eqpto' é obrigatório.", parent=self.parent_window)
            return
        self.controller.salvar_rascunho(self, form_data)

    def salvar_e_enviar(self):
        form_data = self._get_form_data()
        if not form_data.get("eqpto", "").strip():
            messagebox.showwarning("Campo Obrigatório", "O campo 'Eqpto' é obrigatório.", parent=self.parent_window)
            return
        self.controller.salvar_e_enviar(self, form_data)

    def reconstruir_lista_ajustes(self, *args):
        for widget in self.ajustes_items_frame.winfo_children(): widget.destroy()
        
        termo_busca = self.busca_ajustes_var.get().lower()
        ajustes_filtrados = [a for a in self.lista_ajustes_completa if a['eqpto'] and termo_busca in a['eqpto'].lower()]

        for item_data in ajustes_filtrados:
            eqpto, ns, data, alimentador = item_data['eqpto'], item_data['ns'], item_data['data'], item_data['alimentador']
            
            row = tk.Frame(self.ajustes_items_frame, bg='white')
            row.pack(fill='x', expand=True, pady=1)

            lbl_eqpto = tk.Label(row, text=eqpto or '', width=10, anchor='w', bg='white', padx=4, font=FONTE_PEQUENA)
            lbl_eqpto.grid(row=0, column=0, sticky='w')

            lbl_alimentador = tk.Label(row, text=alimentador or '', width=10, anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_alimentador.grid(row=0, column=1, sticky='w', padx=5)

            lbl_ns = tk.Label(row, text=f"NS: {ns or ''}", width=20, anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_ns.grid(row=0, column=2, sticky='w', padx=5)

            lbl_data = tk.Label(row, text=data or '', width=10, anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_data.grid(row=0, column=3, sticky='w', padx=5)
            
            for widget in (row, lbl_eqpto, lbl_ns, lbl_data, lbl_alimentador):
                widget.bind("<Double-1>", lambda e, eq=eqpto: self.carregar_ajuste_pelo_nome(eq))
        
        self.ajustes_canvas.yview_moveto(0)

    def reconstruir_lista_rascunhos(self, *args):
        for widget in self.rascunhos_items_frame.winfo_children(): widget.destroy()
        self.rascunho_check_vars.clear()
        
        termo_busca = self.busca_rascunhos_var.get().lower()
        rascunhos_filtrados = [r for r in self.lista_rascunhos_completa if r['eqpto'] and termo_busca in r['eqpto'].lower()]
        
        for item_data in rascunhos_filtrados:
            eqpto, ns, data, alimentador = item_data['eqpto'], item_data['ns'], item_data['data'], item_data['alimentador']
            
            var = tk.BooleanVar()
            self.rascunho_check_vars[eqpto] = var
            row = tk.Frame(self.rascunhos_items_frame, bg='white')
            row.pack(fill='x', expand=True, pady=1)
            
            check = ttk.Checkbutton(row, variable=var)
            check.grid(row=0, column=0, sticky='w')

            lbl_eqpto = tk.Label(row, text=eqpto or '', width=10, anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_eqpto.grid(row=0, column=1, sticky='w', padx=(5, 0))

            lbl_alimentador = tk.Label(row, text=alimentador or '', width=10, anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_alimentador.grid(row=0, column=2, sticky='w', padx=5)

            lbl_ns = tk.Label(row, text=f"NS: {ns or ''}", width=20, anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_ns.grid(row=0, column=3, sticky='w', padx=5)

            lbl_data = tk.Label(row, text=data or '', anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_data.grid(row=0, column=4, sticky='w', padx=5)

            row.grid_columnconfigure(5, weight=1)

            btn_del = tk.Button(row, text="X", fg="red", relief="flat", cursor="hand2", font=("Helvetica", 8, "bold"), command=lambda e=eqpto: self.deletar_rascunho_individual(e), bg='white')
            btn_del.grid(row=0, column=6, sticky='e', padx=(0,5))
            
            for widget in (lbl_eqpto, lbl_ns, lbl_data, lbl_alimentador):
                 widget.bind("<Double-1>", lambda e, eq=eqpto: self.carregar_rascunho_pelo_nome(eq))
        
        self.selecionar_tudo_rascunhos_var.set(False)
        self.rascunhos_canvas.yview_moveto(0)

    def atualizar_todas_as_listas(self):
        self.controller.atualizar_listas_memorial(self)

    def carregar_ajuste_pelo_nome(self, eqpto):
        self.controller.carregar_ficha_pelo_nome(self, eqpto, 'cadastros')

    def carregar_rascunho_pelo_nome(self, eqpto):
        self.controller.carregar_ficha_pelo_nome(self, eqpto, 'rascunhos')

    def preencher_formulario(self, dados_dict):
        self.limpar_formulario()
        for nome_campo, var in self.campos_dict.items():
            var.set(dados_dict.get(nome_campo.lower(), ""))
        
        # Preenche o primeiro bloco de tabelas
        for i in range(1, 4):
            if f'grupo_{i}' in self.vars_grupos:
                for nome_var, var_tk in self.vars_grupos[f'grupo_{i}'].items():
                    var_tk.set(dados_dict.get(f"g{i}_{nome_var}", ""))
        
        # Preenche o segundo bloco de tabelas (replicado)
        for i in range(1, 4):
             if f'grupo_{i}' in self.vars_grupos_rep:
                for nome_var, var_tk in self.vars_grupos_rep[f'grupo_{i}'].items():
                    var_tk.set(dados_dict.get(f"g{i}_{nome_var}_rep", ""))

        self.text_obs.insert("1.0", dados_dict.get("observacoes", ""))
        anexos_json = dados_dict.get("anexos", "[]")
        try:
            self.anexos_list = json.loads(anexos_json if anexos_json else "[]")
        except json.JSONDecodeError:
            self.anexos_list = []

    def abrir_janela_busca(self):
        messagebox.showinfo("Info", "Funcionalidade de busca detalhada em desenvolvimento.")

    def abrir_anexos(self):
        anexos_window = tk.Toplevel(self.parent_window)
        anexos_window.title("Gerenciar Anexos")
        anexos_window.geometry("500x350")
        anexos_window.transient(self.parent_window); anexos_window.grab_set()
        anexos_window.configure(bg='white')
        controls_frame = tk.Frame(anexos_window, bg='white'); controls_frame.pack(pady=10, padx=10, fill='x')
        add_frame = tk.Frame(controls_frame, bg='white'); add_frame.pack(side='left', padx=(0, 20))
        btn_add = tk.Button(add_frame, text="+", font=("Helvetica", 10, "bold"), relief="solid", bd=1, cursor="hand2", command=lambda: self.adicionar_arquivo(anexos_window))
        btn_add.pack(side='left', padx=(0, 5))
        tk.Label(add_frame, text="Adicionar", font=FONTE_PADRAO, bg='white').pack(side='left')
        remove_frame = tk.Frame(controls_frame, bg='white'); remove_frame.pack(side='left')
        btn_remove = tk.Button(remove_frame, text="-", font=("Helvetica", 10, "bold"), relief="solid", bd=1, cursor="hand2", command=lambda: self.remover_arquivo(anexos_window))
        btn_remove.pack(side='left', padx=(0, 5))
        tk.Label(remove_frame, text="Remover", font=FONTE_PADRAO, bg='white').pack(side='left')
        list_frame = tk.Frame(anexos_window, bg='white'); list_frame.pack(pady=10, padx=10, fill='both', expand=True)
        scrollbar = ttk.Scrollbar(list_frame); scrollbar.pack(side='right', fill='y')
        listbox_anexos = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED, font=FONTE_PEQUENA)
        listbox_anexos.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=listbox_anexos.yview)
        for anexo_path in self.anexos_list: listbox_anexos.insert(tk.END, os.path.basename(anexo_path))
        anexos_window.listbox = listbox_anexos

    def adicionar_arquivo(self, window):
        file_paths = filedialog.askopenfilenames(title="Selecionar arquivos", parent=window)
        if file_paths:
            for path in file_paths:
                if path not in self.anexos_list:
                    self.anexos_list.append(path)
                    window.listbox.insert(tk.END, os.path.basename(path))

    def remover_arquivo(self, window):
        selected_indices = window.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Nenhuma Seleção", "Selecione um ou mais arquivos para remover.", parent=window)
            return
        for i in sorted(selected_indices, reverse=True):
            self.anexos_list.pop(i)
            window.listbox.delete(i)

    def limpar_formulario(self):
        for var in self.campos_dict.values(): var.set("")
        self.campos_dict["Data"].set(datetime.now().strftime('%d/%m/%Y'))
        self.campos_dict["Telecontrolado"].set("sim")
        self.campos_dict["Vinculado a Acessante"].set("Não")
        self.campos_dict["Manobra Efetiva"].set("Não")

        for i in range(1, 4):
            if f'grupo_{i}' in self.vars_grupos:
                for var in self.vars_grupos[f'grupo_{i}'].values(): var.set("")
        
        for i in range(1, 4):
             if f'grupo_{i}' in self.vars_grupos_rep:
                for var in self.vars_grupos_rep[f'grupo_{i}'].values(): var.set("")

        self.text_obs.delete("1.0", "end")
        self.anexos_list.clear()
        print("Formulário limpo.")

if __name__ == '__main__':
    class DummyController:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("Teste do Módulo Memorial de Cálculo")
            self.root.geometry("1400x900")
            self.memorial_frame = MemorialCalculoFrame(self.root, self)
            self.memorial_frame.pack(fill="both", expand=True)
        def show_frame(self, page_name): pass
        def atualizar_listas_memorial(self, view): print("Atualizando listas...")
        def carregar_ficha_pelo_nome(self, view, eqpto, tabela): print(f"Carregando {eqpto} de {tabela}")
        def deletar_rascunhos(self, view, eq_list): print(f"Deletando rascunhos: {eq_list}")
        def salvar_rascunho(self, view, data): print("Salvando rascunho:", data.get('eqpto'))
        def salvar_e_enviar(self, view, data): print("Salvando e enviando:", data.get('eqpto'))

    app = DummyController()
    app.mainloop()
