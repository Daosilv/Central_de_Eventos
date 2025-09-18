import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import sys

FONTE_PADRAO = ("Times New Roman", 12)

class DetalhesWindow(tk.Toplevel):
    # ... (código da classe inalterado) ...
    def __init__(self, parent, controller, id_ficha):
        super().__init__(parent); self.controller = controller; self.id_ficha = id_ficha; self.dados_ficha = self.controller.get_record_by_id(self.id_ficha)
        if not self.dados_ficha: messagebox.showerror("Erro", f"Ficha ID: {self.id_ficha} não encontrada.", parent=self); self.destroy(); return
        self.title("Visualização de Parâmetros"); self.geometry("1200x900"); self.grab_set(); self.resizable(True, True); self.col_widths = [90, 70, 85, 120, 120, 70, 85, 120, 120]
        main_frame = tk.Frame(self); main_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(main_frame, highlightthickness=0); scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview); self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))); self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw"); self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<Enter>", self._bind_mouse_wheel); self.canvas.bind("<Leave>", self._unbind_mouse_wheel); self.scrollable_frame.bind("<Enter>", self._bind_mouse_wheel); self.scrollable_frame.bind("<Leave>", self._unbind_mouse_wheel)
        self.canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y"); self.criar_layout_visualizacao()
    def _on_mouse_wheel(self, event):
        if sys.platform == "win32": self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else: self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")
    def _bind_mouse_wheel(self, event): self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
    def _unbind_mouse_wheel(self, event): self.canvas.unbind_all("<MouseWheel>")
    def _bordered_label(self, parent, text, width=None, anchor="w", **kwargs):
        label = tk.Label(parent, text=text or " ", font=FONTE_PADRAO, anchor=anchor, justify="left", relief="solid", bd=1, **kwargs)
        if width: label.config(width=width)
        return label
    def _cell(self, frame, r, c, txt="", rs=1, cs=1, sticky="nsew"):
        outer = tk.Frame(frame, relief="solid", bd=1); outer.grid(row=r, column=c, rowspan=rs, columnspan=cs, sticky=sticky); outer.pack_propagate(False)
        lbl = tk.Label(outer, text=txt if txt is not None else "", font=FONTE_PADRAO, wraplength=110); lbl.pack(fill="both", expand=True, padx=2, pady=2)
        return outer
    def criar_layout_visualizacao(self):
        main_form_frame = tk.Frame(self.scrollable_frame); main_form_frame.pack(pady=10, padx=10); frame_campos = tk.Frame(main_form_frame); frame_campos.pack(pady=10, padx=10, fill="x"); wrap_tabelas = tk.Frame(main_form_frame); wrap_tabelas.pack(pady=10, anchor="center"); d = self.dados_ficha
        row1 = tk.Frame(frame_campos); row1.pack(fill="x", pady=1); tk.Label(row1, text="Autor", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row1, d.get("autor"), width=40).pack(side="left", padx=(0,5)); tk.Label(row1, text="Data", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row1, d.get("data"), width=11).pack(side="left", padx=(0,5)); tk.Label(row1, text="NS", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row1, d.get("ns")).pack(side="left", padx=(0,5))
        row2 = tk.Frame(frame_campos); row2.pack(fill="x", pady=1); tk.Label(row2, text="Eqpto", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row2, d.get("eqpto"), width=10).pack(side="left", padx=(0,5)); tk.Label(row2, text="Condição", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row2, d.get("condição"), width=16).pack(side="left", padx=(0,5)); tk.Label(row2, text="Coord", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row2, d.get("coord")).pack(side="left", padx=(0,5)); tk.Label(row2, text="Malha", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row2, d.get("malha"), width=16).pack(side="left", padx=(0,5)); tk.Label(row2, text="Alimentador", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row2, d.get("alimentador"), width=10).pack(side="left", padx=(0,5))
        row3 = tk.Frame(frame_campos); row3.pack(fill="x", pady=1); tk.Label(row3, text="Motivador", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row3, d.get("motivador"), width=14).pack(side="left", padx=(0,5)); tk.Label(row3, text="Endereço", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row3, d.get("endereço")).pack(side="left", padx=(0,5), fill="x", expand=True); tk.Label(row3, text="Mídia", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row3, d.get("mídia"), width=14).pack(side="left", padx=(0,5))
        row4 = tk.Frame(frame_campos); row4.pack(fill="x", pady=1); tk.Label(row4, text="Fabricante", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row4, d.get("fabricante"), width=28).pack(side="left", padx=(0,5)); tk.Label(row4, text="Modelo", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row4, d.get("modelo")).pack(side="left", padx=(0,5)); tk.Label(row4, text="Comando", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row4, d.get("comando")).pack(side="left", padx=(0,5)); tk.Label(row4, text="Telecontrolado", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row4, d.get("telecontrolado"), width=8).pack(side="left", padx=(0,5)); tk.Label(row4, text="Siom", relief="solid", bd=1, anchor="e", font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row4, d.get("siom"), width=10).pack(side="left", padx=(0,5))
        row_bypass = tk.Frame(frame_campos); row_bypass.pack(fill="x", pady=1); tk.Label(row_bypass, text="Bypass", relief="solid", bd=1, font=FONTE_PADRAO).pack(side="left"); self._bordered_label(row_bypass, d.get('bypass_1'), width=8).pack(side="left", padx=(0,2)); tk.Label(row_bypass, text="-", bd=0, font=FONTE_PADRAO).pack(side="left", padx=2); self._bordered_label(row_bypass, d.get('bypass_2'), width=10).pack(side="left")
        header = tk.Frame(wrap_tabelas, bd=1, relief="solid"); [header.grid_columnconfigure(c, minsize=w) for c, w in enumerate(self.col_widths)]; [header.grid_rowconfigure(r, minsize=30, weight=1) for r in range(3)]; self._cell(header, 0, 0, "Grupo Normal = Grupo de Consumo", cs=9); self._cell(header, 1, 0, "  Grupos  ", rs=2); self._cell(header, 1, 1, "FASE", cs=4); self._cell(header, 1, 5, "TERRA", cs=4); self._cell(header, 2, 1, "  Pickup  "); self._cell(header, 2, 2, "  Sequência  "); self._cell(header, 2, 3, "  Curva Lenta  "); self._cell(header, 2, 4, "  Curva Rápida  "); self._cell(header, 2, 5, "  Pickup  "); self._cell(header, 2, 6, "  Sequência  "); self._cell(header, 2, 7, "  Curva Lenta  "); self._cell(header, 2, 8, "  Curva Rápida  "); header.pack(pady=5)
        for i in range(1, 4): self._criar_tabela_grupo_visualizacao(wrap_tabelas, f"  Grupo {i}  ", i)
        if d.get("condição") in ["Acess Inv", "Acess s/Inv"]:
            header_rep = tk.Frame(wrap_tabelas, bd=1, relief="solid"); [header_rep.grid_columnconfigure(c, minsize=w) for c, w in enumerate(self.col_widths)]; [header_rep.grid_rowconfigure(r, minsize=30, weight=1) for r in range(3)]; self._cell(header_rep, 0, 0, "Grupo Invertido = Grupo de Injeção", cs=9); self._cell(header_rep, 1, 0, "  Grupos  ", rs=2); self._cell(header_rep, 1, 1, "FASE", cs=4); self._cell(header_rep, 1, 5, "TERRA", cs=4); self._cell(header_rep, 2, 1, "  Pickup  "); self._cell(header_rep, 2, 2, "  Sequência  "); self._cell(header_rep, 2, 3, "  Curva Lenta  "); self._cell(header_rep, 2, 4, "  Curva Rápida  "); self._cell(header_rep, 2, 5, "  Pickup  "); self._cell(header_rep, 2, 6, "  Sequência  "); self._cell(header_rep, 2, 7, "  Curva Lenta  "); self._cell(header_rep, 2, 8, "  Curva Rápida  "); header_rep.pack(pady=(20, 5))
            for i in range(1, 4): self._criar_tabela_grupo_visualizacao(wrap_tabelas, f"  Grupo {i}  ", i, suffix="_rep")
        frame_obs = tk.Frame(main_form_frame); frame_obs.pack(pady=(10, 5), padx=10, fill='x', expand=False); tk.Label(frame_obs, text="Observações:", font=FONTE_PADRAO).pack(anchor='w'); text_container = tk.Frame(frame_obs, height=120, relief="solid", bd=1); text_container.pack(fill='x', expand=False); text_container.pack_propagate(False); obs_text = tk.Text(text_container, relief="flat", bd=0, font=FONTE_PADRAO, wrap="word"); obs_text.insert("1.0", d.get("observacoes") or "Nenhuma observação."); obs_text.config(state="disabled"); obs_text.pack(fill="both", expand=True)
        ttk.Button(main_form_frame, text="Fechar", command=self.destroy).pack(pady=20)
    def _criar_tabela_grupo_visualizacao(self, parent, group_name, group_index, suffix=""):
        frame_tabela = tk.Frame(parent, bd=1, relief="solid"); [frame_tabela.grid_columnconfigure(c, minsize=w) for c, w in enumerate(self.col_widths)]; [frame_tabela.grid_rowconfigure(r, minsize=30, weight=1) for r in range(3)]; d = self.dados_ficha
        self._cell(frame_tabela, 0, 0, group_name, rs=3); self._cell(frame_tabela, 0, 1, d.get(f'g{group_index}_pickup_fase{suffix}'), rs=3); self._cell(frame_tabela, 0, 2, d.get(f'g{group_index}_sequencia{suffix}'), rs=3); self._cell(frame_tabela, 0, 3, d.get(f'g{group_index}_curva_lenta_tipo{suffix}'))
        sub_lenta = tk.Frame(frame_tabela, bd=0); sub_lenta.grid(row=1, column=3, rowspan=2, sticky="nsew"); sub_lenta.grid_rowconfigure(0, weight=1); sub_lenta.grid_rowconfigure(1, weight=1); sub_lenta.grid_columnconfigure(0, weight=1); sub_lenta.grid_columnconfigure(1, weight=1); tk.Label(sub_lenta, text="Dial", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=0, column=0, sticky="nsew"); tk.Label(sub_lenta, text="T. Adic.", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=0, column=1, sticky="nsew"); tk.Label(sub_lenta, text=d.get(f'g{group_index}_curva_lenta_dial{suffix}'), font=FONTE_PADRAO, relief="solid", bd=1).grid(row=1, column=0, sticky="nsew"); tk.Label(sub_lenta, text=d.get(f'g{group_index}_curva_lenta_tadic{suffix}'), font=FONTE_PADRAO, relief="solid", bd=1).grid(row=1, column=1, sticky="nsew")
        self._cell(frame_tabela, 0, 4, "IEC Inversa"); sub_rapida = tk.Frame(frame_tabela, bd=0); sub_rapida.grid(row=1, column=4, rowspan=2, sticky="nsew"); sub_rapida.grid_rowconfigure(0, weight=1); sub_rapida.grid_rowconfigure(1, weight=1); sub_rapida.grid_columnconfigure(0, weight=1); sub_rapida.grid_columnconfigure(1, weight=1); tk.Label(sub_rapida, text="Dial", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=0, column=0, sticky="nsew"); tk.Label(sub_rapida, text="T. Adic.", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=0, column=1, sticky="nsew"); tk.Label(sub_rapida, text=d.get(f'g{group_index}_curva_rapida_dial{suffix}'), font=FONTE_PADRAO, relief="solid", bd=1).grid(row=1, column=0, sticky="nsew"); tk.Label(sub_rapida, text=d.get(f'g{group_index}_curva_rapida_tadic{suffix}'), font=FONTE_PADRAO, relief="solid", bd=1).grid(row=1, column=1, sticky="nsew")
        self._cell(frame_tabela, 0, 5, d.get(f'g{group_index}_pickup_terra{suffix}'), rs=3); self._cell(frame_tabela, 0, 6, d.get(f'g{group_index}_sequencia_terra{suffix}'), rs=3)
        self._cell(frame_tabela, 0, 7, "T. Definido"); self._cell(frame_tabela, 1, 7, "Tempo (s)"); self._cell(frame_tabela, 2, 7, d.get(f'g{group_index}_terra_tempo_lenta{suffix}'))
        self._cell(frame_tabela, 0, 8, "T. Definido"); self._cell(frame_tabela, 1, 8, "Tempo (s)"); self._cell(frame_tabela, 2, 8, d.get(f'g{group_index}_terra_tempo_rapida{suffix}'))
        frame_tabela.pack(pady=(0, 5))

class VisualizacaoFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.filtro_eqpto = tk.StringVar(); self.filtro_malha = tk.StringVar(); self.filtro_alimentador = tk.StringVar(); self.filtro_condicao = tk.StringVar()
        self.id_map = {}
        self.criar_widgets()

    def _get_opcoes_formatadas(self, categoria):
        opcoes_raw = self.controller.get_opcoes_por_categoria_geral(categoria) # <-- MUDANÇA AQUI
        return [item['valor'] for item in opcoes_raw] if opcoes_raw else []

    def criar_widgets(self):
        # ... (código do método inalterado) ...
        btn_voltar = ttk.Button(self, text="< Fechar Módulo", command=self.master.destroy); btn_voltar.pack(anchor='nw', padx=10, pady=10); frame_filtros = tk.LabelFrame(self, text="Filtros de Busca", padx=15, pady=15, font=FONTE_PADRAO); frame_filtros.pack(padx=10, pady=10, fill="x")
        tk.Label(frame_filtros, text="Equipamento:", font=FONTE_PADRAO).grid(row=0, column=0, padx=5, pady=5, sticky="w"); ttk.Entry(frame_filtros, textvariable=self.filtro_eqpto, width=30, font=FONTE_PADRAO).grid(row=0, column=1, padx=5, pady=5)
        opcoes_malha = self._get_opcoes_formatadas('malha'); tk.Label(frame_filtros, text="Malha:", font=FONTE_PADRAO).grid(row=0, column=2, padx=5, pady=5, sticky="w"); ttk.Combobox(frame_filtros, textvariable=self.filtro_malha, values=[""] + opcoes_malha, state="readonly", font=FONTE_PADRAO, width=28).grid(row=0, column=3, padx=5, pady=5)
        tk.Label(frame_filtros, text="Alimentador:", font=FONTE_PADRAO).grid(row=1, column=0, padx=5, pady=5, sticky="w"); opcoes_alimentador = self._get_opcoes_formatadas('alimentador'); ttk.Combobox(frame_filtros, textvariable=self.filtro_alimentador, values=[""] + opcoes_alimentador, width=28, font=FONTE_PADRAO).grid(row=1, column=1, padx=5, pady=5)
        opcoes_condicao = self._get_opcoes_formatadas('condicao'); tk.Label(frame_filtros, text="Condição:", font=FONTE_PADRAO).grid(row=1, column=2, padx=5, pady=5, sticky="w"); ttk.Combobox(frame_filtros, textvariable=self.filtro_condicao, values=[""] + opcoes_condicao, state="readonly", font=FONTE_PADRAO, width=28).grid(row=1, column=3, padx=5, pady=5)
        frame_botoes = tk.Frame(frame_filtros); frame_botoes.grid(row=1, column=4, padx=20, pady=5, sticky="e"); ttk.Button(frame_botoes, text="Buscar", command=self.executar_busca).pack(side="left", padx=5); ttk.Button(frame_botoes, text="Limpar Filtros", command=self.limpar_filtros).pack(side="left", padx=5); frame_filtros.grid_columnconfigure(4, weight=1)
        frame_resultados = tk.LabelFrame(self, text="Resultados da Busca (Equipamentos)", padx=10, pady=10, font=FONTE_PADRAO); frame_resultados.pack(padx=10, pady=10, fill="both", expand=True); scrollbar = ttk.Scrollbar(frame_resultados); scrollbar.pack(side="right", fill="y"); self.listbox_resultados = tk.Listbox(frame_resultados, yscrollcommand=scrollbar.set, font=FONTE_PADRAO); self.listbox_resultados.pack(fill="both", expand=True); self.listbox_resultados.bind("<Double-1>", self.mostrar_detalhes_selecionado); scrollbar.config(command=self.listbox_resultados.yview)

    def executar_busca(self):
        # ... (código do método inalterado) ...
        self.listbox_resultados.delete(0, tk.END); self.id_map.clear(); filtros = { "eqpto": self.filtro_eqpto.get().strip(), "malha": self.filtro_malha.get().strip(), "alimentador": self.filtro_alimentador.get().strip(), "condição": self.filtro_condicao.get().strip() }
        if not any(filtros.values()): messagebox.showwarning("Busca Inválida", "Preencha pelo menos um campo."); return
        resultados = self.controller.buscar_registros(filtros)
        if resultados is None: return
        if not resultados: self.listbox_resultados.insert(tk.END, "Nenhum equipamento encontrado.")
        else:
            self.listbox_resultados.insert(tk.END, f"  {len(resultados)} equipamento(s) encontrado(s). Duplo-clique para ver detalhes."); self.listbox_resultados.insert(tk.END, "")
            for row in resultados:
                data_f = datetime.strptime(row['data_registro'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                display = f"Eqpto: {row['eqpto']} | Malha: {row['malha']} | Alimentador: {row['alimentador']} | Data: {data_f}"
                idx = self.listbox_resultados.size(); self.listbox_resultados.insert(tk.END, display); self.id_map[idx] = row['id']

    def limpar_filtros(self):
        # ... (código do método inalterado) ...
        self.filtro_eqpto.set(""); self.filtro_malha.set(""); self.filtro_alimentador.set(""); self.filtro_condicao.set(""); self.listbox_resultados.delete(0, tk.END); self.id_map.clear()
    def mostrar_detalhes_selecionado(self, event=None):
        # ... (código do método inalterado) ...
        sel = self.listbox_resultados.curselection()
        if not sel: return
        id_ficha = self.id_map.get(sel[0])
        if id_ficha is not None: DetalhesWindow(self, self.controller, id_ficha)
