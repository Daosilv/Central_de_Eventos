import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

# Importa a janela de visualização para ser usada ao clicar no histórico
from visualizacao_frame import DetalhesWindow

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

FONTE_PADRAO = ("Times New Roman", 12)
FONTE_PEQUENA = ("Times New Roman", 10)
SIDEBAR_WIDTH = 400

class ObsWindow(tk.Toplevel):
    def __init__(self, parent, controller, eqpto, autor):
        super().__init__(parent)
        self.controller = controller
        self.eqpto = eqpto
        self.autor = autor if autor and autor.strip() else "Sistema"
        
        self.title(f"Observações para {eqpto}")
        self.geometry("600x550")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        # Centraliza a janela
        self.controller.center_window(self)
        
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        button_frame = tk.Frame(main_frame)
        button_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="Fechar", command=self.destroy).pack(side="right")
        ttk.Button(button_frame, text="Salvar Nova Observação", command=self.salvar_nova_observacao).pack(side="right", padx=5)

        new_obs_frame = tk.LabelFrame(main_frame, text="Adicionar Nova Observação", padx=5, pady=5)
        new_obs_frame.pack(side="bottom", fill="x")
        
        self.new_obs_text = tk.Text(new_obs_frame, wrap="word", font=FONTE_PADRAO, height=6)
        self.new_obs_text.pack(fill="x", expand=True)

        hist_frame = tk.LabelFrame(main_frame, text="Histórico de Observações", padx=5, pady=5)
        hist_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.hist_text = scrolledtext.ScrolledText(hist_frame, wrap="word", font=FONTE_PEQUENA, state="disabled", relief="flat")
        self.hist_text.pack(fill="both", expand=True)
        
        self.carregar_historico()

    def carregar_historico(self):
        self.hist_text.config(state="normal")
        self.hist_text.delete("1.0", "end")
        
        observacoes = self.controller.carregar_observacoes(self.eqpto)
        if not observacoes:
            self.hist_text.insert("1.0", "Nenhuma observação registrada.")
        else:
            for obs in observacoes:
                try:
                    data_f = datetime.strptime(obs['data_obs'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                except (ValueError, TypeError):
                    data_f = "Data Inválida"

                header = f"[{data_f} - {obs.get('autor', 'N/A')}]:\n"
                texto = f"{obs.get('texto', '')}\n" + "-"*80 + "\n"
                
                self.hist_text.insert("end", header, ("bold",))
                self.hist_text.insert("end", texto)

        self.hist_text.config(state="disabled")
        self.hist_text.yview_moveto(1)

    def salvar_nova_observacao(self):
        texto = self.new_obs_text.get("1.0", "end-1c").strip()
        if not texto:
            messagebox.showwarning("Campo Vazio", "A nova observação não pode estar vazia.", parent=self)
            return

        self.controller.adicionar_observacao(self.eqpto, self.autor, texto)
        self.new_obs_text.delete("1.0", "end")
        self.carregar_historico()
        
class AjustesFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent_window = parent
        self.linhas_widgets = {}
        self.logo_photo = None
        
        self.lista_pendentes_completa = []
        self.lista_historico_completa = []
        
        self.busca_pendentes_var = tk.StringVar()
        self.busca_pendentes_var.trace_add("write", self._filtrar_e_recarregar_pendentes)
        self.busca_historico_var = tk.StringVar()
        self.busca_historico_var.trace_add("write", self._filtrar_e_recarregar_historico)
        
        self.header_info = [
            ("Eqpto", 8), ("Autor", 25), ("Data", 12),
            ("Malha", 12), ("Alimentador", 15), ("Fabricante", 14),
            ("Comando", 20), ("Ações", 28)
        ]
        
        self.criar_layout()
        self.carregar_dados_iniciais()

    def criar_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        main_content_frame = tk.Frame(self)
        main_content_frame.grid(row=0, column=0, sticky="nsew", padx=(10,0))
        
        frame_superior = tk.Frame(main_content_frame)
        frame_superior.pack(fill='x', padx=10, pady=10)

        try:
            if Image is None or ImageTk is None:
                raise ImportError("A biblioteca Pillow não está instalada.")
            
            logo_path = r'C:\BD_APP_Cemig\plemt_logo_ao_lado.PNG'
            logo_image = Image.open(logo_path)
            
            original_width, original_height = logo_image.size
            aspect_ratio = original_width / original_height
            new_height = 75
            new_width = int(new_height * aspect_ratio)
            resized_image = logo_image.resize((new_width, new_height))
            
            self.logo_photo = ImageTk.PhotoImage(resized_image)
            
            logo_label = tk.Label(frame_superior, image=self.logo_photo)
            logo_label.pack()
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o logo no módulo de Ajustes. Erro: {e}")
        
        main_container = tk.LabelFrame(main_content_frame, text="AJUSTES PENDENTES", font=("Helvetica", 16, "bold"), padx=10, pady=10)
        main_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(1, weight=1)

        botoes_globais_frame = tk.Frame(main_container)
        botoes_globais_frame.grid(row=0, column=0, sticky='w', pady=(0, 10))
        
        self.btn_iniciar = ttk.Button(botoes_globais_frame, text="Iniciar", command=self.iniciar_selecionados)
        self.btn_iniciar.pack(side='left', padx=(0,5))
        btn_atualizar = ttk.Button(botoes_globais_frame, text="Atualizar Lista", command=self.carregar_dados_iniciais)
        btn_atualizar.pack(side='left')
        
        tk.Label(botoes_globais_frame, text="Buscar Eqpto:").pack(side='left', padx=(15, 5))
        ttk.Entry(botoes_globais_frame, textvariable=self.busca_pendentes_var, width=20).pack(side='left')

        canvas_frame = tk.Frame(main_container)
        canvas_frame.grid(row=1, column=0, sticky='nsew')
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal")
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        canvas = tk.Canvas(canvas_frame, highlightthickness=0, xscrollcommand=h_scrollbar.set)
        canvas.grid(row=0, column=0, sticky='nsew')
        
        h_scrollbar.config(command=canvas.xview)
        
        self.items_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
        self.items_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        sidebar_frame = tk.LabelFrame(self, text="Histórico de Conclusão", width=SIDEBAR_WIDTH, padx=5, pady=5)
        sidebar_frame.grid(row=0, column=1, sticky="ns", padx=10, pady=10)
        sidebar_frame.pack_propagate(False)

        frame_busca_historico = tk.Frame(sidebar_frame)
        frame_busca_historico.pack(fill='x', pady=5)
        tk.Label(frame_busca_historico, text="Buscar Eqpto:").pack(side='left')
        ttk.Entry(frame_busca_historico, textvariable=self.busca_historico_var).pack(fill='x', expand=True, padx=5)

        historico_canvas_frame = tk.Frame(sidebar_frame, relief="sunken", bd=1)
        historico_canvas_frame.pack(fill='both', expand=True, pady=5)
        self.historico_canvas = tk.Canvas(historico_canvas_frame, highlightthickness=0)
        historico_scrollbar = ttk.Scrollbar(historico_canvas_frame, orient="vertical", command=self.historico_canvas.yview)
        self.historico_items_frame = tk.Frame(self.historico_canvas)
        self.historico_canvas.create_window((0, 0), window=self.historico_items_frame, anchor="nw")
        self.historico_canvas.configure(yscrollcommand=historico_scrollbar.set)
        historico_scrollbar.pack(side="right", fill="y")
        self.historico_canvas.pack(side="left", fill="both", expand=True)

    def _configure_grid_columns(self, parent):
        colunas_completas = [("", 4)] + self.header_info
        for i, (text, width) in enumerate(colunas_completas):
            parent.grid_columnconfigure(i * 2 + 1, minsize=width * 8 if width else 30)
    
    def _criar_header(self, parent):
        self._configure_grid_columns(parent)
        colunas_completas = [("", 4)] + self.header_info
        
        for i, (text, width) in enumerate(colunas_completas):
            ttk.Separator(parent, orient='vertical').grid(row=0, column=(i*2), sticky='ns')
            label_opts = {"text": text, "font": ("Courier", 10, "bold"), "anchor": "center"}
            tk.Label(parent, **label_opts).grid(row=0, column=(i*2)+1, sticky='we')
        
        last_col = len(colunas_completas) * 2
        ttk.Separator(parent, orient='vertical').grid(row=0, column=last_col, sticky='ns')
        ttk.Separator(parent, orient='horizontal').grid(row=1, column=0, columnspan=last_col+1, sticky='ew')

    def carregar_dados_iniciais(self):
        self.carregar_equipamentos_pendentes()
        self.carregar_historico()

    def carregar_equipamentos_pendentes(self):
        self.lista_pendentes_completa = self.controller.carregar_ajustes_pendentes() or []
        self._filtrar_e_recarregar_pendentes()

    def _filtrar_e_recarregar_pendentes(self, *args):
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self.linhas_widgets.clear()
        
        self._criar_header(self.items_frame)
        
        termo_busca = self.busca_pendentes_var.get().lower()
        if not termo_busca:
            equipamentos_filtrados = self.lista_pendentes_completa
        else:
            equipamentos_filtrados = [
                dados for dados in self.lista_pendentes_completa 
                if termo_busca in dados.get('eqpto', '').lower()
            ]
        
        if equipamentos_filtrados:
            for index, dados_equipamento in enumerate(equipamentos_filtrados):
                self._criar_linha_equipamento(self.items_frame, dados_equipamento, index)

    def carregar_historico(self):
        self.lista_historico_completa = self.controller.get_historico_ajustes() or []
        self._filtrar_e_recarregar_historico()

    def _abrir_janela_detalhes(self, eqpto):
        id_result = self.controller.get_latest_id_for_equipment(eqpto, 'cadastros')
        if id_result and id_result.get('id'):
            record_id = id_result['id']
            DetalhesWindow(self.parent_window, self.controller, record_id)
        else:
            messagebox.showwarning("Não Encontrado", f"Nenhum registro de memorial de cálculo foi encontrado para o equipamento {eqpto}.", parent=self.parent_window)

    def _filtrar_e_recarregar_historico(self, *args):
        for widget in self.historico_items_frame.winfo_children():
            widget.destroy()
            
        termo_busca = self.busca_historico_var.get().lower()
        if not termo_busca:
            historico_filtrado = self.lista_historico_completa
        else:
            historico_filtrado = [
                item for item in self.lista_historico_completa
                if termo_busca in item.get('eqpto', '').lower()
            ]

        if historico_filtrado:
            style = ttk.Style()
            style.configure("Sidebar.TButton", padding=0)
            for item in historico_filtrado:
                eqpto, data_str, status = item['eqpto'], item['data_conclusao'], item['status']
                data_f = datetime.strptime(data_str.split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                cor_status = "green" if status == "Aprovado" else "red"
                row = tk.Frame(self.historico_items_frame)
                row.pack(fill='x', expand=True, pady=1)

                lbl_eqpto = tk.Label(row, text=eqpto, width=8, anchor='w', font=FONTE_PEQUENA, cursor="hand2") 
                lbl_eqpto.grid(row=0, column=0, sticky='we')
                lbl_eqpto.bind("<Button-1>", lambda e, eq=eqpto: self._abrir_janela_detalhes(eq))
                
                btn_obs = ttk.Button(row, text="Obs", width=4, style="Sidebar.TButton", command=lambda e=eqpto: self._abrir_janela_obs(e))
                btn_obs.grid(row=0, column=1, sticky='', padx=2)

                btn_dir = tk.Button(row, text="📁", font=FONTE_PEQUENA, relief="flat", cursor="hand2")
                btn_dir.grid(row=0, column=2, sticky='')

                lbl_data = tk.Label(row, text=data_f, width=12, anchor='center', font=FONTE_PEQUENA)
                lbl_data.grid(row=0, column=3, sticky='we', padx=2)

                lbl_status = tk.Label(row, text=status, width=10, anchor='center', font=FONTE_PEQUENA, fg=cor_status)
                lbl_status.grid(row=0, column=4, sticky='we', padx=2)

                row.grid_columnconfigure(0, weight=1)

    def iniciar_selecionados(self):
        equipamentos_selecionados = [eqpto for eqpto, widgets in self.linhas_widgets.items() if widgets["check_var"].get()]
        if not equipamentos_selecionados:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione pelo menos um equipamento para iniciar.", parent=self.parent_window)
            return
        self.controller.update_ajuste_status(equipamentos_selecionados, "Andamento")
        for eqpto in equipamentos_selecionados:
            self.linhas_widgets[eqpto]["combo_status"].set("Andamento")
        messagebox.showinfo("Ação Executada", f"{len(equipamentos_selecionados)} equipamento(s) marcado(s) como 'Andamento'.", parent=self.parent_window)

    def _abrir_janela_obs(self, eqpto):
        autor = self.linhas_widgets.get(eqpto, {}).get('dados', {}).get('autor', '')
        ObsWindow(self.parent_window, self.controller, eqpto, autor)

    def _concluir_equipamento(self, eqpto_a_concluir):
        status_selecionado = self.linhas_widgets[eqpto_a_concluir]["combo_status"].get()
        if status_selecionado not in ["Aprovado", "Reprovado"]:
            messagebox.showwarning("Status Inválido", "Para concluir, o status deve ser 'Aprovado' ou 'Reprovado'.", parent=self.parent_window)
            return
        if messagebox.askyesno(title="Confirmar Conclusão", message=f"Você quer concluir o equipamento {eqpto_a_concluir} como '{status_selecionado}'?", parent=self.parent_window):
            self.controller.concluir_ajuste(eqpto_a_concluir, status_selecionado)
            self.carregar_dados_iniciais()

    def _criar_linha_equipamento(self, parent, dados, row_index):
        eqpto = dados['eqpto']
        
        grid_row = (row_index * 2) + 2
        
        colunas_completas = [("", 4)] + self.header_info
        total_grid_cols = len(colunas_completas) * 2
        
        ttk.Separator(parent, orient='vertical').grid(row=grid_row, column=0, sticky='ns')
        
        check_var = tk.BooleanVar()
        ttk.Checkbutton(parent, variable=check_var).grid(row=grid_row, column=1, sticky='w', padx=5)

        data_str = dados.get('data_registro', '')
        data_formatada = ""
        if data_str:
            try:
                data_formatada = datetime.strptime(data_str.split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            except (ValueError, TypeError):
                data_formatada = "Data Inválida"

        data_values = [
            dados.get('eqpto', ''), dados.get('autor', ''), data_formatada,
            dados.get('malha', ''), dados.get('alimentador', ''), dados.get('fabricante', ''),
            dados.get('comando', '')
        ]

        for i, data_text in enumerate(data_values):
            col_idx = (i + 1) * 2
            ttk.Separator(parent, orient='vertical').grid(row=grid_row, column=col_idx, sticky='ns')
            label_opts = {"text": data_text, "font": ("Courier", 10), "anchor": "center", "justify": 'center'}
            tk.Label(parent, **label_opts).grid(row=grid_row, column=col_idx + 1, sticky='ew', padx=5)

        actions_col_idx = (len(data_values) + 1) * 2
        ttk.Separator(parent, orient='vertical').grid(row=grid_row, column=actions_col_idx, sticky='ns')
        action_frame = tk.Frame(parent)
        action_frame.grid(row=grid_row, column=actions_col_idx + 1, sticky='ew')
        
        btn_dir = tk.Button(action_frame, text="📁", font=FONTE_PEQUENA, relief="flat", cursor="hand2")
        btn_dir.pack(side="left", expand=True)
        obs_button = ttk.Button(action_frame, text="Obs", width=4, command=lambda eq=eqpto: self._abrir_janela_obs(eq))
        obs_button.pack(side="left", expand=True)
        opcoes_status = ["Pendente", "Andamento", "Aprovado", "Reprovado"]
        combo_status = ttk.Combobox(action_frame, values=opcoes_status, state="readonly", width=12, font=FONTE_PEQUENA)
        status_atual = dados.get('status') or "Pendente"
        if status_atual not in opcoes_status:
            opcoes_status.insert(0, status_atual)
            combo_status['values'] = opcoes_status
        combo_status.set(status_atual)
        combo_status.pack(side="left", padx=5, expand=True)
        concluir_button = ttk.Button(action_frame, text="Concluir", width=8, command=lambda eq=eqpto: self._concluir_equipamento(eq))
        concluir_button.pack(side="left", padx=(5,0), expand=True)
        
        self.linhas_widgets[eqpto] = {"check_var": check_var, "combo_status": combo_status, "dados": dados}
        
        ttk.Separator(parent, orient='vertical').grid(row=grid_row, column=total_grid_cols, sticky='ns')
        ttk.Separator(parent, orient='horizontal').grid(row=grid_row + 1, column=0, columnspan=total_grid_cols + 1, sticky='ew')
