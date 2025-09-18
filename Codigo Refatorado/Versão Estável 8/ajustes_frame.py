import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

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
        
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        # --- Frame de Botões (irá para o fundo da janela) ---
        button_frame = tk.Frame(main_frame)
        button_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        # Os botões são empacotados da direita para a esquerda
        ttk.Button(button_frame, text="Fechar", command=self.destroy).pack(side="right")
        ttk.Button(button_frame, text="Salvar Nova Observação", command=self.salvar_nova_observacao).pack(side="right", padx=5)

        # --- Frame para Nova Observação (irá para o fundo, logo acima dos botões) ---
        new_obs_frame = tk.LabelFrame(main_frame, text="Adicionar Nova Observação", padx=5, pady=5)
        new_obs_frame.pack(side="bottom", fill="x")
        
        self.new_obs_text = tk.Text(new_obs_frame, wrap="word", font=FONTE_PADRAO, height=6)
        self.new_obs_text.pack(fill="x", expand=True)

        # --- Frame para o Histórico (preenche todo o espaço restante no topo) ---
        hist_frame = tk.LabelFrame(main_frame, text="Histórico de Observações", padx=5, pady=5)
        hist_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.hist_text = scrolledtext.ScrolledText(hist_frame, wrap="word", font=FONTE_PEQUENA, state="disabled", relief="flat")
        self.hist_text.pack(fill="both", expand=True)
        
        self.carregar_historico()

    def carregar_historico(self):
        """Carrega e formata o histórico de observações."""
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
        self.hist_text.yview_moveto(1) # Rola para o final

    def salvar_nova_observacao(self):
        """Salva a nova observação e atualiza o histórico."""
        texto = self.new_obs_text.get("1.0", "end-1c").strip()
        if not texto:
            messagebox.showwarning("Campo Vazio", "A nova observação não pode estar vazia.", parent=self)
            return

        self.controller.adicionar_observacao(self.eqpto, self.autor, texto)
        self.new_obs_text.delete("1.0", "end") # Limpa o campo de entrada
        self.carregar_historico() # Recarrega o histórico para mostrar a nova entrada
        
class AjustesFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent_window = parent
        self.linhas_widgets = {}
        self.lista_historico_completa = []
        self.iniciado = False
        self.criar_layout()
        self.carregar_dados_iniciais()

    def criar_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        main_content_frame = tk.Frame(self)
        main_content_frame.grid(row=0, column=0, sticky="nsew", padx=(10,0))
        
        frame_superior = tk.Frame(main_content_frame)
        frame_superior.pack(fill='x', padx=10, pady=10)
        btn_voltar = ttk.Button(frame_superior, text="< Fechar Módulo", command=self.parent_window.destroy)
        btn_voltar.pack(side='left', anchor='nw')
        
        main_container = tk.LabelFrame(main_content_frame, text="AJUSTES PENDENTES", font=("Helvetica", 16, "bold"), padx=10, pady=10)
        main_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        botoes_globais_frame = tk.Frame(main_container)
        botoes_globais_frame.pack(anchor='w', pady=(0, 10))
        self.btn_iniciar = ttk.Button(botoes_globais_frame, text="Iniciar", command=self.iniciar_selecionados)
        self.btn_iniciar.pack(side='left', padx=(0,5))
        btn_atualizar = ttk.Button(botoes_globais_frame, text="Atualizar Lista", command=self.carregar_dados_iniciais)
        btn_atualizar.pack(side='left')

        # --- INÍCIO DA ALTERAÇÃO 1: Barras de Rolagem ---
        canvas_frame = tk.Frame(main_container)
        canvas_frame.pack(fill="both", expand=True)

        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal")
        h_scrollbar.pack(side="bottom", fill="x")
        
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical")
        v_scrollbar.pack(side="right", fill="y")
        
        canvas = tk.Canvas(canvas_frame, highlightthickness=0, yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)

        v_scrollbar.config(command=canvas.yview)
        h_scrollbar.config(command=canvas.xview)
        
        self.items_frame = tk.Frame(canvas)
        self.items_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
        
        self.items_frame.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        # --- FIM DA ALTERAÇÃO 1 ---

        sidebar_frame = tk.LabelFrame(self, text="Histórico de Conclusão", width=SIDEBAR_WIDTH, padx=5, pady=5)
        sidebar_frame.grid(row=0, column=1, sticky="ns", padx=10, pady=10)
        sidebar_frame.pack_propagate(False)

        historico_canvas_frame = tk.Frame(sidebar_frame, relief="sunken", bd=1)
        historico_canvas_frame.pack(fill='both', expand=True, pady=5)
        self.historico_canvas = tk.Canvas(historico_canvas_frame, highlightthickness=0)
        historico_scrollbar = ttk.Scrollbar(historico_canvas_frame, orient="vertical", command=self.historico_canvas.yview)
        self.historico_items_frame = tk.Frame(self.historico_canvas)
        self.historico_canvas.create_window((0, 0), window=self.historico_items_frame, anchor="nw")
        self.historico_canvas.configure(yscrollcommand=historico_scrollbar.set)
        historico_scrollbar.pack(side="right", fill="y")
        self.historico_canvas.pack(side="left", fill="both", expand=True)

    def carregar_dados_iniciais(self):
        self.carregar_equipamentos_pendentes()
        self.carregar_historico()

    def carregar_equipamentos_pendentes(self):
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self.linhas_widgets.clear()
        
        equipamentos = self.controller.carregar_ajustes_pendentes()
        if equipamentos:
            for index, dados_equipamento in enumerate(equipamentos):
                self._criar_linha_equipamento(self.items_frame, dados_equipamento, index)

    def carregar_historico(self):
        for widget in self.historico_items_frame.winfo_children():
            widget.destroy()
        
        self.lista_historico_completa = self.controller.get_historico_ajustes()
        
        if self.lista_historico_completa:
            for item in self.lista_historico_completa:
                eqpto, data_str, status = item['eqpto'], item['data_conclusao'], item['status']
                data_f = datetime.strptime(data_str.split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                
                cor_status = "green" if status == "Aprovado" else "red"
                
                row = tk.Frame(self.historico_items_frame)
                row.pack(fill='x', expand=True, pady=1)

                # --- INÍCIO DA ALTERAÇÃO 3: Largura da coluna Eqpto ---
                lbl_eqpto = tk.Label(row, text=eqpto, width=8, anchor='w', font=FONTE_PEQUENA) # Alterado width para 8
                lbl_eqpto.grid(row=0, column=0, sticky='w')
                
                btn_dir = tk.Button(row, text="📁", font=FONTE_PEQUENA, relief="flat", cursor="hand2")
                btn_dir.grid(row=0, column=1, sticky='w')

                lbl_data = tk.Label(row, text=data_f, width=12, anchor='w', font=FONTE_PEQUENA)
                lbl_data.grid(row=0, column=2, sticky='w', padx=2)

                lbl_status = tk.Label(row, text=status, width=10, anchor='w', font=FONTE_PEQUENA, fg=cor_status)
                lbl_status.grid(row=0, column=3, sticky='w', padx=2)
                # --- FIM DA ALTERAÇÃO 3 ---

        self.historico_canvas.yview_moveto(0)

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
        # O autor é buscado a partir dos dados do equipamento carregado
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
        # --- INÍCIO DA ALTERAÇÃO 2: Alinhamento de Colunas ---
        eqpto = dados['eqpto']
        
        row_frame = tk.Frame(parent, bd=1, relief="solid")
        row_frame.pack(fill="x", expand=True, pady=(0, 2))

        # Configura a última coluna para expandir, empurrando as ações para a direita
        row_frame.grid_columnconfigure(9, weight=1)

        check_var = tk.BooleanVar()
        ttk.Checkbutton(row_frame, variable=check_var).grid(row=0, column=0, sticky='w', padx=5)

        ttk.Separator(row_frame, orient='vertical').grid(row=0, column=1, sticky='ns', padx=2)

        # Definindo os dados e larguras fixas para alinhamento
        col_data = [
            (f"Eqpto: {dados['eqpto']}", 15),
            (f"Autor: {dados['autor']}", 25),
            (f"Data: {dados['data']}", 12),
            (f"Malha: {dados['malha']}", 15),
            (f"Alimentador: {dados['alimentador']}", 15),
            (f"Fabricante: {dados['fabricante']}", 20),
            (f"Comando: {dados['comando']}", 15)
        ]

        # Criando as labels em colunas fixas
        col_idx = 2
        for text, width in col_data:
            tk.Label(row_frame, text=text, font=("Courier", 10), anchor="w", width=width, justify='left').grid(row=0, column=col_idx, sticky='w', padx=5)
            col_idx += 1
        
        ttk.Separator(row_frame, orient='vertical').grid(row=0, column=col_idx, sticky='ns', padx=2)
        col_idx += 1
        
        # Frame de ações alinhado à direita da coluna expansível
        action_frame = tk.Frame(row_frame)
        action_frame.grid(row=0, column=col_idx, sticky='e')
        
        concluir_button = ttk.Button(action_frame, text="Concluir", width=8, command=lambda eq=eqpto: self._concluir_equipamento(eq))
        concluir_button.pack(side="right", padx=(5,0))

        opcoes_status = ["Pendente", "Andamento", "Aprovado", "Reprovado"]
        combo_status = ttk.Combobox(action_frame, values=opcoes_status, state="readonly", width=12, font=FONTE_PEQUENA)
        status_atual = dados.get('status') or "Pendente"
        
        if status_atual not in opcoes_status:
            opcoes_status.insert(0, status_atual)
            combo_status['values'] = opcoes_status
        combo_status.set(status_atual)
        combo_status.pack(side="right", padx=5)

        obs_button = ttk.Button(action_frame, text="Obs", width=4, command=lambda eq=eqpto: self._abrir_janela_obs(eq))
        obs_button.pack(side="right", padx=5)
        
        btn_dir = tk.Button(action_frame, text="📁", font=FONTE_PEQUENA, relief="flat", cursor="hand2")
        btn_dir.pack(side="right")
        
        self.linhas_widgets[eqpto] = {
            "check_var": check_var,
            "combo_status": combo_status,
            "dados": dados
        }
        # --- FIM DA ALTERAÇÃO 2 ---