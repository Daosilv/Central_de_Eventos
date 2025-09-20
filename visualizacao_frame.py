import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os
import sys
from collections import defaultdict

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

FONTE_PADRAO = ("Times New Roman", 12)
FONTE_PEQUENA = ("Times New Roman", 10) 

class DetalhesWindow(tk.Toplevel):
    def __init__(self, parent, controller, id_ficha):
        super().__init__(parent)
        self.controller = controller
        self.id_ficha = id_ficha
        self.dados_ficha = self.controller.get_record_by_id(self.id_ficha)
        
        if not self.dados_ficha:
            messagebox.showerror("Erro", f"Ficha ID: {self.id_ficha} não encontrada.", parent=self)
            self.destroy()
            return

        self.title("Visualização de Parâmetros")
        self.geometry("1200x900")
        self.grab_set()
        self.resizable(True, True)
        
        self.controller.center_window(self)

        self.col_widths = [90, 70, 85, 120, 120, 70, 85, 120, 120]
        main_frame = tk.Frame(self)
        main_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<Enter>", self._bind_mouse_wheel)
        self.canvas.bind("<Leave>", self._unbind_mouse_wheel)
        self.scrollable_frame.bind("<Enter>", self._bind_mouse_wheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_mouse_wheel)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.criar_layout_visualizacao()

    def _on_mouse_wheel(self, event):
        if sys.platform == "win32":
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else:
            self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

    def _bind_mouse_wheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)

    def _unbind_mouse_wheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _bordered_label(self, parent, text, width=None, anchor="w", **kwargs):
        label = tk.Label(parent, text=text or " ", font=FONTE_PADRAO, anchor=anchor, justify="left", relief="solid", bd=1, **kwargs)
        if width:
            label.config(width=width)
        return label

    def _cell(self, frame, r, c, txt="", rs=1, cs=1, sticky="nsew"):
        outer = tk.Frame(frame, relief="solid", bd=1)
        outer.grid(row=r, column=c, rowspan=rs, columnspan=cs, sticky=sticky)
        outer.pack_propagate(False)
        # --- CORREÇÃO APLICADA: removido wraplength=110 ---
        lbl = tk.Label(outer, text=txt if txt is not None else "", font=FONTE_PADRAO)
        lbl.pack(fill="both", expand=True, padx=2, pady=2)
        return outer

    def criar_layout_visualizacao(self):
        d = self.dados_ficha
        main_container = tk.Frame(self.scrollable_frame, padx=10, pady=10)
        main_container.pack(fill="both", expand=True)

        # --- CABEÇALHO ---
        header_frame = tk.Frame(main_container)
        header_frame.pack(fill='x', pady=(0, 15), anchor='w')

        def create_header_cell(parent, label_text, value_text, label_width, value_width, expand=False):
            cell_frame = tk.Frame(parent)
            pack_options = {'side': 'left', 'padx': (0, 5)}
            if expand:
                pack_options.update({'fill': 'x', 'expand': True})
            
            cell_frame.pack(**pack_options)
            
            tk.Label(cell_frame, text=label_text, relief="solid", bd=1, anchor="w", font=FONTE_PADRAO, width=label_width).pack(side="left", fill='y')
            self._bordered_label(cell_frame, value_text, width=value_width, anchor='w').pack(side="left", fill='both', expand=True)

        row1 = tk.Frame(header_frame); row1.pack(fill="x", pady=1, anchor='w')
        create_header_cell(row1, "Autor:", d.get("autor"), 4, 61)
        create_header_cell(row1, "Data:", d.get("data"), 4, 12)
        create_header_cell(row1, "NS:", d.get("ns"), 3, 20)
        create_header_cell(row1, "Eqpto:", d.get("eqpto"), 5, 10)
        create_header_cell(row1, "Condição:", d.get("condição"), 8, 10)

        row2 = tk.Frame(header_frame); row2.pack(fill="x", pady=1, anchor='w')
        create_header_cell(row2, "Malha:", d.get("malha"), 6, 10)
        create_header_cell(row2, "Alimentador:", d.get("alimentador"), 10, 17)
        create_header_cell(row2, "Motivador:", d.get("motivador"), 8, 8)
        create_header_cell(row2, "Coord:", d.get("coord"), 5, 20)
        create_header_cell(row2, "Endereço:", d.get("endereço"), 8, 45, expand=True)

        row3 = tk.Frame(header_frame); row3.pack(fill="x", pady=1, anchor='w')
        create_header_cell(row3, "Mídia:", d.get("mídia"), 6, 10)
        create_header_cell(row3, "Fabricante:", d.get("fabricante"), 10, 20)
        create_header_cell(row3, "Modelo:", d.get("modelo"), 6, 20)
        create_header_cell(row3, "Comando:", d.get("comando"), 8, 15)
        create_header_cell(row3, "Telecontrolado:", d.get("telecontrolado"), 12, 5)
        create_header_cell(row3, "Siom:", d.get("siom"), 4, 21, expand=True)

        row4 = tk.Frame(header_frame); row4.pack(fill="x", pady=1, anchor='w')
        create_header_cell(row4, "By-Pass:", d.get("bypass"), 6, 10)
        create_header_cell(row4, "Manobra Efetiva:", d.get("manobra_efetiva"), 14, 5)
        create_header_cell(row4, "Vinculado a Acessante:", d.get("vinculado_acessante"), 19, 5)
        if d.get('vinculado_acessante') == 'Sim':
            create_header_cell(row4, "Eqpto Acessante:", d.get('eqpto_acessante'), 14, 10, expand=True)

        params_container = tk.Frame(main_container)
        params_container.pack(fill='x', pady=10, anchor='w')
        params_container.grid_columnconfigure(0, weight=1)
        params_container.grid_columnconfigure(1, weight=1)
        params_container.grid_columnconfigure(2, weight=1)
        
        col_esquerda = tk.Frame(params_container); col_esquerda.grid(row=0, column=0, sticky='new', padx=(0,10))
        col_meio = tk.Frame(params_container); col_meio.grid(row=0, column=1, sticky='new', padx=(0,10))
        col_direita = tk.Frame(params_container); col_direita.grid(row=0, column=2, sticky='new')
        
        f_coord = tk.Frame(col_esquerda); f_coord.pack(anchor='w')
        self._cell(f_coord, 0, 0, "Parâmetros do Coordenograma do Cliente", cs=3)
        self._cell(f_coord, 1, 0, ""); self._cell(f_coord, 1, 1, "Consumo"); self._cell(f_coord, 1, 2, "Injeção")
        self._cell(f_coord, 2, 0, "Pick-up (A)"); self._cell(f_coord, 2, 1, d.get("param_consumo_pickup")); self._cell(f_coord, 2, 2, d.get("param_injecao_pickup"))
        self._cell(f_coord, 3, 0, "Curva"); self._cell(f_coord, 3, 1, d.get("param_consumo_curva")); self._cell(f_coord, 3, 2, d.get("param_injecao_curva"))
        self._cell(f_coord, 4, 0, "Dial"); self._cell(f_coord, 4, 1, d.get("param_consumo_dial")); self._cell(f_coord, 4, 2, d.get("param_injecao_dial"))
        self._cell(f_coord, 5, 0, "T. Adic."); self._cell(f_coord, 5, 1, d.get("param_consumo_t_adic")); self._cell(f_coord, 5, 2, d.get("param_injecao_t_adic"))
        self._cell(f_coord, 6, 0, "Pot. de Consumo (kW)"); self._cell(f_coord, 6, 1, d.get("param_consumo_pot_kw"), cs=2)
        self._cell(f_coord, 7, 0, "Pot. de Injeção (kW)"); self._cell(f_coord, 7, 1, d.get("param_injecao_pot_kw"), cs=2)

        f_tensao = tk.Frame(col_meio); f_tensao.pack(anchor='w', fill='x', pady=(0, 10))
        self._cell(f_tensao, 0, 0, "Tensão [kV] da rede"); self._cell(f_tensao, 0, 1, d.get("tensao_kv_rede"))
        self._cell(f_tensao, 1, 0, "Carga - fase A [A]"); self._cell(f_tensao, 1, 1, d.get("carga_fase_a"))
        self._cell(f_tensao, 2, 0, "Carga - fase B [A]"); self._cell(f_tensao, 2, 1, d.get("carga_fase_b"))
        self._cell(f_tensao, 3, 0, "Carga - fase C [A]"); self._cell(f_tensao, 3, 1, d.get("carga_fase_c"))

        f_falta = tk.Frame(col_meio); f_falta.pack(anchor='w', fill='x')
        self._cell(f_falta, 0, 0, "Corrente de Falta", cs=2)
        self._cell(f_falta, 1, 0, "FASE - CC máximo [A]"); self._cell(f_falta, 1, 1, d.get("corrente_falta_fase_cc_max"))
        self._cell(f_falta, 2, 0, "FASE - Sensibilidade principal [A]"); self._cell(f_falta, 2, 1, d.get("corrente_falta_fase_sens_princ"))
        self._cell(f_falta, 3, 0, "TERRA - Sensibilidade principal [A]"); self._cell(f_falta, 3, 1, d.get("corrente_falta_terra_sens_princ"))

        f_montante = tk.Frame(col_direita); f_montante.pack(anchor='w', fill='x', pady=(0, 10))
        self._cell(f_montante, 0, 0, ""); self._cell(f_montante, 0, 1, "Lado 1\nA montante"); self._cell(f_montante, 0, 2, "Lado 2")
        self._cell(f_montante, 1, 0, "Número do Equipamento"); self._cell(f_montante, 1, 1, d.get("eqpto_montante_numero_l1")); self._cell(f_montante, 1, 2, d.get("eqpto_montante_numero_l2"))
        self._cell(f_montante, 2, 0, "Pick-up Fase - G1 (A)"); self._cell(f_montante, 2, 1, d.get("eqpto_montante_pickup_fase_g1_l1")); self._cell(f_montante, 2, 2, d.get("eqpto_montante_pickup_fase_g1_l2"))
        self._cell(f_montante, 3, 0, "Pick-up Fase - G2 (A)"); self._cell(f_montante, 3, 1, d.get("eqpto_montante_pickup_fase_g2_l1")); self._cell(f_montante, 3, 2, d.get("eqpto_montante_pickup_fase_g2_l2"))
        self._cell(f_montante, 4, 0, "Pick-up Terra - G1 (A)"); self._cell(f_montante, 4, 1, d.get("eqpto_montante_pickup_terra_g1_l1")); self._cell(f_montante, 4, 2, d.get("eqpto_montante_pickup_terra_g1_l2"))
        self._cell(f_montante, 5, 0, "Pick-up Terra - G2 (A)"); self._cell(f_montante, 5, 1, d.get("eqpto_montante_pickup_terra_g2_l1")); self._cell(f_montante, 5, 2, d.get("eqpto_montante_pickup_terra_g2_l2"))

        f_cabo = tk.Frame(col_direita); f_cabo.pack(anchor='w', fill='x')
        self._cell(f_cabo, 0, 0, "Cabo crítico no trecho"); self._cell(f_cabo, 0, 1, "Nominal [A]"); self._cell(f_cabo, 0, 2, "Admissível [A]")
        self._cell(f_cabo, 1, 0, d.get("cabo_critico_trecho")); self._cell(f_cabo, 1, 1, d.get("cabo_critico_nominal")); self._cell(f_cabo, 1, 2, d.get("cabo_critico_admissivel"))
        
        wrap_tabelas = tk.Frame(main_container); wrap_tabelas.pack(pady=10, anchor="center")
        header = tk.Frame(wrap_tabelas, bd=1, relief="solid"); [header.grid_columnconfigure(c, minsize=w) for c, w in enumerate(self.col_widths)]; [header.grid_rowconfigure(r, minsize=30, weight=1) for r in range(3)]; self._cell(header, 0, 0, "Grupo Normal = Grupo de Consumo", cs=9); self._cell(header, 1, 0, "  Grupos  ", rs=2); self._cell(header, 1, 1, "FASE", cs=4); self._cell(header, 1, 5, "TERRA", cs=4); self._cell(header, 2, 1, "  Pickup  "); self._cell(header, 2, 2, "  Sequência  "); self._cell(header, 2, 3, "  Curva Lenta  "); self._cell(header, 2, 4, "  Curva Rápida  "); self._cell(header, 2, 5, "  Pickup  "); self._cell(header, 2, 6, "  Sequência  "); self._cell(header, 2, 7, "  Curva Lenta  "); self._cell(header, 2, 8, "  Curva Rápida  "); header.pack(pady=5)
        for i in range(1, 4): self._criar_tabela_grupo_visualizacao(wrap_tabelas, f"  Grupo {i}  ", i)
        
        condicao_upper = (d.get("condição") or "").upper()
        if condicao_upper in ["ACESS INV", "ACESS S/INV"]:
            header_rep = tk.Frame(wrap_tabelas, bd=1, relief="solid"); [header_rep.grid_columnconfigure(c, minsize=w) for c, w in enumerate(self.col_widths)]; [header_rep.grid_rowconfigure(r, minsize=30, weight=1) for r in range(3)]; self._cell(header_rep, 0, 0, "Grupo Invertido = Grupo de Injeção", cs=9); self._cell(header_rep, 1, 0, "  Grupos  ", rs=2); self._cell(header_rep, 1, 1, "FASE", cs=4); self._cell(header_rep, 1, 5, "TERRA", cs=4); self._cell(header_rep, 2, 1, "  Pickup  "); self._cell(header_rep, 2, 2, "  Sequência  "); self._cell(header_rep, 2, 3, "  Curva Lenta  "); self._cell(header_rep, 2, 4, "  Curva Rápida  "); self._cell(header_rep, 2, 5, "  Pickup  "); self._cell(header_rep, 2, 6, "  Sequência  "); self._cell(header_rep, 2, 7, "  Curva Lenta  "); self._cell(header_rep, 2, 8, "  Curva Rápida  "); header_rep.pack(pady=(20, 5))
            for i in range(1, 4): self._criar_tabela_grupo_visualizacao(wrap_tabelas, f"  Grupo {i}  ", i, suffix="_rep")
        
        frame_obs = tk.Frame(main_container); frame_obs.pack(pady=(10, 5), padx=10, fill='x', expand=False); tk.Label(frame_obs, text="Observações:", font=FONTE_PADRAO).pack(anchor='w'); text_container = tk.Frame(frame_obs, height=120, relief="solid", bd=1); text_container.pack(fill='x', expand=False); text_container.pack_propagate(False); obs_text = tk.Text(text_container, relief="flat", bd=0, font=FONTE_PADRAO, wrap="word"); obs_text.insert("1.0", d.get("observacoes") or "Nenhuma observação."); obs_text.config(state="disabled"); obs_text.pack(fill="both", expand=True)
        
        ttk.Button(main_container, text="Fechar", command=self.destroy).pack(pady=20)

    def _criar_tabela_grupo_visualizacao(self, parent, group_name, group_index, suffix=""):
        frame_tabela = tk.Frame(parent, bd=1, relief="solid"); [frame_tabela.grid_columnconfigure(c, minsize=w) for c, w in enumerate(self.col_widths)]; [frame_tabela.grid_rowconfigure(r, minsize=30, weight=1) for r in range(3)]; d = self.dados_ficha
        self._cell(frame_tabela, 0, 0, group_name, rs=3); self._cell(frame_tabela, 0, 1, d.get(f'g{group_index}_pickup_fase{suffix}'), rs=3); self._cell(frame_tabela, 0, 2, d.get(f'g{group_index}_sequencia{suffix}'), rs=3); self._cell(frame_tabela, 0, 3, d.get(f'g{group_index}_curva_lenta_tipo{suffix}'))
        
        sub_lenta = tk.Frame(frame_tabela, bd=0); 
        sub_lenta.grid_propagate(False)
        sub_lenta.grid(row=1, column=3, rowspan=2, sticky="nsew")
        
        sub_lenta.grid_rowconfigure(0, weight=1); sub_lenta.grid_rowconfigure(1, weight=1)
        sub_lenta.grid_columnconfigure(0, weight=1, minsize=55)
        sub_lenta.grid_columnconfigure(1, weight=1, minsize=55)

        tk.Label(sub_lenta, text="Dial", font=FONTE_PEQUENA, relief="solid", bd=1).grid(row=0, column=0, sticky="nsew")
        tk.Label(sub_lenta, text="T. Adic.", font=FONTE_PEQUENA, relief="solid", bd=1).grid(row=0, column=1, sticky="nsew")
        tk.Label(sub_lenta, text=d.get(f'g{group_index}_curva_lenta_dial{suffix}'), font=FONTE_PEQUENA, relief="solid", bd=1).grid(row=1, column=0, sticky="nsew")
        tk.Label(sub_lenta, text=d.get(f'g{group_index}_curva_lenta_tadic{suffix}'), font=FONTE_PEQUENA, relief="solid", bd=1).grid(row=1, column=1, sticky="nsew")
        
        self._cell(frame_tabela, 0, 4, "IEC Inversa")
        
        sub_rapida = tk.Frame(frame_tabela, bd=0)
        sub_rapida.grid_propagate(False)
        sub_rapida.grid(row=1, column=4, rowspan=2, sticky="nsew")
        
        sub_rapida.grid_rowconfigure(0, weight=1); sub_rapida.grid_rowconfigure(1, weight=1)
        sub_rapida.grid_columnconfigure(0, weight=1, minsize=55)
        sub_rapida.grid_columnconfigure(1, weight=1, minsize=55)

        tk.Label(sub_rapida, text="Dial", font=FONTE_PEQUENA, relief="solid", bd=1).grid(row=0, column=0, sticky="nsew")
        tk.Label(sub_rapida, text="T. Adic.", font=FONTE_PEQUENA, relief="solid", bd=1).grid(row=0, column=1, sticky="nsew")
        tk.Label(sub_rapida, text=d.get(f'g{group_index}_curva_rapida_dial{suffix}'), font=FONTE_PEQUENA, relief="solid", bd=1).grid(row=1, column=0, sticky="nsew")
        tk.Label(sub_rapida, text=d.get(f'g{group_index}_curva_rapida_tadic{suffix}'), font=FONTE_PEQUENA, relief="solid", bd=1).grid(row=1, column=1, sticky="nsew")
        
        self._cell(frame_tabela, 0, 5, d.get(f'g{group_index}_pickup_terra{suffix}'), rs=3); self._cell(frame_tabela, 0, 6, d.get(f'g{group_index}_sequencia_terra{suffix}'), rs=3)
        self._cell(frame_tabela, 0, 7, "T. Definido"); self._cell(frame_tabela, 1, 7, "Tempo (s)"); self._cell(frame_tabela, 2, 7, d.get(f'g{group_index}_terra_tempo_lenta{suffix}'))
        self._cell(frame_tabela, 0, 8, "T. Definido"); self._cell(frame_tabela, 1, 8, "Tempo (s)"); self._cell(frame_tabela, 2, 8, d.get(f'g{group_index}_terra_tempo_rapida{suffix}'))
        frame_tabela.pack(pady=(0, 5))

class VisualizacaoFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.filtro_eqpto = tk.StringVar(); self.filtro_malha = tk.StringVar(); self.filtro_alimentador = tk.StringVar(); self.filtro_condicao = tk.StringVar()
        self.logo_photo = None
        self.criar_widgets()

    def _get_opcoes_formatadas(self, categoria):
        opcoes_raw = self.controller.get_opcoes_por_categoria_geral(categoria)
        return [item['valor'] for item in opcoes_raw] if opcoes_raw else []

    def criar_widgets(self):
        style = ttk.Style()
        style.configure("Treeview", font=FONTE_PADRAO, rowheight=30)
        style.configure("Treeview.Heading", font=FONTE_PADRAO)
        
        top_frame = tk.Frame(self)
        top_frame.pack(fill='x', pady=10)

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
            
            logo_label = tk.Label(top_frame, image=self.logo_photo)
            logo_label.pack()
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o logo no módulo de Visualização. Erro: {e}")

        frame_filtros = tk.LabelFrame(self, text="Filtros de Busca", padx=15, pady=15, font=FONTE_PADRAO); frame_filtros.pack(padx=10, pady=10, fill="x")
        tk.Label(frame_filtros, text="Equipamento:", font=FONTE_PADRAO).grid(row=0, column=0, padx=5, pady=5, sticky="w"); ttk.Entry(frame_filtros, textvariable=self.filtro_eqpto, width=30, font=FONTE_PADRAO).grid(row=0, column=1, padx=5, pady=5)
        opcoes_malha = self._get_opcoes_formatadas('malha'); tk.Label(frame_filtros, text="Malha:", font=FONTE_PADRAO).grid(row=0, column=2, padx=5, pady=5, sticky="w"); ttk.Combobox(frame_filtros, textvariable=self.filtro_malha, values=[""] + opcoes_malha, state="readonly", font=FONTE_PADRAO, width=28).grid(row=0, column=3, padx=5, pady=5)
        tk.Label(frame_filtros, text="Alimentador:", font=FONTE_PADRAO).grid(row=1, column=0, padx=5, pady=5, sticky="w"); opcoes_alimentador = self._get_opcoes_formatadas('alimentador'); ttk.Combobox(frame_filtros, textvariable=self.filtro_alimentador, values=[""] + opcoes_alimentador, width=28, font=FONTE_PADRAO).grid(row=1, column=1, padx=5, pady=5)
        opcoes_condicao = self._get_opcoes_formatadas('condicao'); tk.Label(frame_filtros, text="Condição:", font=FONTE_PADRAO).grid(row=1, column=2, padx=5, pady=5, sticky="w"); ttk.Combobox(frame_filtros, textvariable=self.filtro_condicao, values=[""] + opcoes_condicao, state="readonly", font=FONTE_PADRAO, width=28).grid(row=1, column=3, padx=5, pady=5)
        frame_botoes = tk.Frame(frame_filtros); frame_botoes.grid(row=1, column=4, padx=20, pady=5, sticky="e"); ttk.Button(frame_botoes, text="Buscar", command=self.executar_busca).pack(side="left", padx=5); ttk.Button(frame_botoes, text="Limpar Filtros", command=self.limpar_filtros).pack(side="left", padx=5); frame_filtros.grid_columnconfigure(4, weight=1)
        
        frame_resultados = tk.LabelFrame(self, text="Resultados da Busca (Equipamentos)", padx=10, pady=10, font=FONTE_PADRAO); frame_resultados.pack(padx=10, pady=10, fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(frame_resultados); scrollbar.pack(side="right", fill="y")
        
        self.tree = ttk.Treeview(frame_resultados, yscrollcommand=scrollbar.set, selectmode="browse")
        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading("#0", text="Detalhes do Equipamento Registrado", anchor='w')
        self.tree.bind("<Double-1>", self.mostrar_detalhes_selecionado)

    def executar_busca(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        filtros = { "eqpto": self.filtro_eqpto.get().strip(), "malha": self.filtro_malha.get().strip(), "alimentador": self.filtro_alimentador.get().strip(), "condição": self.filtro_condicao.get().strip() }
        if not any(filtros.values()):
            messagebox.showwarning("Busca Inválida", "Preencha pelo menos um campo.")
            return

        resultados = self.controller.buscar_todos_registros_visualizacao(filtros)
        
        if not resultados:
            self.tree.insert("", "end", text="Nenhum equipamento encontrado.")
            return

        equipamentos_agrupados = defaultdict(list)
        for row in resultados:
            equipamentos_agrupados[row['eqpto']].append(row)
            
        total_encontrado = len(equipamentos_agrupados)
        self.tree.insert("", "end", text=f" {total_encontrado} equipamento(s) encontrado(s). Duplo-clique para ver detalhes.")

        for eqpto, registros in equipamentos_agrupados.items():
            registro_recente = registros[0]
            registros_antigos = registros[1:]
            
            data_f = datetime.strptime(registro_recente['data_registro'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
            prefixo = "+ " if registros_antigos else "  "
            
            rec = registro_recente
            display_recente = (f"{prefixo}{rec.get('eqpto','')} | Malha: {rec.get('malha','')} | "
                               f"Alimentador: {rec.get('alimentador','')} | NS: {rec.get('ns','')} | "
                               f"Condição: {rec.get('condição','')} | Fabricante: {rec.get('fabricante','')} | "
                               f"Mídia: {rec.get('mídia','')} | Data: {data_f}")

            parent_id = self.tree.insert("", "end", iid=rec['id'], text=display_recente, open=False)

            for registro_antigo in registros_antigos:
                data_antiga_f = datetime.strptime(registro_antigo['data_registro'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
                
                rec_antigo = registro_antigo
                display_antigo = (f"  └─ {rec_antigo.get('eqpto','')} | Malha: {rec_antigo.get('malha','')} | "
                                  f"Alimentador: {rec_antigo.get('alimentador','')} | NS: {rec_antigo.get('ns','')} | "
                                  f"Condição: {rec_antigo.get('condição','')} | Fabricante: {rec_antigo.get('fabricante','')} | "
                                  f"Mídia: {rec_antigo.get('mídia','')} | Data: {data_antiga_f}")
                
                self.tree.insert(parent_id, "end", iid=rec_antigo['id'], text=display_antigo)

    def limpar_filtros(self):
        self.filtro_eqpto.set(""); self.filtro_malha.set(""); self.filtro_alimentador.set(""); self.filtro_condicao.set("")
        for i in self.tree.get_children():
            self.tree.delete(i)

    def mostrar_detalhes_selecionado(self, event=None):
        try:
            selected_item = self.tree.selection()[0]
            if selected_item:
                id_ficha = int(selected_item)
                DetalhesWindow(self, self.controller, id_ficha)
        except (IndexError, ValueError):
            pass
