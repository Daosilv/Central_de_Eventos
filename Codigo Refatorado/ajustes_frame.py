import tkinter as tk
from tkinter import ttk, messagebox
import os

FONTE_PADRAO = ("Times New Roman", 12)

class ObsWindow(tk.Toplevel):
    def __init__(self, parent, controller, eqpto):
        super().__init__(parent)
        self.controller = controller
        self.eqpto = eqpto
        self.title(f"Observação para {eqpto}")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        tk.Label(main_frame, text="Insira a observação:", font=FONTE_PADRAO).pack(anchor="w")
        text_frame = tk.Frame(main_frame, bd=1, relief="solid")
        self.text_obs = tk.Text(text_frame, wrap="word", font=FONTE_PADRAO, height=15)
        self.text_obs.pack(fill="both", expand=True)
        text_frame.pack(fill="both", expand=True, pady=5)
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(5,0))
        ttk.Button(button_frame, text="Salvar", command=self.salvar_e_fechar).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.destroy).pack(side="right")
        self.carregar_obs_existente()
        
    def carregar_obs_existente(self):
        texto_obs = self.controller.carregar_observacao(self.eqpto)
        if texto_obs:
            self.text_obs.insert("1.0", texto_obs)

    def salvar_e_fechar(self):
        texto = self.text_obs.get("1.0", "end-1c")
        self.controller.salvar_observacao(self.eqpto, texto)
        messagebox.showinfo("Sucesso", "Observação salva com sucesso.", parent=self)
        self.destroy()

class AjustesFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent_window = parent
        self.linhas_widgets = {}
        self.iniciado = False
        self.criar_layout()
        self.carregar_equipamentos_pendentes()

    def criar_layout(self):
        frame_superior = tk.Frame(self)
        frame_superior.pack(fill='x', padx=10, pady=10)
        btn_voltar = ttk.Button(frame_superior, text="< Fechar Módulo", command=self.parent_window.destroy)
        btn_voltar.pack(side='left', anchor='nw')
        botoes_globais_frame = tk.Frame(frame_superior)
        botoes_globais_frame.pack(side='right', anchor='ne')
        btn_atualizar = ttk.Button(botoes_globais_frame, text="Atualizar Lista", command=self.carregar_equipamentos_pendentes)
        btn_atualizar.pack(side='left', padx=5)
        main_container = tk.LabelFrame(self, text="AJUSTES PENDENTES", font=("Helvetica", 16, "bold"), padx=10, pady=10)
        main_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self.btn_iniciar = ttk.Button(main_container, text="Iniciar", command=self.toggle_iniciar_parar)
        self.btn_iniciar.pack(anchor='w', pady=(0, 10))
        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        self.items_frame = tk.Frame(canvas)
        self.items_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.items_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.items_frame.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def carregar_equipamentos_pendentes(self):
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self.linhas_widgets.clear()
        
        equipamentos = self.controller.carregar_ajustes_pendentes()
        if equipamentos is None: return

        for index, dados_equipamento in enumerate(equipamentos):
            self._criar_linha_equipamento(self.items_frame, dados_equipamento, index)

    def toggle_iniciar_parar(self):
        equipamentos_selecionados = [eqpto for eqpto, widgets in self.linhas_widgets.items() if widgets["check_var"].get()]
        if not equipamentos_selecionados:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione pelo menos um equipamento.")
            return
        if not self.iniciado:
            msg = "Os seguintes equipamentos foram 'Iniciados':\n\n- " + "\n- ".join(equipamentos_selecionados)
            messagebox.showinfo("Ação Executada", msg)
            self.btn_iniciar.config(text="Parar")
            self.iniciado = True
        else:
            msg = "Os seguintes equipamentos foram 'Parados':\n\n- " + "\n- ".join(equipamentos_selecionados)
            messagebox.showinfo("Ação Executada", msg)
            self.btn_iniciar.config(text="Iniciar")
            self.iniciado = False

    def _abrir_janela_obs(self, eqpto):
        ObsWindow(self, self.controller, eqpto)

    def _concluir_equipamento(self, eqpto_a_concluir):
        if messagebox.askyesno(title="Confirmar Conclusão", message=f"Você quer concluir o equipamento {eqpto_a_concluir}?"):
            self.controller.concluir_ajuste(eqpto_a_concluir)
            self.carregar_equipamentos_pendentes()

    def _criar_linha_equipamento(self, parent, dados, row_index):
        eqpto, autor, data, malha, alimentador, fabricante, comando = dados['eqpto'], dados['autor'], dados['data'], dados['malha'], dados['alimentador'], dados['fabricante'], dados['comando']
        row_frame = tk.Frame(parent, bd=1, relief="solid")
        row_frame.grid(row=row_index, column=0, sticky="nsew", pady=(0, 2))
        for i in range(24): row_frame.columnconfigure(i, weight=0)
        row_frame.columnconfigure(2, weight=3); row_frame.columnconfigure(4, weight=5); row_frame.columnconfigure(6, weight=3); row_frame.columnconfigure(8, weight=3); row_frame.columnconfigure(10, weight=4); row_frame.columnconfigure(12, weight=4); row_frame.columnconfigure(14, weight=3); row_frame.columnconfigure(16, weight=1)
        check_var = tk.BooleanVar()
        ttk.Checkbutton(row_frame, variable=check_var).grid(row=0, column=0, padx=5, sticky="w")
        ttk.Separator(row_frame, orient='vertical').grid(row=0, column=1, sticky='ns')
        labels_data = [eqpto, autor, data, malha, alimentador, fabricante, comando]
        col_widths = [18, 30, 15, 18, 18, 20, 15]
        grid_col = 2
        for i, item in enumerate(labels_data):
            tk.Label(row_frame, text=item, font=("Courier", 10), anchor="w", width=col_widths[i]).grid(row=0, column=grid_col, padx=5, sticky="w")
            grid_col += 1
            ttk.Separator(row_frame, orient='vertical').grid(row=0, column=grid_col, sticky='ns')
            grid_col += 1
        folder_button = tk.Button(row_frame, text="📁", relief="flat", cursor="hand2"); folder_button.grid(row=0, column=17, padx=2)
        ttk.Separator(row_frame, orient='vertical').grid(row=0, column=18, sticky='ns')
        play_button = tk.Button(row_frame, text="▶️", relief="flat", cursor="hand2"); play_button.grid(row=0, column=19, padx=2)
        ttk.Separator(row_frame, orient='vertical').grid(row=0, column=20, sticky='ns')
        obs_button = tk.Button(row_frame, text="Obs", font=("Arial", 8), width=4, command=lambda eq=eqpto: self._abrir_janela_obs(eq)); obs_button.grid(row=0, column=21, padx=2)
        ttk.Separator(row_frame, orient='vertical').grid(row=0, column=22, sticky='ns')
        concluir_button = tk.Button(row_frame, text="Concluir", font=("Arial", 9), command=lambda eq=eqpto: self._concluir_equipamento(eq)); concluir_button.grid(row=0, column=23, padx=(2, 5))
        self.linhas_widgets[eqpto] = { "check_var": check_var }

if __name__ == '__main__':
    pass
