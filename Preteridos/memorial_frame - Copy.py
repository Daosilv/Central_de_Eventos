import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import sqlite3
import shutil

# --- Configurações ---
FONTE_PADRAO = ("Times New Roman", 12)
FONTE_PEQUENA = ("Times New Roman", 10)
SIDEBAR_WIDTH = 300 

diretorio_local_ativo = r'C:\BD_APP_Cemig'
nome_arquivo_bd = 'Primeiro_banco.db'
caminho_bd_ativo = os.path.join(diretorio_local_ativo, nome_arquivo_bd)
diretorio_backup_onedrive = r'C:\Users\Israel\OneDrive - G4F SOLUÇÕES CORPORATIVAS\Treinamento ChatGPT\Treinamento Ficha de Ajuste\BD_APP_Cemig'

class MemorialCalculoFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Inicializa variáveis e colunas como atributos da classe
        self.campos_dict = {
            "Autor": tk.StringVar(), "Eqpto": tk.StringVar(), "Malha": tk.StringVar(), "Condição": tk.StringVar(),
            "Motivador": tk.StringVar(), "Alimentador": tk.StringVar(), "NS": tk.StringVar(), "Siom": tk.StringVar(),
            "Data": tk.StringVar(value=datetime.now().strftime('%d/%m/%Y')), "Coord": tk.StringVar(), "Endereço": tk.StringVar(),
            "Mídia": tk.StringVar(), "Fabricante": tk.StringVar(), "Modelo": tk.StringVar(), "Comando": tk.StringVar(),
            "Telecontrolado": tk.StringVar(value="sim"), "Bypass_1": tk.StringVar(), "Bypass_2": tk.StringVar()
        }
        self.colunas_db = ["id", "data_registro"] + [k.lower() for k in self.campos_dict.keys()]
        self.vars_grupos = {}
        
        # Centraliza a definição de largura das colunas
        self.col_widths = [90, 70, 85, 120, 120, 70, 85, 120, 120]
        
        # Atributos para guardar referências para o alinhamento
        self.frame_tabela_header = None
        self.tabelas_grupo_frames = []
        self.ref_cells = []

        # Registra comandos de validação
        self.vcmd_4 = self.register(self.limitar_4_caracteres)

        # Configura Trace para formatação automática
        self.campos_dict["Siom"].trace_add("write", self.formatar_siom)
        self.campos_dict["Coord"].trace_add("write", self.formatar_coord)

        # Cria a estrutura principal da UI deste módulo
        self.criar_layout_principal()
        
        # Cria o layout do formulário em si
        self.criar_layout_formulario()
        
        # Inicializa o banco de dados (verifica se tabelas existem)
        self.inicializar_banco()
        # Popula as listas na barra lateral
        self.atualizar_todas_as_listas()

        # Chama a função de alinhamento após a interface ser renderizada
        self.after(150, self.alinhar_coluna_critica)

    def criar_layout_principal(self):
        """Cria a estrutura de painéis (formulário à esquerda, histórico à direita)."""
        app_frame = tk.Frame(self)
        app_frame.pack(fill="both", expand=True)
        
        sidebar_frame = tk.LabelFrame(app_frame, text="Histórico", width=SIDEBAR_WIDTH, padx=5, pady=5)
        sidebar_frame.pack(side="right", fill="y", padx=10, pady=10)
        sidebar_frame.pack_propagate(False)
        
        main_content_frame = tk.Frame(app_frame)
        main_content_frame.pack(side="left", fill="both", expand=True)

        scroll_container = tk.Frame(main_content_frame)
        scroll_container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(scroll_container, highlightthickness=0)
        yscrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview)
        
        scroll_container.grid_rowconfigure(0, weight=1)
        scroll_container.grid_columnconfigure(0, weight=1)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        yscrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=yscrollbar.set)
        
        self.main_form_frame = tk.Frame(self.canvas, bd=1)
        self.canvas.create_window((0, 0), window=self.main_form_frame, anchor="nw")
        
        self.main_form_frame.bind("<Configure>", self.on_frame_configure)
        self.bind_all("<MouseWheel>", self._on_mouse_wheel)

        # --- Widgets do Painel Lateral ---
        btn_atualizar_listas = ttk.Button(sidebar_frame, text="Atualizar Listas", command=self.atualizar_todas_as_listas)
        btn_atualizar_listas.pack(fill='x', pady=(0, 10))
        
        lbl_local = tk.Label(sidebar_frame, text="Salvos no BD (Duplo-Clique para Carregar)")
        lbl_local.pack(fill='x')
        frame_local_list = tk.Frame(sidebar_frame)
        frame_local_list.pack(fill='both', expand=True, pady=5)
        scrollbar_local = ttk.Scrollbar(frame_local_list)
        scrollbar_local.pack(side='right', fill='y')
        self.listbox_local = tk.Listbox(frame_local_list, yscrollcommand=scrollbar_local.set)
        self.listbox_local.pack(side='left', fill='both', expand=True)
        scrollbar_local.config(command=self.listbox_local.yview)
        self.listbox_local.bind("<Double-1>", self.carregar_ficha_selecionada)
        
        lbl_backup = tk.Label(sidebar_frame, text="Backups na Nuvem")
        lbl_backup.pack(fill='x', pady=(10, 0))
        frame_backup_list = tk.Frame(sidebar_frame)
        frame_backup_list.pack(fill='both', expand=True, pady=5)
        scrollbar_backup = ttk.Scrollbar(frame_backup_list)
        scrollbar_backup.pack(side='right', fill='y')
        self.listbox_backup = tk.Listbox(frame_backup_list, yscrollcommand=scrollbar_backup.set)
        self.listbox_backup.pack(side='left', fill='both', expand=True)
        scrollbar_backup.config(command=self.listbox_backup.yview)

    def criar_layout_formulario(self):
        """Cria todos os widgets do formulário de preenchimento."""
        frame_campos = tk.Frame(self.main_form_frame)
        frame_campos.pack(pady=10, padx=10, fill="x")
        wrap_tabelas = tk.Frame(self.main_form_frame)
        wrap_tabelas.pack(pady=10, anchor="center")
        
        btn_voltar = ttk.Button(frame_campos, text="< Voltar ao Menu Principal", 
                                command=lambda: self.controller.show_frame("MenuFrame"))
        btn_voltar.pack(anchor='nw', pady=(0, 10))
        
        # --- Linhas do Cabeçalho (código omitido por brevidade) ---
        row1_frame = tk.Frame(frame_campos); row1_frame.pack(fill="x", pady=1)
        tk.Label(row1_frame, text="Autor", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        tk.Entry(row1_frame, textvariable=self.campos_dict["Autor"], relief="solid", bd=1, font=FONTE_PADRAO, width=40).pack(side="left", padx=(0,5))
        tk.Label(row1_frame, text="Data", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        tk.Entry(row1_frame, textvariable=self.campos_dict["Data"], relief="solid", bd=1, font=FONTE_PADRAO, width=11).pack(side="left", padx=(0,5))
        tk.Label(row1_frame, text="NS", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        tk.Entry(row1_frame, textvariable=self.campos_dict["NS"], relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left", padx=(0,5))

        row2_frame = tk.Frame(frame_campos); row2_frame.pack(fill="x", pady=1)
        tk.Label(row2_frame, text="Eqpto", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        tk.Entry(row2_frame, textvariable=self.campos_dict["Eqpto"], relief="solid", bd=1, font=FONTE_PADRAO, width=10).pack(side="left", padx=(0,5))
        opcoes_condicao = ["NA", "NF", "NA ABR", "NF LS", "P.O. NA", "P.O. NF", "P.O. SECC NA", "P.O. SECC NF", "SECC NA", "SECC NF", "PRIM", "SE RELI", "SE SECI", "ACESS INV", "ACESS S/ INV", "MONOF. NF", "MONOF. NA", "MONOF. SECC NA", "MONOF. SECC NF"]
        tk.Label(row2_frame, text="Condição", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        self.create_bordered_combobox(row2_frame, self.campos_dict["Condição"], opcoes_condicao, 16).pack(side="left", padx=(0,5))
        tk.Label(row2_frame, text="Coord", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        tk.Entry(row2_frame, textvariable=self.campos_dict["Coord"], relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left", padx=(0,5))
        opcoes_malha = ["Centro", "Leste", "Mantiqueira", "Norte", "Sul"]
        tk.Label(row2_frame, text="Malha", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        self.create_bordered_combobox(row2_frame, self.campos_dict["Malha"], opcoes_malha, 16).pack(side="left", padx=(0,5))
        tk.Label(row2_frame, text="Alimentador", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        tk.Entry(row2_frame, textvariable=self.campos_dict["Alimentador"], relief="solid", bd=1, font=FONTE_PADRAO, width=10).pack(side="left", padx=(0,5))

        row3_frame = tk.Frame(frame_campos); row3_frame.pack(fill="x", pady=1)
        opcoes_motivador = ["Instalação", "Reajuste", "Relocação"]
        tk.Label(row3_frame, text="Motivador", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        self.create_bordered_combobox(row3_frame, self.campos_dict["Motivador"], opcoes_motivador, 14).pack(side="left", padx=(0,5))
        tk.Label(row3_frame, text="Endereço", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        tk.Entry(row3_frame, textvariable=self.campos_dict["Endereço"], relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left", padx=(0,5), fill="x", expand=True)
        opcoes_midia = ["Celular", "Satélite", "Rádio", "Desconhecido", "Não enc."]
        tk.Label(row3_frame, text="Mídia", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        self.create_bordered_combobox(row3_frame, self.campos_dict["Mídia"], opcoes_midia, 14).pack(side="left", padx=(0,5))

        row4_frame = tk.Frame(frame_campos); row4_frame.pack(fill="x", pady=1)
        opcoes_fabricante = ["ABB", "AMPERA", "ARTECHE", "BRUSH", "COOPER", "GeW", "HSS", "McGRAW_EDISON", "NOJA", "NU_LEC", "REYROLLE", "ROMAGNOLE", "SIEMENS", "SCHNEIDER", "TAVRIDA", "WESTINGHOUSE", "WHIPP_BOURNE", "DESCONHECIDO", "SC_ElectricCompany"]
        tk.Label(row4_frame, text="Fabricante", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        self.create_bordered_combobox(row4_frame, self.campos_dict["Fabricante"], opcoes_fabricante, 28).pack(side="left", padx=(0,5))
        tk.Label(row4_frame, text="Modelo", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        tk.Entry(row4_frame, textvariable=self.campos_dict["Modelo"], relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left", padx=(0,5))
        tk.Label(row4_frame, text="Comando", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        tk.Entry(row4_frame, textvariable=self.campos_dict["Comando"], relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left", padx=(0,5))
        opcoes_telecontrolado = ["sim", "não"]
        tk.Label(row4_frame, text="Telecontrolado", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        self.create_bordered_combobox(row4_frame, self.campos_dict["Telecontrolado"], opcoes_telecontrolado, 8).pack(side="left", padx=(0,5))
        tk.Label(row4_frame, text="Siom", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left")
        tk.Entry(row4_frame, textvariable=self.campos_dict["Siom"], relief="solid", bd=1, font=FONTE_PADRAO, width=10).pack(side="left", padx=(0,5))

        row_bypass_frame = tk.Frame(frame_campos); row_bypass_frame.pack(fill="x", pady=1)
        tk.Label(row_bypass_frame, text="Bypass", relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left")
        opcoes_bypass = ["6", "8", "10", "12", "15", "20", "25", "30"]
        bypass1_cell = tk.Frame(row_bypass_frame, relief="solid", bd=1)
        bypass1_combo = ttk.Combobox(bypass1_cell, textvariable=self.campos_dict["Bypass_1"], values=opcoes_bypass, state="readonly", width=8, font=FONTE_PADRAO, style='Arrowless.TCombobox')
        bypass1_combo.bind("<Button-1>", self.open_dropdown_on_click); bypass1_combo.pack(fill='both', expand=True); bypass1_cell.pack(side="left", padx=(0,2))
        tk.Label(row_bypass_frame, text="-", bd=0, font=FONTE_PADRAO).pack(side="left", padx=2)
        tk.Entry(row_bypass_frame, textvariable=self.campos_dict["Bypass_2"], width=10, relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left")
        
        # --- Tabela de Cabeçalho ---
        self.frame_tabela_header = tk.Frame(wrap_tabelas, bd=1, relief="solid")
        for c, minsize in enumerate(self.col_widths): self.frame_tabela_header.grid_columnconfigure(c, minsize=minsize)
        for r in range(3): self.frame_tabela_header.grid_rowconfigure(r, minsize=30, weight=1)
        self._cell(self.frame_tabela_header, 0, 0, "Grupo Normal = Grupo de Consumo", cs=9); self._cell(self.frame_tabela_header, 1, 0, "  Grupos  ", rs=2)
        self._cell(self.frame_tabela_header, 1, 1, "FASE", cs=4); self._cell(self.frame_tabela_header, 1, 5, "TERRA", cs=4)
        self._cell(self.frame_tabela_header, 2, 1, "  Pickup  "); self._cell(self.frame_tabela_header, 2, 2, "  Sequência  "); self._cell(self.frame_tabela_header, 2, 3, "  Curva Lenta  ")
        self._cell(self.frame_tabela_header, 2, 4, "  Curva Rápida  "); self._cell(self.frame_tabela_header, 2, 5, "  Pickup  "); self._cell(self.frame_tabela_header, 2, 6, "  Sequência  ")
        self._cell(self.frame_tabela_header, 2, 7, "  Curva Lenta  "); self._cell(self.frame_tabela_header, 2, 8, "  Curva Rápida  ")
        self.frame_tabela_header.pack(pady=5)
        
        # --- Tabelas de Grupo ---
        for i in range(1, 4):
            tabela_frame, ref_cell, group_vars = self.criar_tabela_grupo(wrap_tabelas, f"  Grupo {i}  ")
            self.vars_grupos[f'grupo_{i}'] = group_vars
            self.tabelas_grupo_frames.append(tabela_frame)
            self.ref_cells.append(ref_cell)
            for var_name in group_vars: self.colunas_db.append(f"g{i}_{var_name}")
        self.colunas_db.append("observacoes")

        # --- Botões de Ação ---
        botoes_frame = tk.Frame(self.main_form_frame)
        botoes_frame.pack(pady=20)
        btn_carregar = ttk.Button(botoes_frame, text="Buscar", command=self.abrir_janela_busca)
        btn_carregar.pack(side="left", padx=5)
        btn_backup = ttk.Button(botoes_frame, text="Fazer Backup", command=self.fazer_backup_nuvem)
        btn_backup.pack(side="left", padx=5)
        btn_salvar_enviar = ttk.Button(botoes_frame, text="Salvar", command=self.salvar_e_enviar)
        btn_salvar_enviar.pack(side="left", padx=5)
        btn_limpar = ttk.Button(botoes_frame, text="Limpar", command=self.limpar_formulario)
        btn_limpar.pack(side="left", padx=5)

        # --- Campo de Observações ---
        frame_obs = tk.Frame(self.main_form_frame)
        frame_obs.pack(pady=(10, 5), padx=10, fill='x', expand=False)
        lbl_obs = tk.Label(frame_obs, text="Observações:", font=FONTE_PADRAO); lbl_obs.pack(anchor='w')
        text_container = tk.Frame(frame_obs, height=120, relief="solid", bd=1); text_container.pack(fill='x', expand=False)
        text_container.pack_propagate(False)
        self.text_obs = tk.Text(text_container, relief="flat", bd=0, font=FONTE_PADRAO); self.text_obs.pack(fill="both", expand=True)
    
    # =====================================================================================
    # === MÉTODOS DE LÓGICA E SUPORTE (ANTIGAS FUNÇÕES GLOBAIS) ===
    # =====================================================================================

    def alinhar_coluna_critica(self):
        """Mede a largura real da coluna de referência e aplica a todas as tabelas."""
        self.update_idletasks()  # Força a UI a terminar os cálculos de geometria
        if not self.ref_cells:
            return

        # Pega a largura real renderizada da célula de referência (coluna "Curva Lenta")
        reference_width = self.ref_cells[0].winfo_width()

        if reference_width > 1:  # Checagem de segurança
            # Aplica a largura medida à 4ª coluna (índice 3) da tabela de cabeçalho
            if self.frame_tabela_header:
                self.frame_tabela_header.grid_columnconfigure(3, minsize=reference_width)

            # Aplica a mesma largura a todas as tabelas de grupo
            for table in self.tabelas_grupo_frames:
                table.grid_columnconfigure(3, minsize=reference_width)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mouse_wheel(self, event):
        direction = -1 if (event.num == 4 or event.delta > 0) else 1
        self.canvas.yview_scroll(direction, "units")

    def open_dropdown_on_click(self, event):
        event.widget.after(5, lambda: event.widget.event_generate('<Down>'))

    def _cell(self, frame, r, c, txt="", rs=1, cs=1, sticky="nsew"):
        outer = tk.Frame(frame, relief="solid", bd=1)
        outer.grid(row=r, column=c, rowspan=rs, columnspan=cs, sticky=sticky)
        if txt:
            lbl = tk.Label(outer, text=txt, font=FONTE_PADRAO)
            lbl.pack(fill="both", expand=True)
        return outer

    def limitar_4_caracteres(self, P):
        return len(P) <= 4

    def formatar_siom(self, *args):
        valor = ''.join(filter(str.isdigit, self.campos_dict["Siom"].get().replace("-", "")))
        if len(valor) > 7: valor = valor[:7]
        if len(valor) > 5: valor = valor[:5] + '-' + valor[5:]
        self.campos_dict["Siom"].set(valor)

    def formatar_coord(self, *args):
        valor = ''.join(filter(str.isdigit, self.campos_dict["Coord"].get().replace(":", "")))
        if len(valor) > 13: valor = valor[:13]
        if len(valor) > 6: valor = valor[:6] + ':' + valor[6:]
        self.campos_dict["Coord"].set(valor)

    def create_bordered_combobox(self, parent, var, values, width):
        cell_frame = tk.Frame(parent, relief="solid", bd=1)
        combobox = ttk.Combobox(cell_frame, textvariable=var, values=values, state="readonly", width=width, font=FONTE_PADRAO, style='Arrowless.TCombobox')
        combobox.bind("<Button-1>", self.open_dropdown_on_click)
        combobox.pack(fill="both", expand=True)
        return cell_frame

    def criar_tabela_grupo(self, parent, group_name):
        group_vars = {
            "pickup_fase": tk.StringVar(), "sequencia": tk.StringVar(), "curva_lenta_tipo": tk.StringVar(),
            "curva_lenta_dial": tk.StringVar(), "curva_lenta_tadic": tk.StringVar(), "curva_rapida_dial": tk.StringVar(),
            "curva_rapida_tadic": tk.StringVar(), "pickup_terra": tk.StringVar(), "sequencia_terra": tk.StringVar(),
            "terra_tempo_lenta": tk.StringVar(), "terra_tempo_rapida": tk.StringVar(),
        }
        frame_tabela = tk.Frame(parent, bd=1, relief="solid")
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
            if novo_estado == 'disabled':
                group_vars["curva_rapida_dial"].set(''); group_vars["curva_rapida_tadic"].set(''); group_vars["terra_tempo_rapida"].set('')

        group_vars["sequencia"].trace_add("write", _atualizar_sequencia_terra)
        group_vars["sequencia"].trace_add("write", _gerenciar_campos_curva_rapida)
        
        tk.Label(frame_tabela, text=group_name, relief="solid", bd=1, font=FONTE_PADRAO).grid(row=1, column=0, rowspan=3, sticky="nsew")
        tk.Label(frame_tabela, text="FASE", relief="solid", bd=1, font=FONTE_PADRAO).grid(row=1, column=1, columnspan=2, sticky="nsew")
        opcoes_curva_lenta = ["IEC Muito Inversa", "IEC Ext. Inversa"]
        lenta_fase_cell = tk.Frame(frame_tabela, relief="solid", bd=1)
        combobox_lenta_fase = ttk.Combobox(lenta_fase_cell, textvariable=group_vars["curva_lenta_tipo"], values=opcoes_curva_lenta, state="readonly", font=FONTE_PEQUENA, justify="center", style='Arrowless.TCombobox')
        combobox_lenta_fase.bind("<Button-1>", self.open_dropdown_on_click); combobox_lenta_fase.pack(fill='both', expand=True); lenta_fase_cell.grid(row=1, column=3, sticky="nsew")
        self._cell(frame_tabela, 1, 4, "IEC Inversa")
        tk.Label(frame_tabela, text="TERRA", relief="solid", bd=1, font=FONTE_PADRAO).grid(row=1, column=5, columnspan=2, sticky="nsew")
        tk.Label(frame_tabela, text="T. Definido", relief="solid", bd=1, font=FONTE_PADRAO).grid(row=1, column=7, sticky="nsew"); tk.Label(frame_tabela, text="T. Definido", relief="solid", bd=1, font=FONTE_PADRAO).grid(row=1, column=8, sticky="nsew")
        cell_pickup_fase = tk.Frame(frame_tabela, relief="solid", bd=1); cell_pickup_fase.grid_propagate(False); cell_pickup_fase.grid(row=1, column=1, rowspan=3, sticky="nsew")
        tk.Entry(cell_pickup_fase, textvariable=group_vars["pickup_fase"], font=FONTE_PADRAO, width=4, relief="flat", justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).pack(fill="both", expand=True)
        opcoes_sequencia = ["1L", "2L", "3L", "1R+3L", "1R+2L", "2R+2L"]
        cell_sequencia = tk.Frame(frame_tabela, relief="solid", bd=1); cell_sequencia.grid_propagate(False); cell_sequencia.grid(row=1, column=2, rowspan=3, sticky="nsew")
        combobox_sequencia_fase = ttk.Combobox(cell_sequencia, textvariable=group_vars["sequencia"], values=opcoes_sequencia, state="readonly", font=FONTE_PADRAO, justify="center", width=8, style='Arrowless.TCombobox')
        combobox_sequencia_fase.bind("<Button-1>", self.open_dropdown_on_click); combobox_sequencia_fase.pack(fill="both", expand=True)
        cell_pickup_terra = tk.Frame(frame_tabela, relief="solid", bd=1); cell_pickup_terra.grid_propagate(False); cell_pickup_terra.grid(row=1, column=5, rowspan=3, sticky="nsew")
        tk.Entry(cell_pickup_terra, textvariable=group_vars["pickup_terra"], font=FONTE_PADRAO, width=4, relief="flat", justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).pack(fill="both", expand=True)
        cell_sequencia_terra = tk.Frame(frame_tabela, relief="solid", bd=1); cell_sequencia_terra.grid_propagate(False); cell_sequencia_terra.grid(row=1, column=6, rowspan=3, sticky="nsew")
        tk.Label(cell_sequencia_terra, textvariable=group_vars["sequencia_terra"], font=FONTE_PADRAO, justify="center").pack(fill="both", expand=True)
        subframe_lenta = tk.Frame(frame_tabela, bd=0); subframe_lenta.grid_propagate(False); subframe_lenta.grid(row=2, column=3, rowspan=2, sticky="nsew")
        for r in range(2): subframe_lenta.grid_rowconfigure(r, weight=1);
        for c in range(2): subframe_lenta.grid_columnconfigure(c, weight=1)
        tk.Label(subframe_lenta, text="Dial", font=FONTE_PADRAO, width=8, relief="solid", bd=1).grid(row=0, column=0, sticky="nsew"); tk.Label(subframe_lenta, text="T. Adic.", font=FONTE_PADRAO, width=8, relief="solid", bd=1).grid(row=0, column=1, sticky="nsew")
        tk.Entry(subframe_lenta, textvariable=group_vars["curva_lenta_dial"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=1, column=0, sticky="nsew")
        tk.Entry(subframe_lenta, textvariable=group_vars["curva_lenta_tadic"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=1, column=1, sticky="nsew")
        subframe_rapida = tk.Frame(frame_tabela, bd=0); subframe_rapida.grid_propagate(False); subframe_rapida.grid(row=2, column=4, rowspan=2, sticky="nsew")
        for r in range(2): subframe_rapida.grid_rowconfigure(r, weight=1)
        for c in range(2): subframe_rapida.grid_columnconfigure(c, weight=1)
        tk.Label(subframe_rapida, text="Dial", font=FONTE_PADRAO, width=8, relief="solid", bd=1).grid(row=0, column=0, sticky="nsew"); tk.Label(subframe_rapida, text="T. Adic.", font=FONTE_PADRAO, width=8, relief="solid", bd=1).grid(row=0, column=1, sticky="nsew")
        entry_fase_rapida_dial = tk.Entry(subframe_rapida, textvariable=group_vars["curva_rapida_dial"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_fase_rapida_dial.grid(row=1, column=0, sticky="nsew")
        entry_fase_rapida_tadic = tk.Entry(subframe_rapida, textvariable=group_vars["curva_rapida_tadic"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_fase_rapida_tadic.grid(row=1, column=1, sticky="nsew")
        self._cell(frame_tabela, 2, 7, "Tempo (s)"); self._cell(frame_tabela, 2, 8, "Tempo (s)")
        tk.Entry(frame_tabela, textvariable=group_vars["terra_tempo_lenta"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=3, column=7, sticky="nsew")
        entry_terra_rapida_tempo = tk.Entry(frame_tabela, textvariable=group_vars["terra_tempo_rapida"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_terra_rapida_tempo.grid(row=3, column=8, sticky="nsew")
        frame_tabela.pack(pady=(0, 5))
        return frame_tabela, lenta_fase_cell, group_vars

    def inicializar_banco(self):
        try:
            os.makedirs(diretorio_local_ativo, exist_ok=True)
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                colunas_para_criar = [c for c in self.colunas_db if c not in ['id', 'data_registro']]
                colunas_sql = ', '.join([f'"{c}" TEXT' for c in colunas_para_criar])
                comando_sql = f"CREATE TABLE IF NOT EXISTS cadastros (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})"
                cursor.execute(comando_sql)
        except Exception as e:
            messagebox.showerror("Erro Crítico", f"Não foi possível criar o banco de dados: {e}")
            self.controller.destroy()

    def limpar_formulario(self):
        for var in self.campos_dict.values(): var.set("")
        self.campos_dict["Data"].set(datetime.now().strftime('%d/%m/%Y'))
        self.campos_dict["Telecontrolado"].set("sim")
        for i in range(1, 4):
            if f'grupo_{i}' in self.vars_grupos:
                for var in self.vars_grupos[f'grupo_{i}'].values(): var.set("")
        self.text_obs.delete("1.0", "end")
        print("Formulário limpo.")

    def salvar_e_enviar(self):
        if not self.campos_dict["Eqpto"].get().strip():
            messagebox.showwarning("Campo Obrigatório", "O campo 'Eqpto' é obrigatório.")
            return
        try:
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                nomes_colunas = [c for c in self.colunas_db if c not in ['id', 'data_registro']]
                valores = [self.campos_dict[k].get() for k in self.campos_dict.keys()]
                for i in range(1, 4):
                    valores.extend([v.get() for v in self.vars_grupos[f'grupo_{i}'].values()])
                valores.append(self.text_obs.get("1.0", "end-1c"))
                placeholders = ', '.join(['?'] * len(nomes_colunas))
                sql_nomes_colunas = ', '.join([f'"{c}"' for c in nomes_colunas])
                comando_sql = f"INSERT INTO cadastros ({sql_nomes_colunas}) VALUES ({placeholders})"
                cursor.execute(comando_sql, tuple(valores))
            messagebox.showinfo("Sucesso", "Ficha salva com sucesso!")
            self.limpar_formulario()
            self.atualizar_todas_as_listas()
        except sqlite3.Error as e: messagebox.showerror("Erro de Banco de Dados", f"Erro ao salvar: {e}")

    def fazer_backup_nuvem(self):
        eqpto_atual = self.campos_dict["Eqpto"].get().strip()
        if not eqpto_atual:
            messagebox.showwarning("Campo Obrigatório", "O campo 'Eqpto' deve ser preenchido para nomear o backup.")
            return
        if not os.path.exists(caminho_bd_ativo):
            messagebox.showwarning("Backup", "Salve uma ficha antes de fazer o primeiro backup.")
            return
        try:
            os.makedirs(diretorio_backup_onedrive, exist_ok=True)
            nome_backup = f"{eqpto_atual}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.db"
            caminho_backup_completo = os.path.join(diretorio_backup_onedrive, nome_backup)
            shutil.copy2(caminho_bd_ativo, caminho_backup_completo)
            messagebox.showinfo("Backup Concluído", f"Backup para Eqpto '{eqpto_atual}' salvo na nuvem!")
            self.atualizar_lista_backups()
        except Exception as e: messagebox.showerror("Erro de Backup", f"Não foi possível criar o backup: {e}")

    def atualizar_lista_local(self):
        self.listbox_local.delete(0, tk.END)
        try:
            if not os.path.exists(caminho_bd_ativo): return
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                cursor.execute("SELECT DISTINCT eqpto FROM cadastros WHERE eqpto != '' ORDER BY data_registro DESC")
                for eq in cursor.fetchall(): self.listbox_local.insert(tk.END, eq[0])
        except sqlite3.Error as e: print(f"Erro ao ler BD local: {e}")

    def atualizar_lista_backups(self):
        self.listbox_backup.delete(0, tk.END)
        try:
            if not os.path.exists(diretorio_backup_onedrive): return
            files = sorted([f for f in os.listdir(diretorio_backup_onedrive) if f.endswith('.db')], reverse=True)
            for f in files: self.listbox_backup.insert(tk.END, f)
        except Exception as e: print(f"Erro ao ler pasta de backup: {e}")

    def atualizar_todas_as_listas(self):
        self.atualizar_lista_local()
        self.atualizar_lista_backups()
    
    def carregar_ficha_por_id(self, id_ficha, janela_pai=None):
        try:
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                conexao.row_factory = sqlite3.Row
                cursor = conexao.cursor()
                cursor.execute(f"SELECT * FROM cadastros WHERE id = ?", (id_ficha,))
                dados_row = cursor.fetchone()
            if dados_row:
                self.limpar_formulario()
                dados_dict = dict(dados_row)
                for nome_campo, var in self.campos_dict.items():
                    var.set(dados_dict.get(nome_campo.lower(), ""))
                for i in range(1, 4):
                    for nome_var, var_tk in self.vars_grupos[f'grupo_{i}'].items():
                        var_tk.set(dados_dict.get(f"g{i}_{nome_var}", ""))
                self.text_obs.insert("1.0", dados_dict.get("observacoes", ""))
                if janela_pai: janela_pai.destroy()
            else: messagebox.showerror("Erro", "ID da ficha não encontrado.")
        except sqlite3.Error as e: messagebox.showerror("Erro de Banco de Dados", f"Erro ao carregar ficha: {e}")

    def carregar_ficha_selecionada(self, event=None):
        if not self.listbox_local.curselection(): return
        eqpto = self.listbox_local.get(self.listbox_local.curselection()[0])
        try:
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                cursor.execute("SELECT id FROM cadastros WHERE eqpto = ? ORDER BY data_registro DESC LIMIT 1", (eqpto,))
                resultado = cursor.fetchone()
            if resultado: self.carregar_ficha_por_id(resultado[0])
            else: messagebox.showinfo("Info", f"Nenhum registro encontrado para {eqpto}.")
        except sqlite3.Error as e: messagebox.showerror("Erro de Banco de Dados", f"Erro ao buscar ficha: {e}")

    def abrir_janela_busca(self):
        busca_window = tk.Toplevel(self)
        busca_window.title("Buscar Histórico de Equipamento")
        busca_window.geometry("500x400")
        busca_window.transient(self)
        busca_window.grab_set()
        
        frame_busca = tk.Frame(busca_window, padx=10, pady=10)
        frame_busca.pack(fill='x')
        tk.Label(frame_busca, text="Eqpto:").pack(side='left')
        entry_busca = tk.Entry(frame_busca)
        entry_busca.pack(side='left', fill='x', expand=True, padx=5)
        
        frame_resultados = tk.Frame(busca_window, padx=10, pady=5)
        frame_resultados.pack(fill='both', expand=True)
        scrollbar_busca = ttk.Scrollbar(frame_resultados)
        scrollbar_busca.pack(side='right', fill='y')
        listbox_resultados = tk.Listbox(frame_resultados, yscrollcommand=scrollbar_busca.set)
        listbox_resultados.pack(fill='both', expand=True)
        scrollbar_busca.config(command=listbox_resultados.yview)
        
        def executar_busca():
            listbox_resultados.delete(0, tk.END)
            eqpto_procurado = entry_busca.get().strip()
            if not eqpto_procurado: return
            try:
                with sqlite3.connect(caminho_bd_ativo) as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("SELECT id, data_registro FROM cadastros WHERE eqpto = ? ORDER BY data_registro DESC", (eqpto_procurado,))
                    resultados = cursor.fetchall()
                if not resultados:
                    messagebox.showinfo("Não Encontrado", f"Nenhum histórico para '{eqpto_procurado}'.", parent=busca_window)
                    return
                for id_ficha, data in resultados:
                    data_f = datetime.strptime(data.split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M:%S')
                    listbox_resultados.insert(tk.END, f"{id_ficha}: {eqpto_procurado} (salvo em {data_f})")
            except sqlite3.Error as e: messagebox.showerror("Erro", f"Erro ao buscar: {e}", parent=busca_window)
        
        btn_buscar = ttk.Button(frame_busca, text="Buscar", command=executar_busca)
        btn_buscar.pack(side='left')
        
        def carregar_versao_selecionada():
            if not listbox_resultados.curselection():
                messagebox.showwarning("Seleção", "Selecione uma versão para carregar.", parent=busca_window)
                return
            id_ficha = int(listbox_resultados.get(listbox_resultados.curselection()[0]).split(':')[0])
            self.carregar_ficha_por_id(id_ficha, busca_window)

        btn_carregar_versao = ttk.Button(busca_window, text="Carregar Versão Selecionada", command=carregar_versao_selecionada)
        btn_carregar_versao.pack(pady=10)


# --- Bloco de Execução para Teste Individual ---
if __name__ == '__main__':
    class DummyController(tk.Tk):
        """Classe controladora falsa para testar este frame de forma isolada."""
        def __init__(self):
            super().__init__()
            self.title("Teste do Módulo Memorial de Cálculo")
            self.geometry("1400x900")
        
        def show_frame(self, page_name):
            print(f"Simulando navegação para: {page_name}")
            self.destroy() # Fecha a janela de teste ao tentar voltar ao menu

    app = DummyController()
    memorial_frame = MemorialCalculoFrame(app, app)
    memorial_frame.pack(fill="both", expand=True)
    app.mainloop()
