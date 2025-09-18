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

class MemorialCalculoFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Variáveis de busca e seleção ---
        self.busca_ajustes_var = tk.StringVar()
        self.lista_ajustes_completa = []
        self.busca_ajustes_var.trace_add("write", self._filtrar_ajustes_recentes)

        self.busca_rascunhos_var = tk.StringVar()
        self.lista_rascunhos_completa = []
        self.rascunho_check_vars = {} # Mapeia eqpto -> tk.BooleanVar para cada item
        self.selecionar_tudo_rascunhos_var = tk.BooleanVar()
        self.busca_rascunhos_var.trace_add("write", self.reconstruir_lista_rascunhos)

        self.busca_concluidos_var = tk.StringVar()
        self.lista_concluidos_completa = []
        self.busca_concluidos_var.trace_add("write", self._filtrar_concluidos)

        self.campos_dict = {
            "Autor": tk.StringVar(), "Eqpto": tk.StringVar(), "Malha": tk.StringVar(), "Condição": tk.StringVar(),
            "Motivador": tk.StringVar(), "Alimentador": tk.StringVar(), "NS": tk.StringVar(), "Siom": tk.StringVar(),
            "Data": tk.StringVar(value=datetime.now().strftime('%d/%m/%Y')), "Coord": tk.StringVar(), "Endereço": tk.StringVar(),
            "Mídia": tk.StringVar(), "Fabricante": tk.StringVar(), "Modelo": tk.StringVar(), "Comando": tk.StringVar(),
            "Telecontrolado": tk.StringVar(value="sim"), "Bypass_1": tk.StringVar(), "Bypass_2": tk.StringVar()
        }
        self.colunas_db = ["id", "data_registro"] + [k.lower() for k in self.campos_dict.keys()]
        self.vars_grupos = {}
        self.col_widths = [90, 70, 85, 120, 120, 70, 85, 120, 120]
        self.frame_tabela_header = None
        self.tabelas_grupo_frames = []
        self.ref_cells = []
        self.vcmd_4 = self.register(self.limitar_4_caracteres)
        self.campos_dict["Siom"].trace_add("write", self.formatar_siom)
        self.campos_dict["Coord"].trace_add("write", self.formatar_coord)
        self.criar_layout_principal()
        self.criar_layout_formulario()
        self.inicializar_banco()
        self.atualizar_todas_as_listas()
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

        # Container do formulário com scroll
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
        
        ajustes_container = tk.LabelFrame(sidebar_frame, text="Ajustes Recentes", padx=5, pady=5)
        ajustes_container.pack(fill='both', expand=True, pady=(0, 5))

        frame_busca_ajustes = tk.Frame(ajustes_container)
        frame_busca_ajustes.pack(fill='x')
        tk.Label(frame_busca_ajustes, text="Buscar:").pack(side='left')
        tk.Entry(frame_busca_ajustes, textvariable=self.busca_ajustes_var).pack(side='left', fill='x', expand=True, padx=5)

        frame_local_list = tk.Frame(ajustes_container)
        frame_local_list.pack(fill='both', expand=True, pady=(5,0))
        scrollbar_local = ttk.Scrollbar(frame_local_list)
        scrollbar_local.pack(side='right', fill='y')
        self.listbox_local = tk.Listbox(frame_local_list, yscrollcommand=scrollbar_local.set)
        self.listbox_local.pack(side='left', fill='both', expand=True)
        scrollbar_local.config(command=self.listbox_local.yview)
        self.listbox_local.bind("<Double-1>", self.carregar_ficha_selecionada)
        
        rascunhos_container = tk.LabelFrame(sidebar_frame, text="Rascunhos", padx=5, pady=5)
        rascunhos_container.pack(fill='both', expand=True, pady=(5, 5))

        frame_busca_rascunhos = tk.Frame(rascunhos_container)
        frame_busca_rascunhos.pack(fill='x')
        tk.Label(frame_busca_rascunhos, text="Buscar:").pack(side='left')
        tk.Entry(frame_busca_rascunhos, textvariable=self.busca_rascunhos_var).pack(side='left', fill='x', expand=True, padx=5)

        frame_rascunhos_actions = tk.Frame(rascunhos_container)
        frame_rascunhos_actions.pack(fill='x', pady=(5,0))
        ttk.Checkbutton(frame_rascunhos_actions, text="Selecionar Tudo", variable=self.selecionar_tudo_rascunhos_var, command=self._toggle_selecionar_tudo_rascunhos).pack(side='left')
        tk.Button(frame_rascunhos_actions, text="X", fg="red", font=("Helvetica", 10, "bold"), command=self.deletar_rascunhos_selecionados, width=2, relief="flat", cursor="hand2").pack(side='right', padx=(0,5))
        
        rascunhos_canvas_frame = tk.Frame(rascunhos_container)
        rascunhos_canvas_frame.pack(fill='both', expand=True, pady=5)
        self.rascunhos_canvas = tk.Canvas(rascunhos_canvas_frame, highlightthickness=0)
        rascunhos_scrollbar = ttk.Scrollbar(rascunhos_canvas_frame, orient="vertical", command=self.rascunhos_canvas.yview)
        self.rascunhos_items_frame = tk.Frame(self.rascunhos_canvas)
        self.rascunhos_canvas.create_window((0, 0), window=self.rascunhos_items_frame, anchor="nw")
        self.rascunhos_canvas.configure(yscrollcommand=rascunhos_scrollbar.set)
        rascunhos_scrollbar.pack(side="right", fill="y")
        self.rascunhos_canvas.pack(side="left", fill="both", expand=True)
        self.rascunhos_items_frame.bind("<Configure>", lambda e: self.rascunhos_canvas.configure(scrollregion=self.rascunhos_canvas.bbox("all")))

        concluidos_container = tk.LabelFrame(sidebar_frame, text="Concluídos", padx=5, pady=5)
        concluidos_container.pack(fill='both', expand=True, pady=(5, 0))

        frame_busca_concluidos = tk.Frame(concluidos_container)
        frame_busca_concluidos.pack(fill='x')
        tk.Label(frame_busca_concluidos, text="Buscar:").pack(side='left')
        tk.Entry(frame_busca_concluidos, textvariable=self.busca_concluidos_var).pack(side='left', fill='x', expand=True, padx=5)

        frame_concluidos_list = tk.Frame(concluidos_container)
        frame_concluidos_list.pack(fill='both', expand=True, pady=(5,0))
        scrollbar_concluidos = ttk.Scrollbar(frame_concluidos_list)
        scrollbar_concluidos.pack(side='right', fill='y')
        self.listbox_concluidos = tk.Listbox(frame_concluidos_list, yscrollcommand=scrollbar_concluidos.set)
        self.listbox_concluidos.pack(side='left', fill='both', expand=True)
        scrollbar_concluidos.config(command=self.listbox_concluidos.yview)


    def criar_layout_formulario(self):
        frame_campos = tk.Frame(self.main_form_frame)
        frame_campos.pack(pady=10, padx=10, fill="x")
        wrap_tabelas = tk.Frame(self.main_form_frame)
        wrap_tabelas.pack(pady=10, anchor="center")
        
        btn_voltar = ttk.Button(frame_campos, text="< Voltar ao Menu Principal", 
                                command=lambda: self.controller.show_frame("MenuFrame"))
        btn_voltar.pack(anchor='nw', pady=(0, 10))
        
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
        
        self.frame_tabela_header = tk.Frame(wrap_tabelas, bd=1, relief="solid")
        for c, minsize in enumerate(self.col_widths): self.frame_tabela_header.grid_columnconfigure(c, minsize=minsize)
        for r in range(3): self.frame_tabela_header.grid_rowconfigure(r, minsize=30, weight=1)
        self._cell(self.frame_tabela_header, 0, 0, "Grupo Normal = Grupo de Consumo", cs=9); self._cell(self.frame_tabela_header, 1, 0, "  Grupos  ", rs=2)
        self._cell(self.frame_tabela_header, 1, 1, "FASE", cs=4); self._cell(self.frame_tabela_header, 1, 5, "TERRA", cs=4)
        self._cell(self.frame_tabela_header, 2, 1, "  Pickup  "); self._cell(self.frame_tabela_header, 2, 2, "  Sequência  "); self._cell(self.frame_tabela_header, 2, 3, "  Curva Lenta  ")
        self._cell(self.frame_tabela_header, 2, 4, "  Curva Rápida  "); self._cell(self.frame_tabela_header, 2, 5, "  Pickup  "); self._cell(self.frame_tabela_header, 2, 6, "  Sequência  ")
        self._cell(self.frame_tabela_header, 2, 7, "  Curva Lenta  "); self._cell(self.frame_tabela_header, 2, 8, "  Curva Rápida  ")
        self.frame_tabela_header.pack(pady=5)
        for i in range(1, 4):
            tabela_frame, ref_cell, group_vars = self.criar_tabela_grupo(wrap_tabelas, f"  Grupo {i}  ")
            self.vars_grupos[f'grupo_{i}'] = group_vars
            self.tabelas_grupo_frames.append(tabela_frame)
            self.ref_cells.append(ref_cell)
            for var_name in group_vars: self.colunas_db.append(f"g{i}_{var_name}")
        self.colunas_db.append("observacoes")
        botoes_frame = tk.Frame(self.main_form_frame)
        botoes_frame.pack(pady=20)
        btn_buscar = ttk.Button(botoes_frame, text="Buscar", command=self.abrir_janela_busca)
        btn_buscar.pack(side="left", padx=5)
        btn_salvar_rascunho = ttk.Button(botoes_frame, text="Salvar Rascunho", command=self.salvar_rascunho)
        btn_salvar_rascunho.pack(side="left", padx=5)
        btn_salvar_enviar = ttk.Button(botoes_frame, text="Salvar e Enviar", command=self.salvar_e_enviar)
        btn_salvar_enviar.pack(side="left", padx=5)
        btn_limpar = ttk.Button(botoes_frame, text="Limpar", command=self.limpar_formulario)
        btn_limpar.pack(side="left", padx=5)
        frame_obs = tk.Frame(self.main_form_frame)
        frame_obs.pack(pady=(10, 5), padx=10, fill='x', expand=False)
        lbl_obs = tk.Label(frame_obs, text="Observações:", font=FONTE_PADRAO); lbl_obs.pack(anchor='w')
        text_container = tk.Frame(frame_obs, height=120, relief="solid", bd=1); text_container.pack(fill='x', expand=False)
        text_container.pack_propagate(False)
        self.text_obs = tk.Text(text_container, relief="flat", bd=0, font=FONTE_PADRAO); self.text_obs.pack(fill="both", expand=True)

    def _filtrar_lista(self, termo_busca, lista_completa, listbox):
        termo = termo_busca.get().lower()
        listbox.delete(0, tk.END)
        if not termo:
            for item in lista_completa:
                listbox.insert(tk.END, item)
        else:
            for item in lista_completa:
                if termo in item.lower():
                    listbox.insert(tk.END, item)

    def _filtrar_ajustes_recentes(self, *args):
        self._filtrar_lista(self.busca_ajustes_var, self.lista_ajustes_completa, self.listbox_local)

    def _filtrar_concluidos(self, *args):
        self._filtrar_lista(self.busca_concluidos_var, self.lista_concluidos_completa, self.listbox_concluidos)

    def _toggle_selecionar_tudo_rascunhos(self):
        estado_selecao = self.selecionar_tudo_rascunhos_var.get()
        for var in self.rascunho_check_vars.values():
            var.set(estado_selecao)

    def deletar_rascunho_individual(self, eqpto_para_deletar):
        confirm = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Você tem certeza que deseja deletar permanentemente o rascunho para '{eqpto_para_deletar}'?"
        )
        if confirm:
            try:
                with sqlite3.connect(caminho_bd_ativo) as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("DELETE FROM rascunhos WHERE eqpto = ?", (eqpto_para_deletar,))
                self.reconstruir_lista_rascunhos()
            except sqlite3.Error as e:
                messagebox.showerror("Erro de Banco de Dados", f"Não foi possível deletar o rascunho: {e}")

    def deletar_rascunhos_selecionados(self):
        para_deletar = [eqpto for eqpto, var in self.rascunho_check_vars.items() if var.get()]
        
        if not para_deletar:
            messagebox.showwarning("Nenhuma Seleção", "Nenhum rascunho selecionado para deletar.")
            return

        confirm = messagebox.askyesno(
            "Confirmar Exclusão em Massa",
            f"Você tem certeza que deseja deletar os {len(para_deletar)} rascunhos selecionados?"
        )
        
        if confirm:
            try:
                with sqlite3.connect(caminho_bd_ativo) as conexao:
                    cursor = conexao.cursor()
                    cursor.executemany("DELETE FROM rascunhos WHERE eqpto = ?", [(eqpto,) for eqpto in para_deletar])
                messagebox.showinfo("Sucesso", f"{len(para_deletar)} rascunhos foram deletados.")
                self.reconstruir_lista_rascunhos()
            except sqlite3.Error as e:
                messagebox.showerror("Erro de Banco de Dados", f"Ocorreu um erro ao deletar os rascunhos: {e}")

    def alinhar_coluna_critica(self):
        self.update_idletasks()
        if not self.ref_cells: return
        reference_width = self.ref_cells[0].winfo_width()
        if reference_width > 1:
            if self.frame_tabela_header:
                self.frame_tabela_header.grid_columnconfigure(3, minsize=reference_width)
            for table in self.tabelas_grupo_frames:
                table.grid_columnconfigure(3, minsize=reference_width)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mouse_wheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

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
                comando_sql_cadastros = f"CREATE TABLE IF NOT EXISTS cadastros (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})"
                cursor.execute(comando_sql_cadastros)
                comando_sql_rascunhos = f"CREATE TABLE IF NOT EXISTS rascunhos (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})"
                cursor.execute(comando_sql_rascunhos)

                comando_sql_ajustes = """
                CREATE TABLE IF NOT EXISTS ajustes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    eqpto TEXT NOT NULL UNIQUE,
                    data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
                cursor.execute(comando_sql_ajustes)

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

    def _salvar_dados(self, tabela):
        if not self.campos_dict["Eqpto"].get().strip():
            messagebox.showwarning("Campo Obrigatório", "O campo 'Eqpto' é obrigatório.")
            return False
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
                comando_sql = f"INSERT INTO {tabela} ({sql_nomes_colunas}) VALUES ({placeholders})"
                cursor.execute(comando_sql, tuple(valores))
            return True
        except sqlite3.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao salvar em '{tabela}': {e}")
            return False

    def salvar_rascunho(self):
        if self._salvar_dados('rascunhos'):
            messagebox.showinfo("Sucesso", "Rascunho salvo com sucesso!")
            self.reconstruir_lista_rascunhos()

    def salvar_e_enviar(self):
        eqpto_atual = self.campos_dict["Eqpto"].get().strip()
        if self._salvar_dados('cadastros'):
            messagebox.showinfo("Sucesso", "Ficha salva e enviada com sucesso!")
            
            try:
                with sqlite3.connect(caminho_bd_ativo) as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("INSERT OR IGNORE INTO ajustes (eqpto) VALUES (?)", (eqpto_atual,))
            except sqlite3.Error as e:
                messagebox.showwarning("Aviso", f"Não foi possível adicionar o equipamento à lista de ajustes pendentes: {e}")
            
            try:
                with sqlite3.connect(caminho_bd_ativo) as conexao:
                    cursor = conexao.cursor()
                    cursor.execute("DELETE FROM rascunhos WHERE eqpto = ?", (eqpto_atual,))
            except sqlite3.Error as e:
                messagebox.showwarning("Aviso", f"Não foi possível remover o rascunho antigo: {e}")
            
            self.limpar_formulario()
            self.atualizar_todas_as_listas()

    def atualizar_lista_local(self):
        self.lista_ajustes_completa.clear()
        try:
            if not os.path.exists(caminho_bd_ativo): return
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                cursor.execute("SELECT DISTINCT eqpto FROM cadastros WHERE eqpto != '' ORDER BY data_registro DESC LIMIT 50")
                for eq in cursor.fetchall():
                    self.lista_ajustes_completa.append(eq[0])
            self._filtrar_ajustes_recentes()
        except sqlite3.Error as e:
            print(f"Erro ao ler BD local (cadastros): {e}")

    def reconstruir_lista_rascunhos(self, *args):
        for widget in self.rascunhos_items_frame.winfo_children():
            widget.destroy()
        self.rascunho_check_vars.clear()
        
        self.lista_rascunhos_completa.clear()
        try:
            if not os.path.exists(caminho_bd_ativo): return
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                cursor.execute("SELECT DISTINCT eqpto FROM rascunhos WHERE eqpto != '' ORDER BY data_registro DESC")
                for eq in cursor.fetchall():
                    self.lista_rascunhos_completa.append(eq[0])
        except sqlite3.Error as e: 
            print(f"Erro ao ler BD local (rascunhos): {e}")

        termo_busca = self.busca_rascunhos_var.get().lower()
        rascunhos_filtrados = [r for r in self.lista_rascunhos_completa if termo_busca in r.lower()]

        for eqpto in rascunhos_filtrados:
            var = tk.BooleanVar()
            self.rascunho_check_vars[eqpto] = var
            
            row = tk.Frame(self.rascunhos_items_frame)
            row.pack(fill='x', expand=True, pady=1)
            
            ttk.Checkbutton(row, variable=var).pack(side='left')
            
            lbl = tk.Label(row, text=eqpto, anchor='w')
            lbl.pack(side='left', fill='x', expand=True)
            lbl.bind("<Double-1>", lambda e, eq=eqpto: self.carregar_rascunho_pelo_nome(eq))
            
            tk.Button(row, text="X", fg="red", relief="flat", cursor="hand2", font=("Helvetica", 8, "bold"),
                      command=lambda e=eqpto: self.deletar_rascunho_individual(e)).pack(side='right')

        self.selecionar_tudo_rascunhos_var.set(False)
        self.rascunhos_canvas.yview_moveto(0)

    def atualizar_lista_concluidos(self):
        self.lista_concluidos_completa.clear()
        self._filtrar_concluidos()

    def atualizar_todas_as_listas(self):
        self.atualizar_lista_local()
        self.reconstruir_lista_rascunhos()
        self.atualizar_lista_concluidos()
    
    def carregar_ficha_por_id(self, id_ficha, tabela='cadastros', janela_pai=None):
        try:
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                conexao.row_factory = sqlite3.Row
                cursor = conexao.cursor()
                cursor.execute(f"SELECT * FROM {tabela} WHERE id = ?", (id_ficha,))
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
            if resultado: self.carregar_ficha_por_id(resultado[0], tabela='cadastros')
        except sqlite3.Error as e: messagebox.showerror("Erro de Banco de Dados", f"Erro ao buscar ficha: {e}")

    def carregar_rascunho_pelo_nome(self, eqpto):
        try:
            with sqlite3.connect(caminho_bd_ativo) as conexao:
                cursor = conexao.cursor()
                cursor.execute("SELECT id FROM rascunhos WHERE eqpto = ? ORDER BY data_registro DESC LIMIT 1", (eqpto,))
                resultado = cursor.fetchone()
            if resultado: self.carregar_ficha_por_id(resultado[0], tabela='rascunhos')
        except sqlite3.Error as e: messagebox.showerror("Erro de Banco de Dados", f"Erro ao buscar rascunho: {e}")

    def abrir_janela_busca(self):
        busca_window = tk.Toplevel(self)
        busca_window.title("Buscar Histórico de Equipamento")
        
if __name__ == '__main__':
    class DummyController(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Teste do Módulo Memorial de Cálculo")
            self.geometry("1400x900")
        
        def show_frame(self, page_name):
            print(f"Simulando navegação para: {page_name}")
            self.destroy()

    app = DummyController()
    memorial_frame = MemorialCalculoFrame(app, app)
    memorial_frame.pack(fill="both", expand=True)
    app.mainloop()
