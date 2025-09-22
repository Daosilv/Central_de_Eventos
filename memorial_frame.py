import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from datetime import datetime
import os
import sys
import json

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

# Importa a janela de observação do módulo de ajustes para ser reutilizada
from ajustes_frame import ObsWindow

FONTE_PADRAO = ("Times New Roman", 12)
FONTE_PEQUENA = ("Times New Roman", 10)
FONTE_MUITO_PEQUENA = ("Times New Roman", 8)
SIDEBAR_WIDTH = 450

class MapSelectDialog(simpledialog.Dialog):
    def __init__(self, parent, title, maps, controller):
        self.maps = maps
        self.map_id_map = {m['nome']: m['id'] for m in self.maps}
        self.result = None
        self.controller = controller
        super().__init__(parent, title)

    def body(self, master):
        self.controller.center_window(self.winfo_toplevel())
        tk.Label(master, text="Selecione o mapa de exportação:").pack(padx=5, pady=5)
        self.map_var = tk.StringVar()
        map_names = sorted(self.map_id_map.keys())
        
        self.map_combo = ttk.Combobox(master, textvariable=self.map_var, values=map_names, state="readonly")
        self.map_combo.pack(padx=5, pady=5)
        if map_names:
            self.map_combo.set(map_names[0])
        return self.map_combo

    def apply(self):
        selected_name = self.map_var.get()
        if selected_name:
            self.result = self.map_id_map[selected_name]

class BuscaDialog(tk.Toplevel):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_id = None

        self.title("Buscar Equipamento")
        self.geometry("800x500")
        self.transient(parent)
        self.grab_set()

        self.controller.center_window(self)

        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        frame_filtros = tk.LabelFrame(main_frame, text="Filtros", padx=10, pady=10)
        frame_filtros.pack(fill="x", pady=(0, 10))
        
        self.filtro_eqpto = tk.StringVar()
        self.filtro_malha = tk.StringVar()
        self.filtro_alimentador = tk.StringVar()

        tk.Label(frame_filtros, text="Equipamento:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame_filtros, textvariable=self.filtro_eqpto, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame_filtros, text="Malha:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Entry(frame_filtros, textvariable=self.filtro_malha, width=20).grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(frame_filtros, text="Alimentador:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(frame_filtros, textvariable=self.filtro_alimentador, width=20).grid(row=1, column=1, padx=5, pady=5)

        btn_buscar = ttk.Button(frame_filtros, text="Buscar", command=self.executar_busca)
        btn_buscar.grid(row=1, column=3, padx=5, pady=5, sticky="e")

        frame_resultados = tk.LabelFrame(main_frame, text="Resultados", padx=10, pady=10)
        frame_resultados.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(frame_resultados)
        scrollbar.pack(side="right", fill="y")
        self.listbox_resultados = tk.Listbox(frame_resultados, yscrollcommand=scrollbar.set, font=FONTE_PADRAO)
        self.listbox_resultados.pack(fill="both", expand=True)
        self.listbox_resultados.bind("<Double-1>", lambda e: self.carregar_selecionado())
        scrollbar.config(command=self.listbox_resultados.yview)
        self.id_map = {}

        frame_botoes = tk.Frame(main_frame)
        frame_botoes.pack(fill="x", pady=(10, 0))
        ttk.Button(frame_botoes, text="Carregar", command=self.carregar_selecionado).pack(side="right", padx=5)
        ttk.Button(frame_botoes, text="Cancelar", command=self.destroy).pack(side="right")

        self.wait_window(self)

    def executar_busca(self):
        self.listbox_resultados.delete(0, tk.END)
        self.id_map.clear()

        filtros = {
            "eqpto": self.filtro_eqpto.get().strip(),
            "malha": self.filtro_malha.get().strip(),
            "alimentador": self.filtro_alimentador.get().strip(),
        }

        filtros_ativos = {k: v for k, v in filtros.items() if v}
        if not filtros_ativos:
            messagebox.showwarning("Busca Inválida", "Preencha pelo menos um campo para buscar.", parent=self)
            return

        resultados = self.controller.buscar_registros(filtros_ativos)
        if not resultados:
            self.listbox_resultados.insert(tk.END, "Nenhum equipamento encontrado.")
        else:
            for row in resultados:
                data_f = datetime.strptime(row['data_registro'].split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                display = f"Eqpto: {row['eqpto']} | Malha: {row['malha']} | Alimentador: {row['alimentador']} | Data: {data_f}"
                idx = self.listbox_resultados.size()
                self.listbox_resultados.insert(tk.END, display)
                self.id_map[idx] = row['id']

    def carregar_selecionado(self):
        sel = self.listbox_resultados.curselection()
        if not sel:
            messagebox.showwarning("Nenhuma Seleção", "Selecione um equipamento para carregar.", parent=self)
            return
        
        self.selected_id = self.id_map.get(sel[0])
        if self.selected_id:
            self.destroy()

class AutocompleteCombobox(ttk.Combobox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._completion_list = []
        self.set_completion_list([])
        self.bind('<KeyRelease>', self._on_keyrelease)
        self.bind('<FocusOut>', self._on_focus_out)

    def set_completion_list(self, completion_list):
        self._completion_list = sorted(list(set(completion_list)))
        self['values'] = self._completion_list
    
    def _on_keyrelease(self, event):
        value = self.get().lower()
        
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Home", "End"):
            pass

        if value == '':
            self['values'] = self._completion_list
            return
        else:
            data = []
            for item in self._completion_list:
                if item.lower().startswith(value):
                    data.append(item)
            
            if self['values'] != tuple(data):
                self['values'] = data
        
        if self.get() and self['values']:
             self.event_generate('<Down>')

    def _on_focus_out(self, event):
        current_value = self.get()
        if current_value and self['values'] and current_value not in self['values']:
            if self['values'] and self['values'][0].lower().startswith(current_value.lower()):
                self.set(self['values'][0])
            else:
                self.set('')

class MemorialCalculoFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent_window = parent
        self.logo_photo = None
        
        self.configure(bg="lightblue")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('.', background='white', foreground='black')
        
        style.map('TCombobox',
                  fieldbackground=[('readonly', 'white'), ('!readonly', 'white')],
                  selectbackground=[('readonly', 'white'), ('!readonly', 'white')],
                  selectforeground=[('readonly', 'black'), ('!readonly', 'black')])
                  
        style.layout('Arrowless.TCombobox',
            [('Combobox.padding', {'expand': '1', 'sticky': 'nswe', 'children':
                [('Combobox.focus', {'expand': '1', 'sticky': 'nswe', 'children':
                    [('Combobox.text', {'sticky': 'nswe'})]
                })]
            })]
        )
        style.configure('Centered.TCombobox', justify='center')

        self.comboboxes_cabecalho = {}
        self.fabricantes_map = {}
        self.modelos_map = {}
        self.comandos_map = {}
        self.cabos_map = {}

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
            "Telecontrolado": tk.StringVar(), 
            "Bypass": tk.StringVar(),
            "Vinculado a Acessante": tk.StringVar(),
            "Eqpto Acessante": tk.StringVar(),
            "Manobra Efetiva": tk.StringVar(),
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
        self.campos_dict["Condição"].trace_add("write", self._gerenciar_visibilidade_tabelas)
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
        self.vars_grupos_secc = {}
        self.tabelas_grupo_frames_secc = []
        
        self.tempo_morto_widgets = []
        self.tempo_morto_widgets_rep = []
        self.tempo_morto_widgets_secc = []

        self.vcmd_limite = self.register(self._limitar_tamanho)
        self.vcmd_4 = self.register(lambda P: self._limitar_tamanho(P, '4'))
        
        self.campos_dict["Siom"].trace_add("write", self.formatar_siom)
        self.campos_dict["Coord"].trace_add("write", self.formatar_coord)
        
        scroll_container = tk.Frame(self, bg='white')
        scroll_container.pack(fill="both", expand=True, padx=20, pady=(20, 0))

        self.criar_layout_principal(scroll_container)
        self._criar_layout_cabecalho()
        self.criar_layout_formulario()

        if 'grupo_1' in self.vars_grupos and 'grupo_3' in self.vars_grupos:
            self.vars_grupos['grupo_1']['sequencia'].trace_add("write", self._replicar_sequencia_g1_para_g3)
        self.atualizar_todas_as_listas()
        self.after(10, self._gerenciar_campo_acessante)
        self.after(10, self._gerenciar_visibilidade_tabelas)
        
    @staticmethod
    def get_db_columns():
        colunas_principais = [ "autor", "eqpto", "malha", "condição", "motivador", "alimentador", "ns", "siom", "data", "coord", "endereço", "mídia", "fabricante", "modelo", "comando", "telecontrolado", "bypass", "vinculado_acessante", "eqpto_acessante", "manobra_efetiva", "param_consumo_pickup", "param_consumo_curva", "param_consumo_dial", "param_consumo_t_adic", "param_consumo_pot_kw", "param_injecao_pickup", "param_injecao_curva", "param_injecao_dial", "param_injecao_t_adic", "param_injecao_pot_kw", "tensao_kv_rede", "carga_fase_a", "carga_fase_b", "carga_fase_c", "cabo_critico_trecho", "cabo_critico_nominal", "cabo_critico_admissivel", "corrente_falta_fase_cc_max", "corrente_falta_fase_sens_princ", "corrente_falta_terra_sens_princ", "eqpto_montante_numero_l1", "eqpto_montante_numero_l2", "eqpto_montante_pickup_fase_g1_l1", "eqpto_montante_pickup_fase_g1_l2", "eqpto_montante_pickup_fase_g2_l1", "eqpto_montante_pickup_fase_g2_l2", "eqpto_montante_pickup_terra_g1_l1", "eqpto_montante_pickup_terra_g1_l2", "eqpto_montante_pickup_terra_g2_l1", "eqpto_montante_pickup_terra_g2_l2", ]
        campos_grupo = ["pickup_fase", "sequencia", "curva_lenta_tipo", "curva_lenta_dial", "curva_lenta_tadic", "curva_rapida_dial", "curva_rapida_tadic", "pickup_terra", "sequencia_terra", "terra_tempo_lenta", "terra_tempo_rapida"]
        colunas_grupos = [f'g{i}_{c}' for i in range(1, 4) for c in campos_grupo]
        colunas_grupos_rep = [f'g{i}_{c}_rep' for i in range(1, 4) for c in campos_grupo]
        campos_grupo_secc = ["pickup_fase", "sequencia", "pickup_terra", "sequencia_terra"]
        colunas_grupos_secc = [f'g{i}_{c}_secc' for i in range(1, 4) for c in campos_grupo_secc]
        colunas_tempo_morto = [f'tempo_morto_v{i}' for i in range(1, 6)]
        colunas_adicionais = ['observacoes', 'anexos']
        return colunas_principais + colunas_grupos + colunas_grupos_rep + colunas_grupos_secc + colunas_tempo_morto + colunas_adicionais

    def criar_layout_principal(self, scroll_container):
        scroll_container.grid_rowconfigure(0, weight=1); scroll_container.grid_columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(scroll_container, highlightthickness=0, bg='white'); v_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview); h_scrollbar = ttk.Scrollbar(scroll_container, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set); self.canvas.grid(row=0, column=0, sticky="nsew"); v_scrollbar.grid(row=0, column=1, sticky="ns"); h_scrollbar.grid(row=1, column=0, sticky="ew")
        self.content_holder_frame = tk.Frame(self.canvas, bg='white'); self.canvas_window_id = self.canvas.create_window((0, 0), window=self.content_holder_frame, anchor="nw")
        self.content_holder_frame.bind("<Configure>", self.on_frame_configure); self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)); self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        
        self.content_holder_frame.grid_columnconfigure(0, minsize=900); self.content_holder_frame.grid_columnconfigure(1, weight=0); self.content_holder_frame.grid_rowconfigure(2, weight=1)

        logo_frame = tk.Frame(self.content_holder_frame, bg='white', bd=1, relief="solid")
        logo_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")
        try:
            if Image is None or ImageTk is None: raise ImportError("Pillow não instalado")
            logo_path = r'C:\BD_APP_Cemig\plemt_logo_ao_lado.PNG'
            logo_image = Image.open(logo_path)
            original_width, original_height = logo_image.size
            aspect_ratio = original_width / original_height
            new_height = 75
            new_width = int(new_height * aspect_ratio)
            resized_image = logo_image.resize((new_width, new_height))
            self.logo_photo = ImageTk.PhotoImage(resized_image)
            logo_label = tk.Label(logo_frame, image=self.logo_photo, bg='white')
            logo_label.pack()
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o logo no Memorial de Cálculo. Erro: {e}")
        
        self.header_frame = tk.Frame(self.content_holder_frame, bg='white'); self.header_frame.grid(row=1, column=0, sticky="new", padx=10, pady=10)
        self.main_form_frame = tk.Frame(self.content_holder_frame, bg='white'); self.main_form_frame.grid(row=2, column=0, sticky="nsew", padx=10)
        
        sidebar_frame = tk.LabelFrame(self.content_holder_frame, text="Histórico", width=SIDEBAR_WIDTH, padx=5, pady=5, bg='white'); sidebar_frame.grid(row=1, column=1, rowspan=2, sticky="ns", pady=10)
        sidebar_frame.pack_propagate(False)

        ttk.Button(sidebar_frame, text="Atualizar Listas", command=self.atualizar_todas_as_listas).pack(fill='x', pady=(0, 10))
        ajustes_container = tk.LabelFrame(sidebar_frame, text="Ajustes Recentes", padx=5, pady=5, bg='white'); ajustes_container.pack(fill='both', expand=True, pady=(0, 5))
        frame_busca_ajustes = tk.Frame(ajustes_container, bg='white'); frame_busca_ajustes.pack(fill='x'); tk.Label(frame_busca_ajustes, text="Buscar:", bg='white').pack(side='left'); tk.Entry(frame_busca_ajustes, textvariable=self.busca_ajustes_var).pack(side='left', fill='x', expand=True, padx=5)
        
        ajustes_canvas_frame = tk.Frame(ajustes_container, bg='white', relief="solid", bd=1); ajustes_canvas_frame.pack(fill='both', expand=True, pady=(5,0))
        ajustes_h_scrollbar = ttk.Scrollbar(ajustes_canvas_frame, orient="horizontal")
        ajustes_h_scrollbar.pack(side="bottom", fill="x")
        self.ajustes_canvas = tk.Canvas(ajustes_canvas_frame, highlightthickness=0, bg='white', xscrollcommand=ajustes_h_scrollbar.set)
        ajustes_scrollbar = ttk.Scrollbar(ajustes_canvas_frame, orient="vertical", command=self.ajustes_canvas.yview)
        self.ajustes_items_frame = tk.Frame(self.ajustes_canvas, bg='white')
        self.ajustes_window_id = self.ajustes_canvas.create_window((0, 0), window=self.ajustes_items_frame, anchor="nw")
        self.ajustes_canvas.configure(yscrollcommand=ajustes_scrollbar.set)
        ajustes_scrollbar.pack(side="right", fill="y"); self.ajustes_canvas.pack(side="left", fill="both", expand=True)
        ajustes_h_scrollbar.config(command=self.ajustes_canvas.xview)
        self.ajustes_items_frame.bind("<Configure>", lambda e: self.ajustes_canvas.configure(scrollregion=self.ajustes_canvas.bbox("all")))
        
        rascunhos_container = tk.LabelFrame(sidebar_frame, text="Rascunhos", padx=5, pady=5, bg='white'); rascunhos_container.pack(fill='both', expand=True, pady=(5, 5)); frame_busca_rascunhos = tk.Frame(rascunhos_container, bg='white'); frame_busca_rascunhos.pack(fill='x'); tk.Label(frame_busca_rascunhos, text="Buscar:", bg='white').pack(side='left'); tk.Entry(frame_busca_rascunhos, textvariable=self.busca_rascunhos_var).pack(side='left', fill='x', expand=True, padx=5); frame_rascunhos_actions = tk.Frame(rascunhos_container, bg='white'); frame_rascunhos_actions.pack(fill='x', pady=(5,0)); ttk.Checkbutton(frame_rascunhos_actions, text="Selecionar Tudo", variable=self.selecionar_tudo_rascunhos_var, command=self._toggle_selecionar_tudo_rascunhos).pack(side='left'); tk.Button(frame_rascunhos_actions, text="X", fg="red", font=("Helvetica", 10, "bold"), command=self.deletar_rascunhos_selecionados, width=2, relief="flat", cursor="hand2", bg='white').pack(side='right', padx=(0,5))
        
        rascunhos_canvas_frame = tk.Frame(rascunhos_container, bg='white', relief="solid", bd=1); rascunhos_canvas_frame.pack(fill='both', expand=True, pady=5)
        rascunhos_h_scrollbar = ttk.Scrollbar(rascunhos_canvas_frame, orient="horizontal")
        rascunhos_h_scrollbar.pack(side="bottom", fill="x")
        self.rascunhos_canvas = tk.Canvas(rascunhos_canvas_frame, highlightthickness=0, bg='white', xscrollcommand=rascunhos_h_scrollbar.set)
        rascunhos_scrollbar = ttk.Scrollbar(rascunhos_canvas_frame, orient="vertical", command=self.rascunhos_canvas.yview)
        self.rascunhos_items_frame = tk.Frame(self.rascunhos_canvas, bg='white')
        self.rascunhos_window_id = self.rascunhos_canvas.create_window((0, 0), window=self.rascunhos_items_frame, anchor="nw")
        self.rascunhos_canvas.configure(yscrollcommand=rascunhos_scrollbar.set)
        rascunhos_scrollbar.pack(side="right", fill="y"); self.rascunhos_canvas.pack(side="left", fill="both", expand=True)
        rascunhos_h_scrollbar.config(command=self.rascunhos_canvas.xview)
        self.rascunhos_items_frame.bind("<Configure>", lambda e: self.rascunhos_canvas.configure(scrollregion=self.rascunhos_canvas.bbox("all")))

    def _get_opcoes_formatadas_geral(self, categoria):
        opcoes_raw = self.controller.get_opcoes_por_categoria_geral(categoria)
        return [item['valor'] for item in opcoes_raw] if opcoes_raw else []

    def _criar_layout_cabecalho(self):
        frame_campos = tk.Frame(self.header_frame, bg='white')
        frame_campos.pack(fill="x")
        
        frame_campos.grid_columnconfigure(0, weight=1)

        row1_frame = tk.Frame(frame_campos, bg='white'); row1_frame.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        self._criar_celula_cabecalho(row1_frame, "Autor:", self.campos_dict["Autor"], tk.Entry, {}, 4, 61)
        self._criar_celula_cabecalho(row1_frame, "Data:", self.campos_dict["Data"], tk.Entry, {}, 4, 12)
        self._criar_celula_cabecalho(row1_frame, "NS:", self.campos_dict["NS"], tk.Entry, {}, 3, 20)
        self._criar_celula_cabecalho(row1_frame, "Eqpto:", self.campos_dict["Eqpto"], tk.Entry, {}, 5, 10)
        self._criar_celula_cabecalho(row1_frame, "Condição:", self.campos_dict["Condição"], AutocompleteCombobox, {}, 8, 10, categoria_db='condicao', tipo_lista='geral', expand=True)

        row2_frame = tk.Frame(frame_campos, bg='white'); row2_frame.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        self._criar_celula_cabecalho(row2_frame, "Malha:", self.campos_dict["Malha"], AutocompleteCombobox, {}, 6, 10, categoria_db='malha', tipo_lista='geral')
        self._criar_celula_cabecalho(row2_frame, "Alimentador:", self.campos_dict["Alimentador"], AutocompleteCombobox, {}, 10, 17, categoria_db='alimentador', tipo_lista='geral')
        self._criar_celula_cabecalho(row2_frame, "Motivador:", self.campos_dict["Motivador"], AutocompleteCombobox, {}, 8, 8, categoria_db='motivador', tipo_lista='geral')
        self._criar_celula_cabecalho(row2_frame, "Coord:", self.campos_dict["Coord"], tk.Entry, {}, 5, 20)
        self._criar_celula_cabecalho(row2_frame, "Endereço:", self.campos_dict["Endereço"], tk.Entry, {}, 8, 45, expand=True)

        row3_frame = tk.Frame(frame_campos, bg='white'); row3_frame.grid(row=2, column=0, sticky="ew", pady=(0, 2))
        self._criar_celula_cabecalho(row3_frame, "Mídia:", self.campos_dict["Mídia"], AutocompleteCombobox, {}, 6, 10, categoria_db='midia', tipo_lista='geral')
        self._criar_celula_cabecalho(row3_frame, "Fabricante:", self.campos_dict["Fabricante"], AutocompleteCombobox, {}, 10, 20, nome_widget='fabricante')
        self._criar_celula_cabecalho(row3_frame, "Modelo:", self.campos_dict["Modelo"], AutocompleteCombobox, {}, 6, 20, nome_widget='modelo')
        self._criar_celula_cabecalho(row3_frame, "Comando:", self.campos_dict["Comando"], AutocompleteCombobox, {}, 8, 15, nome_widget='comando')
        self._criar_celula_cabecalho(row3_frame, "Telecontrolado:", self.campos_dict["Telecontrolado"], AutocompleteCombobox, {}, 12, 5, categoria_db='telecontrolado', tipo_lista='geral')
        self._criar_celula_cabecalho(row3_frame, "Siom:", self.campos_dict["Siom"], tk.Entry, {}, 4, 21, expand=True)

        row4_frame = tk.Frame(frame_campos, bg='white'); row4_frame.grid(row=3, column=0, sticky="ew")
        self._criar_celula_cabecalho(row4_frame, "By-Pass:", self.campos_dict["Bypass"], ttk.Combobox, {'state': 'readonly'}, 6, 10, categoria_db='bypass', tipo_lista='geral')
        self._criar_celula_cabecalho(row4_frame, "Manobra Efetiva:", self.campos_dict["Manobra Efetiva"], AutocompleteCombobox, {}, 14, 5, categoria_db='manobra_efetiva', tipo_lista='geral')
        self._criar_celula_cabecalho(row4_frame, "Vinculado a Acessante:", self.campos_dict["Vinculado a Acessante"], AutocompleteCombobox, {}, 19, 5, categoria_db='vinculado_acessante', tipo_lista='geral')
        self.frame_acessante = self._criar_celula_cabecalho(row4_frame, "Eqpto Acessante:", self.campos_dict["Eqpto Acessante"], tk.Entry, {}, 14, 10, expand=True)

    def _criar_celula_cabecalho(self, parent, label_text, var, widget_class, widget_options, label_width, entry_width, categoria_db=None, tipo_lista=None, nome_widget=None, expand=False):
        frame = tk.Frame(parent, bg='white')
        
        pack_options = {'side': 'left', 'padx': (0,5)}
        if expand:
            pack_options.update({'fill': 'x', 'expand': True})
        else:
            pack_options['fill'] = 'y'
        
        frame.pack(**pack_options)
        
        label = tk.Label(frame, text=label_text, font=FONTE_PADRAO, anchor="w", bg='white', width=label_width, relief="solid", bd=1, padx=5)
        label.pack(side='left', fill='both')

        widget_container = tk.Frame(frame, relief="solid", bd=1)
        
        options = widget_options.copy()
        options['textvariable'] = var
        options['font'] = FONTE_PADRAO

        if issubclass(widget_class, ttk.Combobox):
            widget = widget_class(widget_container, **options)
            widget.bind("<Button-1>", self.open_dropdown_on_click)

            if tipo_lista == 'geral' and categoria_db:
                opcoes = [""] + self._get_opcoes_formatadas_geral(categoria_db)
                if isinstance(widget, AutocompleteCombobox):
                    widget.set_completion_list(opcoes)
                else:
                    widget['values'] = opcoes 
            
            if not isinstance(widget, AutocompleteCombobox):
                if 'state' not in widget_options:
                    widget.config(state='readonly')
            
            if nome_widget:
                self.comboboxes_cabecalho[nome_widget] = widget
            elif categoria_db:
                self.comboboxes_cabecalho[categoria_db] = widget
        else: 
            widget = widget_class(widget_container, **options)
        
        widget.config(width=entry_width)
        widget.pack(fill='x', expand=True)
        widget_container.pack(side='left', fill='both', expand=True)
        return frame

    def atualizar_todas_as_listas(self):
        self.controller.atualizar_listas_memorial(self)
        
        for categoria, combobox in self.comboboxes_cabecalho.items():
            if categoria not in ['fabricante', 'modelo', 'comando', 'cabo_critico_trecho']:
                opcoes = self._get_opcoes_formatadas_geral(categoria)
                if "" not in opcoes:
                    opcoes.insert(0, "")
                if isinstance(combobox, AutocompleteCombobox):
                    combobox.set_completion_list(opcoes)
                else:
                    combobox['values'] = opcoes

        self._carregar_fabricantes()
        self._carregar_cabos()
        
    def _carregar_fabricantes(self):
        combo = self.comboboxes_cabecalho.get('fabricante')
        if not combo: return
        fabricantes = self.controller.get_opcoes_hierarquicas()
        self.fabricantes_map = {f['valor']: f['id'] for f in fabricantes}
        
        lista_fabricantes = [""] + sorted(self.fabricantes_map.keys())
        combo.set_completion_list(lista_fabricantes)
        combo.bind("<<ComboboxSelected>>", self._on_fabricante_select)

    def _carregar_cabos(self):
        combo = self.comboboxes_cabecalho.get('cabo_critico_trecho')
        if not combo: return
        cabos = self.controller.get_todos_cabos()
        self.cabos_map = {c['trecho']: c for c in cabos}
        
        lista_cabos = [""] + sorted(self.cabos_map.keys())
        if isinstance(combo, AutocompleteCombobox):
            combo.set_completion_list(lista_cabos)
        else: 
            combo['values'] = lista_cabos
            
        combo.bind("<<ComboboxSelected>>", self._on_cabo_select)

    def _on_fabricante_select(self, event=None):
        self.campos_dict["Modelo"].set("")
        self.campos_dict["Comando"].set("")
        self.comboboxes_cabecalho['modelo'].set_completion_list([""])
        self.comboboxes_cabecalho['comando'].set_completion_list([""])
        self.modelos_map.clear()
        self.comandos_map.clear()

        fab_selecionado = self.campos_dict["Fabricante"].get()
        if not fab_selecionado: return

        id_pai = self.fabricantes_map.get(fab_selecionado)
        if not id_pai: return
        modelos = self.controller.get_opcoes_hierarquicas(id_pai)
        self.modelos_map = {m['valor']: m['id'] for m in modelos}
        
        combo_modelo = self.comboboxes_cabecalho['modelo']
        combo_modelo.set_completion_list([""] + sorted(self.modelos_map.keys()))
        combo_modelo.bind("<<ComboboxSelected>>", self._on_modelo_select)

    def _on_modelo_select(self, event=None):
        self.campos_dict["Comando"].set("")
        self.comboboxes_cabecalho['comando'].set_completion_list([""])
        self.comandos_map.clear()

        mod_selecionado = self.campos_dict["Modelo"].get()
        if not mod_selecionado: return
        
        id_pai = self.modelos_map.get(mod_selecionado)
        if not id_pai: return
        comandos = self.controller.get_opcoes_hierarquicas(id_pai)
        self.comandos_map = {c['valor']: c['id'] for c in comandos}
        
        combo_comando = self.comboboxes_cabecalho['comando']
        combo_comando.set_completion_list([""] + sorted(self.comandos_map.keys()))

    def _on_cabo_select(self, event=None):
        cabo_selecionado = self.campos_dict["cabo_critico_trecho"].get()
        if not cabo_selecionado:
            self.campos_dict["cabo_critico_nominal"].set("")
            self.campos_dict["cabo_critico_admissivel"].set("")
            return

        propriedades = self.controller.get_propriedades_cabo(cabo_selecionado)
        if propriedades:
            self.campos_dict["cabo_critico_nominal"].set(propriedades.get('nominal', ''))
            self.campos_dict["cabo_critico_admissivel"].set(propriedades.get('admissivel', ''))
            
    def criar_layout_formulario(self):
        self._criar_novas_tabelas_parametros(self.main_form_frame)
        frame_anexos = tk.Frame(self.main_form_frame, bg='white'); frame_anexos.pack(pady=(15, 5), padx=10, anchor='w'); btn_anexos = tk.Button(frame_anexos, text="+", font=("Helvetica", 10, "bold"), relief="solid", bd=1, command=self.abrir_anexos, cursor="hand2"); btn_anexos.pack(side="left", padx=(0, 5)); lbl_anexos = tk.Label(frame_anexos, text="Anexos", font=FONTE_PADRAO, bg='white'); lbl_anexos.pack(side="left")
        
        self.tabela_principal_container = tk.Frame(self.main_form_frame, bg='white')
        self.tabela_principal_container.pack(pady=10, anchor="center")

        self.wrap_tabelas = tk.Frame(self.tabela_principal_container, bg='white')
        self._construir_bloco_tabelas(self.wrap_tabelas, self.vars_grupos, self.tabelas_grupo_frames, self.ref_cells, "original")
        
        self.frame_bloco_tabelas_secc = tk.Frame(self.tabela_principal_container, bg='white')
        self._construir_bloco_tabelas_secc(
            self.frame_bloco_tabelas_secc,
            self.vars_grupos_secc,
            self.tabelas_grupo_frames_secc
        )

        botoes_frame = tk.Frame(self.main_form_frame, bg='white'); botoes_frame.pack(pady=20)
        ttk.Button(botoes_frame, text="Buscar", command=self.abrir_janela_busca).pack(side="left", padx=5)
        ttk.Button(botoes_frame, text="Salvar Rascunho", command=self.salvar_rascunho).pack(side="left", padx=5)
        ttk.Button(botoes_frame, text="Exportar Doc", command=self.exportar_documento).pack(side="left", padx=5)
        ttk.Button(botoes_frame, text="Salvar e Enviar", command=self.salvar_e_enviar).pack(side="left", padx=5)
        ttk.Button(botoes_frame, text="Limpar", command=self.limpar_formulario).pack(side="left", padx=5)
        
        frame_obs = tk.Frame(self.main_form_frame, bg='white'); frame_obs.pack(pady=(10, 5), padx=10, fill='x', expand=False); lbl_obs = tk.Label(frame_obs, text="Observações:", font=FONTE_PADRAO, bg='white'); lbl_obs.pack(anchor='w'); text_container = tk.Frame(frame_obs, height=120, relief="solid", bd=1); text_container.pack(fill='x', expand=False); text_container.pack_propagate(False); self.text_obs = tk.Text(text_container, relief="flat", bd=0, font=FONTE_PADRAO); self.text_obs.pack(fill="both", expand=True)
        
        self.frame_bloco_tabelas_replicado = tk.Frame(self.main_form_frame, bg='white')
        self.frame_bloco_tabelas_replicado.pack(pady=(20, 10), anchor="center")
        self._construir_bloco_tabelas(self.frame_bloco_tabelas_replicado, self.vars_grupos_rep, self.tabelas_grupo_frames_rep, self.ref_cells_rep, "replicado")

    def _criar_novas_tabelas_parametros(self, parent):
        container_principal = tk.Frame(parent, bg='white'); container_principal.pack(pady=(10, 10), padx=10, anchor='w'); coluna_esquerda = tk.Frame(container_principal, bg='white'); coluna_esquerda.grid(row=0, column=0, sticky='new', padx=(0, 10)); coluna_meio = tk.Frame(container_principal, bg='white'); coluna_meio.grid(row=0, column=1, sticky='new', padx=(0, 10)); coluna_direita = tk.Frame(container_principal, bg='white'); coluna_direita.grid(row=0, column=2, sticky='new')
        frame_coordenograma = tk.Frame(coluna_esquerda, bg='white'); frame_coordenograma.pack(anchor='w'); tk.Label(frame_coordenograma, text="Parâmetros do Coordenograma do Cliente", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=0, column=0, columnspan=3, sticky='nsew'); tk.Label(frame_coordenograma, text="", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=1, column=0, sticky='nsew'); tk.Label(frame_coordenograma, text="Consumo", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=1, column=1, sticky='nsew'); tk.Label(frame_coordenograma, text="Injeção", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=1, column=2, sticky='nsew')
        labels_coord = ["Pick-up (A)", "Curva", "Dial", "T. Adic.", "Pot. de Consumo (kW)", "Pot. de Injeção (kW)"]; vars_consumo = ["param_consumo_pickup", "param_consumo_curva", "param_consumo_dial", "param_consumo_t_adic", "param_consumo_pot_kw"]; vars_injecao = ["param_injecao_pickup", "param_injecao_curva", "param_injecao_dial", "param_injecao_t_adic", "param_injecao_pot_kw"]
        for i, label in enumerate(labels_coord[:4]): tk.Label(frame_coordenograma, text=label, font=FONTE_PADRAO, relief="solid", bd=1, anchor='w', width=20).grid(row=i+2, column=0, sticky='nsew'); tk.Entry(frame_coordenograma, textvariable=self.campos_dict[vars_consumo[i]], font=FONTE_PADRAO, justify='center', relief='solid', bd=1, width=8).grid(row=i+2, column=1, sticky='nsew'); tk.Entry(frame_coordenograma, textvariable=self.campos_dict[vars_injecao[i]], font=FONTE_PADRAO, justify='center', relief='solid', bd=1, width=8).grid(row=i+2, column=2, sticky='nsew')
        tk.Label(frame_coordenograma, text=labels_coord[4], font=FONTE_PADRAO, relief="solid", bd=1, anchor='w').grid(row=6, column=0, sticky='nsew'); tk.Entry(frame_coordenograma, textvariable=self.campos_dict[vars_consumo[4]], font=FONTE_PADRAO, justify='center', relief='solid', bd=1).grid(row=6, column=1, columnspan=2, sticky='nsew'); tk.Label(frame_coordenograma, text=labels_coord[5], font=FONTE_PADRAO, relief="solid", bd=1, anchor='w').grid(row=7, column=0, sticky='nsew'); tk.Entry(frame_coordenograma, textvariable=self.campos_dict[vars_injecao[4]], font=FONTE_PADRAO, justify='center', relief='solid', bd=1).grid(row=7, column=1, columnspan=2, sticky='nsew')
        
        f3 = tk.Frame(coluna_meio, bg='white'); f3.pack(anchor='w', pady=(0, 10));
        
        tk.Label(f3, text="Tensão [kV] da rede", font=FONTE_PADRAO, bg='white', relief="solid", bd=1, width=18, anchor='w').grid(row=0, column=0, sticky="nsew")
        combo_tensao = AutocompleteCombobox(f3, textvariable=self.campos_dict["tensao_kv_rede"], font=FONTE_PADRAO, justify="center", width=6)
        opcoes_tensao = [""] + self._get_opcoes_formatadas_geral('tensao_kv_rede')
        combo_tensao.set_completion_list(opcoes_tensao)
        combo_tensao.grid(row=0, column=1, sticky="nsew")
        self.comboboxes_cabecalho['tensao_kv_rede'] = combo_tensao
        combo_tensao.bind("<Button-1>", self.open_dropdown_on_click)

        params_tensao = [("Carga - fase A [A]", self.campos_dict["carga_fase_a"]), ("Carga - fase B [A]", self.campos_dict["carga_fase_b"]), ("Carga - fase C [A]", self.campos_dict["carga_fase_c"])]
        for i, (label, var) in enumerate(params_tensao): 
            tk.Label(f3, text=label, font=FONTE_PADRAO, bg='white', relief="solid", bd=1, width=18, anchor='w').grid(row=i+1, column=0, sticky="nsew")
            tk.Entry(f3, textvariable=var, font=FONTE_PADRAO, justify="center", relief="solid", bd=1, width=8).grid(row=i+1, column=1, sticky="nsew")

        f5 = tk.Frame(coluna_meio, bg='white'); f5.pack(anchor='w', pady=(0, 10)); tk.Label(f5, text="Corrente de Falta", font=FONTE_PADRAO, bg='white', relief="solid", bd=1).grid(row=0, column=0, columnspan=2, sticky='nsew'); params_corrente = [("FASE - CC máximo [A]", self.campos_dict["corrente_falta_fase_cc_max"]), ("FASE - Sensibilidade principal [A]", self.campos_dict["corrente_falta_fase_sens_princ"]), ("TERRA - Sensibilidade principal [A]", self.campos_dict["corrente_falta_terra_sens_princ"])]
        for i, (label, var) in enumerate(params_corrente): tk.Label(f5, text=label, font=FONTE_PADRAO, bg='white', relief="solid", bd=1, width=28, anchor='w').grid(row=i+1, column=0, sticky="nsew"); tk.Entry(f5, textvariable=var, font=FONTE_PADRAO, justify="center", relief="solid", bd=1, width=12).grid(row=i+1, column=1, sticky="nsew")
        frame_montante = tk.Frame(coluna_direita, bg='white'); frame_montante.pack(anchor='w', pady=(0, 10)); tk.Label(frame_montante, text="", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=0, column=0, sticky='nsew'); tk.Label(frame_montante, text="Lado 1\nA montante", font=FONTE_PADRAO, relief="solid", bd=1, wraplength=70, justify="center").grid(row=0, column=1, sticky='nsew'); tk.Label(frame_montante, text="Lado 2", font=FONTE_PADRAO, relief="solid", bd=1).grid(row=0, column=2, sticky='nsew'); labels_montante = ["Número do Equipamento", "Pick-up Fase - G1 (A)", "Pick-up Fase - G2 (A)", "Pick-up Terra - G1 (A)", "Pick-up Terra - G2 (A)"]; vars_montante = ["eqpto_montante_numero", "eqpto_montante_pickup_fase_g1", "eqpto_montante_pickup_fase_g2", "eqpto_montante_pickup_terra_g1", "eqpto_montante_pickup_terra_g2"]
        for i, label in enumerate(labels_montante): row_num = i + 1; tk.Label(frame_montante, text=label, font=FONTE_PADRAO, relief="solid", bd=1, anchor='w', width=20).grid(row=row_num, column=0, sticky='nsew'); tk.Entry(frame_montante, textvariable=self.campos_dict[f"{vars_montante[i]}_l1"], font=FONTE_PADRAO, justify='center', relief='solid', bd=1, width=8).grid(row=row_num, column=1, sticky='nsew'); tk.Entry(frame_montante, textvariable=self.campos_dict[f"{vars_montante[i]}_l2"], font=FONTE_PADRAO, justify='center', relief='solid', bd=1, width=8).grid(row=row_num, column=2, sticky='nsew')
        
        f4 = tk.Frame(coluna_direita, bg='white')
        f4.pack(anchor='w', pady=(0, 10))
        tk.Label(f4, text="Cabo crítico no trecho", font=FONTE_PADRAO, bg='white', relief="solid", bd=1).grid(row=0, column=0, sticky='nsew')
        tk.Label(f4, text="Nominal [A]", font=FONTE_PADRAO, bg='white', relief="solid", bd=1).grid(row=0, column=1, sticky='nsew')
        tk.Label(f4, text="Admissível [A]", font=FONTE_PADRAO, bg='white', relief="solid", bd=1).grid(row=0, column=2, sticky='nsew')
        
        combo_cabo = AutocompleteCombobox(f4, textvariable=self.campos_dict["cabo_critico_trecho"], font=FONTE_PADRAO, justify="center", width=14)
        combo_cabo.grid(row=1, column=0, sticky="nsew")
        self.comboboxes_cabecalho['cabo_critico_trecho'] = combo_cabo
        
        tk.Entry(f4, textvariable=self.campos_dict["cabo_critico_nominal"], font=FONTE_PADRAO, justify="center", relief="solid", bd=1, width=12, state='readonly').grid(row=1, column=1, sticky="nsew")
        tk.Entry(f4, textvariable=self.campos_dict["cabo_critico_admissivel"], font=FONTE_PADRAO, justify="center", relief="solid", bd=1, width=12, state='readonly').grid(row=1, column=2, sticky="nsew")
    
    def _gerenciar_campo_acessante(self, *args):
        if self.campos_dict["Vinculado a Acessante"].get() == "Sim":
            self.frame_acessante.pack(side='left', fill='x', expand=True, padx=(0,5))
        else: 
            self.frame_acessante.pack_forget()
            self.campos_dict["Eqpto Acessante"].set("")
        
    def _construir_bloco_tabelas(self, parent, vars_storage, tables_storage, refs_storage, tipo_bloco):
        for widget in parent.winfo_children():
            widget.destroy()

        widget_list = self.tempo_morto_widgets if tipo_bloco == 'original' else self.tempo_morto_widgets_rep
        widget_list.clear()

        parent.grid_columnconfigure(2, weight=1)
        row_heights = [90, 90, 90, 90, 60]

        textos_header = {
            "original": "Grupo Normal = Grupo de Consumo",
            "replicado": "Grupo Inverso = Grupo de Injeção"
        }
        header = tk.Frame(parent, bd=1, relief="solid", bg='white')
        [header.grid_columnconfigure(c, minsize=w, weight=1) for c, w in enumerate(self.col_widths)]
        [header.grid_rowconfigure(r, minsize=30, weight=1) for r in range(3)]
        self._cell(header, 0, 0, textos_header.get(tipo_bloco, ""), cs=9)
        self._cell(header, 1, 0, "  Grupos  ", rs=2); self._cell(header, 1, 1, "FASE", cs=4); self._cell(header, 1, 5, "TERRA", cs=4); self._cell(header, 2, 1, "  Pickup  "); self._cell(header, 2, 2, "  Sequência  "); self._cell(header, 2, 3, "  Curva Lenta  "); self._cell(header, 2, 4, "  Curva Rápida  "); self._cell(header, 2, 5, "  Pickup  "); self._cell(header, 2, 6, "  Sequência  "); self._cell(header, 2, 7, "  Curva Lenta  "); self._cell(header, 2, 8, "  Curva Rápida  ")
        header.grid(row=0, column=2, pady=5, sticky='ew')
        
        side_cell_1 = self._criar_celula_lateral(parent, row_heights[0], widget_list, is_first_cell=True)
        side_cell_1.grid(row=0, column=1, sticky='ns', padx=(0, 5), pady=5)
        
        tables_storage.clear(); refs_storage.clear(); tables_storage.append(header)
        
        for i in range(1, 4):
            t, r, v = self.criar_tabela_grupo(parent, f"  Grupo {i}  ")
            vars_storage[f'grupo_{i}'] = v; tables_storage.append(t); refs_storage.append(r)
            t.grid(row=i, column=2, pady=(0, 5), sticky='ew')

            tk.Label(parent, text="📎", font=("Helvetica", 12), bg='white').grid(row=i, column=0, sticky='e', padx=(0, 5))
            
            side_cell = self._criar_celula_lateral(parent, row_heights[i], widget_list)
            side_cell.grid(row=i, column=1, sticky='ns', padx=(0, 5), pady=(0,5))

        t4 = self.criar_tabela_grupo4(parent)
        tables_storage.append(t4)
        t4.grid(row=4, column=2, pady=(0, 5), sticky='ew')
        
        side_cell_5 = self._criar_celula_lateral(parent, row_heights[4], widget_list)
        side_cell_5.grid(row=4, column=1, sticky='ns', padx=(0, 5), pady=(0,5))

    def _criar_celula_lateral(self, parent, height, widget_list, is_first_cell=False, is_group_cell=False):
        width = self.col_widths[0] * 2.5
        
        container = tk.Frame(parent, height=height, width=int(width), bg='white')
        container.pack_propagate(False)

        # Add an outer frame to simulate the double border
        outer_frame = tk.Frame(container, bd=1, relief="solid", bg='white')
        outer_frame.pack(fill='both', expand=True)

        cell_frame = tk.Frame(outer_frame, bd=1, relief="solid", bg='white') # Inner frame still has its border
        cell_frame.pack(fill='both', expand=True)

        if is_first_cell:
            lbl = tk.Label(cell_frame, text="Configurações", font=FONTE_PADRAO, bg='white', justify='center', anchor='center')
            lbl.pack(fill='both', expand=True, padx=2, pady=2)
            widget_list.append(lbl) # Append the label to widget_list
        elif is_group_cell:
            # Add the attachment icon
            icon_label = tk.Label(cell_frame, text="+ ", font=("Helvetica", 10, "bold"), bg='white')
            icon_label.pack(side="left", padx=(2, 0))
            
            text_widget = tk.Text(cell_frame, font=FONTE_PEQUENA, relief='flat', wrap=tk.WORD, bd=0, highlightthickness=0)
            text_widget.pack(fill='both', expand=True, padx=(0, 2), pady=2) # Adjust padx for icon
            widget_list.append(text_widget)
        else:
            text_widget = tk.Text(cell_frame, font=FONTE_PEQUENA, relief='flat', wrap=tk.WORD, bd=0, highlightthickness=0)
            text_widget.pack(fill='both', expand=True, padx=2, pady=2)
            widget_list.append(text_widget)
        return container

    def _construir_bloco_tabelas_secc(self, parent, vars_storage, tables_storage):
        for widget in parent.winfo_children():
            widget.destroy()
        
        self.tempo_morto_widgets_secc.clear()
        parent.grid_columnconfigure(1, weight=1)

        row_heights = [90, 90, 90, 90, 60]

        header = tk.Frame(parent, bd=1, relief="solid", bg='white')
        [header.grid_columnconfigure(c, minsize=w, weight=1) for c, w in enumerate(self.col_widths)]
        [header.grid_rowconfigure(r, minsize=30, weight=1) for r in range(3)]
        self._cell(header, 0, 0, "Parâmetros do Seccionalizador", cs=9)
        self._cell(header, 1, 0, "  Grupos  ", rs=2); self._cell(header, 1, 1, "FASE", cs=4); self._cell(header, 1, 5, "TERRA", cs=4); self._cell(header, 2, 1, "  Pickup  "); self._cell(header, 2, 2, "  Sequência  "); self._cell(header, 2, 3, "  Curva Lenta  "); self._cell(header, 2, 4, "  Curva Rápida  "); self._cell(header, 2, 5, "  Pickup  "); self._cell(header, 2, 6, "  Sequência  "); self._cell(header, 2, 7, "  Curva Lenta  "); self._cell(header, 2, 8, "  Curva Rápida  ")
        header.grid(row=0, column=1, pady=5, sticky='ew')
        
        side_cell_1 = self._criar_celula_lateral(parent, row_heights[0], self.tempo_morto_widgets_secc, is_first_cell=True)
        side_cell_1.grid(row=0, column=0, sticky='ns', padx=(0, 5), pady=5)
        
        tables_storage.clear()
        tables_storage.append(header)

        for i in range(1, 4):
            t, v = self.criar_tabela_grupo_secc(parent, f"  Grupo {i}  ")
            vars_storage[f'grupo_{i}'] = v
            tables_storage.append(t)
            t.grid(row=i, column=1, pady=(0, 5), sticky='ew')

            side_cell = self._criar_celula_lateral(parent, row_heights[i], self.tempo_morto_widgets_secc, is_group_cell=True)
            side_cell.grid(row=i, column=0, sticky='ns', padx=(0, 5), pady=(0,5))
        
        t4 = self.criar_tabela_grupo4(parent)
        tables_storage.append(t4)
        t4.grid(row=4, column=1, pady=(0, 5), sticky='ew')

        side_cell_5 = self._criar_celula_lateral(parent, row_heights[4], self.tempo_morto_widgets_secc)
        side_cell_5.grid(row=4, column=0, sticky='ns', padx=(0, 5), pady=(0,5))

    def criar_tabela_grupo4(self, parent):
        f = tk.Frame(parent, bd=1, relief="solid")
        [f.grid_columnconfigure(i, minsize=w, weight=1) for i, w in enumerate(self.col_widths)]
        f.grid_rowconfigure(0, minsize=60, weight=1)
        self._cell(f, 0, 0, "Grupo 4")
        self._cell(f, 0, 1, "630")
        self._cell(f, 0, 2, "1L")
        self._cell(f, 0, 3, "T.Definido", font=FONTE_PEQUENA)

        s4_container = tk.Frame(f, bd=0, bg='white')
        s4_container.grid(row=0, column=4, sticky="nsew")
        s4_container.grid_rowconfigure(0, weight=1)
        s4_container.grid_columnconfigure(0, weight=1)
        s4_container.grid_columnconfigure(1, weight=1)
        tk.Label(s4_container, text="Lenta", font=FONTE_PEQUENA, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=0, sticky="nsew")
        tk.Label(s4_container, text="20", font=FONTE_PEQUENA, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=1, sticky="nsew")

        self._cell(f, 0, 5, "630")
        self._cell(f, 0, 6, "1L")
        self._cell(f, 0, 7, "T.Definido", font=FONTE_PEQUENA)
        
        s8 = tk.Frame(f, bd=0, bg='white')
        s8.grid(row=0, column=8, sticky="nsew")
        s8.grid_columnconfigure(0, weight=1)
        s8.grid_columnconfigure(1, weight=1)
        s8.grid_rowconfigure(0, weight=1)
        tk.Label(s8, text="Lenta", font=FONTE_PEQUENA, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=0, sticky="nsew")
        tk.Label(s8, text="20", font=FONTE_PEQUENA, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=1, sticky="nsew")

        return f
    
    def _set_widgets_state(self, parent, new_state):
        for child in parent.winfo_children():
            widget_class = child.winfo_class()
            try:
                if widget_class in ('TEntry', 'Entry', 'Text'):
                    child.config(state=new_state)
                elif widget_class == 'TCombobox':
                    child.config(state='readonly' if new_state == 'normal' else 'disabled')
                elif widget_class == 'TButton':
                    child.config(state=new_state)
                self._set_widgets_state(child, new_state)
            except tk.TclError:
                self._set_widgets_state(child, new_state)

    def _gerenciar_visibilidade_tabelas(self, *args):
        cond = self.campos_dict["Condição"].get().upper()

        if cond in ["SECC NA", "SECC NF"]:
            self.wrap_tabelas.grid_forget()
            [var.set("") for g in self.vars_grupos.values() for var in g.values()]
            
            self.frame_bloco_tabelas_secc.grid(row=0, column=0, sticky="nsew")
            self._set_widgets_state(self.frame_bloco_tabelas_secc, 'normal')
        else:
            self.frame_bloco_tabelas_secc.grid_forget()
            [var.set("") for g in self.vars_grupos_secc.values() for var in g.values()]
            
            self.wrap_tabelas.grid(row=0, column=0, sticky="nsew")

        new_state = 'normal' if cond in ["ACESS INV", "ACESS S/INV"] else 'disabled'
        self._set_widgets_state(self.frame_bloco_tabelas_replicado, new_state)
        if new_state == 'disabled':
            [var.set("") for g in self.vars_grupos_rep.values() for var in g.values()]
    
    def _toggle_selecionar_tudo_rascunhos(self): [v.set(self.selecionar_tudo_rascunhos_var.get()) for v in self.rascunho_check_vars.values()]
    def _replicar_sequencia_g1_para_g3(self, *args):
        try: self.vars_grupos['grupo_3']['sequencia'].set(self.vars_grupos['grupo_1']['sequencia'].get())
        except KeyError: pass
    def deletar_rascunho_individual(self, eqpto):
        if messagebox.askyesno("Confirmar Exclusão", f"Deseja deletar o rascunho para '{eqpto}'?"): self.controller.deletar_rascunhos(self, [eqpto])
    def deletar_rascunhos_selecionados(self):
        a_deletar = [e for e, v in self.rascunho_check_vars.items() if v.get()]
        if not a_deletar: messagebox.showwarning("Nenhuma Seleção", "Nenhum rascunho selecionado."); return
        if messagebox.askyesno("Confirmar Exclusão", f"Deseja deletar os {len(a_deletar)} rascunhos selecionados?"): self.controller.deletar_rascunhos(self, a_deletar)

    def on_frame_configure(self, event): self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def _on_mouse_wheel(self, event):
        if sys.platform == "win32": self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        else: self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

    def open_dropdown_on_click(self, event):
        widget = event.widget
        widget.after(10, lambda: widget.event_generate('<Down>'))

    def _cell(self, frame, r, c, txt="", rs=1, cs=1, sticky="nsew", font=None):
        outer = tk.Frame(frame, relief="solid", bd=1, bg='white')
        outer.grid(row=r, column=c, rowspan=rs, columnspan=cs, sticky=sticky)
        if txt is not None:
            font_to_use = font if font else FONTE_PADRAO
            lbl = tk.Label(outer, text=txt, font=font_to_use, bg='white', justify='center')
            lbl.pack(fill="both", expand=True)
        return outer

    def _limitar_tamanho(self, P, max_len_str): return len(P) <= int(max_len_str)
    def formatar_siom(self, *args):
        var = self.campos_dict["Siom"]; var.trace_remove("write", var.trace_info()[0][1]); valor = ''.join(filter(str.isdigit, var.get()))[:7]; var.set(f"{valor[:5]}-{valor[5:]}" if len(valor) > 5 else valor); var.trace_add("write", self.formatar_siom)
    def formatar_coord(self, *args):
        var = self.campos_dict["Coord"]; var.trace_remove("write", var.trace_info()[0][1]); valor = ''.join(filter(str.isdigit, var.get()))[:13]; var.set(f"{valor[:6]}:{valor[6:]}" if len(valor) > 6 else valor); var.trace_add("write", self.formatar_coord)
    
    def criar_tabela_grupo(self, parent, group_name):
        group_vars = {k: tk.StringVar() for k in ["pickup_fase", "sequencia", "curva_lenta_tipo", "curva_lenta_dial", "curva_lenta_tadic", "curva_rapida_dial", "curva_rapida_tadic", "pickup_terra", "sequencia_terra", "terra_tempo_lenta", "terra_tempo_rapida"]}; frame_tabela = tk.Frame(parent, bd=1, relief="solid", bg='white'); [frame_tabela.grid_columnconfigure(c, minsize=w, weight=1) for c, w in enumerate(self.col_widths)]; [frame_tabela.grid_rowconfigure(r, minsize=30, weight=1) for r in range(1, 4)]; entry_fase_rapida_dial, entry_fase_rapida_tadic, entry_terra_rapida_tempo = None, None, None
        def _sync_seq(*args): group_vars["sequencia_terra"].set(group_vars["sequencia"].get())
        def _manage_rapida(*args):
            state = 'disabled' if group_vars["sequencia"].get() in ['1L', '2L', '3L'] else 'normal'
            if entry_fase_rapida_dial: entry_fase_rapida_dial.config(state=state)
            if entry_fase_rapida_tadic: entry_fase_rapida_tadic.config(state=state)
            if entry_terra_rapida_tempo: entry_terra_rapida_tempo.config(state=state)
            if state == 'disabled': group_vars["curva_rapida_dial"].set(''); group_vars["curva_rapida_tadic"].set(''); group_vars["terra_tempo_rapida"].set('')
        group_vars["sequencia"].trace_add("write", _sync_seq); group_vars["sequencia"].trace_add("write", _manage_rapida); tk.Label(frame_tabela, text=group_name, relief="solid", bd=1, font=FONTE_PADRAO, bg='white').grid(row=1, column=0, rowspan=3, sticky="nsew"); tk.Label(frame_tabela, text="FASE", relief="solid", bd=1, font=FONTE_PADRAO, bg='white').grid(row=1, column=1, columnspan=2, sticky="nsew"); 
        lenta_fase_cell = tk.Frame(frame_tabela, relief="solid", bd=1, bg='white'); 
        combo_lenta = ttk.Combobox(lenta_fase_cell, textvariable=group_vars["curva_lenta_tipo"], values=["", "IEC Muito Inversa", "IEC Ext. Inversa"], state="readonly", font=FONTE_PEQUENA, justify="center", style='Arrowless.TCombobox', width=18); 
        combo_lenta.bind("<Button-1>", self.open_dropdown_on_click); 
        combo_lenta.pack(fill='both', expand=True); 
        lenta_fase_cell.grid(row=1, column=3, sticky="nsew"); 
        self._cell(frame_tabela, 1, 4, "IEC Inversa"); 
        tk.Label(frame_tabela, text="TERRA", relief="solid", bd=1, font=FONTE_PADRAO, bg='white').grid(row=1, column=5, columnspan=2, sticky="nsew"); 
        tk.Label(frame_tabela, text="T. Definido", relief="solid", bd=1, font=FONTE_PADRAO, bg='white').grid(row=1, column=7, sticky="nsew"); 
        tk.Label(frame_tabela, text="T. Definido", relief="solid", bd=1, font=FONTE_PADRAO, bg='white').grid(row=1, column=8, sticky="nsew"); 
        tk.Entry(frame_tabela, textvariable=group_vars["pickup_fase"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=1, column=1, rowspan=3, sticky="nsew"); 
        cell_seq = tk.Frame(frame_tabela, relief="solid", bd=1, bg='white'); cell_seq.grid_propagate(False); cell_seq.grid(row=1, column=2, rowspan=3, sticky="nsew"); 
        combo_seq = ttk.Combobox(cell_seq, textvariable=group_vars["sequencia"], values=["", "1L", "2L", "3L", "1R+3L", "1R+2L", "2R+2L"], state="readonly", font=FONTE_PADRAO, justify="center", width=8, style='Arrowless.TCombobox'); combo_seq.bind("<Button-1>", self.open_dropdown_on_click); combo_seq.pack(fill="both", expand=True); 
        tk.Entry(frame_tabela, textvariable=group_vars["pickup_terra"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=1, column=5, rowspan=3, sticky="nsew"); 
        cell_seq_terra = tk.Frame(frame_tabela, relief="solid", bd=1, bg='white'); cell_seq_terra.grid_propagate(False); cell_seq_terra.grid(row=1, column=6, rowspan=3, sticky="nsew"); 
        tk.Label(cell_seq_terra, textvariable=group_vars["sequencia_terra"], font=FONTE_PADRAO, justify="center", bg='white').pack(fill="both", expand=True); 
        sub_lenta = tk.Frame(frame_tabela, bd=0, bg='white'); sub_lenta.grid_propagate(False); sub_lenta.grid(row=2, column=3, rowspan=2, sticky="nsew"); [sub_lenta.grid_rowconfigure(r, weight=1) for r in range(2)]; [sub_lenta.grid_columnconfigure(c, weight=1) for c in range(2)]; 
        tk.Label(sub_lenta, text="Dial", font=FONTE_PADRAO, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=0, sticky="nsew"); 
        tk.Label(sub_lenta, text="T. Adic.", font=FONTE_PADRAO, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=1, sticky="nsew"); 
        tk.Entry(sub_lenta, textvariable=group_vars["curva_lenta_dial"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=1, column=0, sticky="nsew"); 
        tk.Entry(sub_lenta, textvariable=group_vars["curva_lenta_tadic"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=1, column=1, sticky="nsew"); 
        sub_rapida = tk.Frame(frame_tabela, bd=0, bg='white'); sub_rapida.grid_propagate(False); sub_rapida.grid(row=2, column=4, rowspan=2, sticky="nsew"); [sub_rapida.grid_rowconfigure(r, weight=1) for r in range(2)]; [sub_rapida.grid_columnconfigure(c, weight=1) for c in range(2)]; 
        tk.Label(sub_rapida, text="Dial", font=FONTE_PADRAO, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=0, sticky="nsew"); 
        tk.Label(sub_rapida, text="T. Adic.", font=FONTE_PADRAO, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=1, sticky="nsew"); 
        entry_fase_rapida_dial = tk.Entry(sub_rapida, textvariable=group_vars["curva_rapida_dial"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_fase_rapida_dial.grid(row=1, column=0, sticky="nsew"); 
        entry_fase_rapida_tadic = tk.Entry(sub_rapida, textvariable=group_vars["curva_rapida_tadic"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_fase_rapida_tadic.grid(row=1, column=1, sticky="nsew"); 
        self._cell(frame_tabela, 2, 7, "Tempo (s)"); self._cell(frame_tabela, 2, 8, "Tempo (s)"); 
        tk.Entry(frame_tabela, textvariable=group_vars["terra_tempo_lenta"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=3, column=7, sticky="nsew"); 
        entry_terra_rapida_tempo = tk.Entry(frame_tabela, textvariable=group_vars["terra_tempo_rapida"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")); entry_terra_rapida_tempo.grid(row=3, column=8, sticky="nsew"); 
        
        return frame_tabela, lenta_fase_cell, group_vars
    
    def criar_tabela_grupo_secc(self, parent, group_name):
        group_vars = {k: tk.StringVar() for k in ["pickup_fase", "sequencia", "pickup_terra", "sequencia_terra"]}
        frame_tabela = tk.Frame(parent, bd=1, relief="solid", bg='white'); [frame_tabela.grid_columnconfigure(c, minsize=w, weight=1) for c, w in enumerate(self.col_widths)]; [frame_tabela.grid_rowconfigure(r, minsize=30, weight=1) for r in range(3)]
        
        def _sync_seq(*args):
            group_vars["sequencia_terra"].set(group_vars["sequencia"].get())
        group_vars["sequencia"].trace_add("write", _sync_seq)

        self._cell(frame_tabela, 0, 0, group_name, rs=3)
        tk.Entry(frame_tabela, textvariable=group_vars["pickup_fase"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=0, column=1, rowspan=3, sticky="nsew")
        
        cell_seq = tk.Frame(frame_tabela, relief="solid", bd=1, bg='white'); cell_seq.grid_propagate(False); cell_seq.grid(row=0, column=2, rowspan=3, sticky="nsew")
        combo_seq = ttk.Combobox(cell_seq, textvariable=group_vars["sequencia"], values=["", "1L", "2L", "3L"], state="readonly", font=FONTE_PADRAO, justify="center", width=8, style='Arrowless.TCombobox'); combo_seq.bind("<Button-1>", self.open_dropdown_on_click); combo_seq.pack(fill="both", expand=True)

        self._cell(frame_tabela, 0, 3, "SECCIONALIZADOR", font=FONTE_MUITO_PEQUENA)
        sub_lenta = tk.Frame(frame_tabela, bd=0, bg='white'); sub_lenta.grid_propagate(False); sub_lenta.grid(row=1, column=3, rowspan=2, sticky="nsew"); [sub_lenta.grid_rowconfigure(r, weight=1) for r in range(2)]; [sub_lenta.grid_columnconfigure(c, weight=1) for c in range(2)] 
        tk.Label(sub_lenta, text="Dial", font=FONTE_PADRAO, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=0, sticky="nsew")
        tk.Label(sub_lenta, text="T. Adic.", font=FONTE_PADRAO, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=1, sticky="nsew")
        self._cell(sub_lenta, 1, 0, ""); self._cell(sub_lenta, 1, 1, "")

        self._cell(frame_tabela, 0, 4, "")
        sub_rapida = tk.Frame(frame_tabela, bd=0, bg='white'); sub_rapida.grid_propagate(False); sub_rapida.grid(row=1, column=4, rowspan=2, sticky="nsew"); [sub_rapida.grid_rowconfigure(r, weight=1) for r in range(2)]; [sub_rapida.grid_columnconfigure(c, weight=1) for c in range(2)]
        tk.Label(sub_rapida, text="Dial", font=FONTE_PADRAO, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=0, sticky="nsew")
        tk.Label(sub_rapida, text="T. Adic.", font=FONTE_PADRAO, width=6, relief="solid", bd=1, bg='white').grid(row=0, column=1, sticky="nsew")
        self._cell(sub_rapida, 1, 0, ""); self._cell(sub_rapida, 1, 1, "")

        tk.Entry(frame_tabela, textvariable=group_vars["pickup_terra"], font=FONTE_PADRAO, width=4, relief="solid", bd=1, justify="center", validate="key", validatecommand=(self.vcmd_4, "%P")).grid(row=0, column=5, rowspan=3, sticky="nsew")

        cell_seq_terra = tk.Frame(frame_tabela, relief="solid", bd=1, bg='white'); cell_seq_terra.grid_propagate(False); cell_seq_terra.grid(row=0, column=6, rowspan=3, sticky="nsew")
        tk.Label(cell_seq_terra, textvariable=group_vars["sequencia_terra"], font=FONTE_PADRAO, justify="center", bg='white').pack(fill="both", expand=True)
        
        self._cell(frame_tabela, 0, 7, "SECCIONALIZADOR", font=FONTE_MUITO_PEQUENA)
        self._cell(frame_tabela, 1, 7, "Tempo (s)"); self._cell(frame_tabela, 2, 7, "")

        self._cell(frame_tabela, 0, 8, ""); self._cell(frame_tabela, 1, 8, "Tempo (s)"); self._cell(frame_tabela, 2, 8, "")
        
        return frame_tabela, group_vars
        
    def _get_form_data(self):
        data = {k.lower().replace(" ", "_"): v.get() for k, v in self.campos_dict.items()}
        
        for i, widget in enumerate(self.tempo_morto_widgets, 1):
            data[f'tempo_morto_v{i}'] = widget.get("1.0", "end-1c").strip()
        
        # Os dados das tabelas laterais replicadas não são salvos,
        # pois não existem colunas correspondentes no banco de dados.

        for i in range(1, 4):
            if f'grupo_{i}' in self.vars_grupos: data.update({f'g{i}_{vn}': v.get() for vn, v in self.vars_grupos[f'grupo_{i}'].items()})
        if self.campos_dict["Condição"].get().upper() in ["ACESS INV", "ACESS S/INV"]:
            for i in range(1, 4):
                if f'grupo_{i}' in self.vars_grupos_rep: data.update({f'g{i}_{vn}_rep': v.get() for vn, v in self.vars_grupos_rep[f'grupo_{i}'].items()})
        if self.campos_dict["Condição"].get().upper() in ["SECC NA", "SECC NF"]:
            for i in range(1, 4):
                if f'grupo_{i}' in self.vars_grupos_secc:
                    data.update({f'g{i}_{vn}_secc': v.get() for vn, v in self.vars_grupos_secc[f'grupo_{i}'].items()})
        data['observacoes'] = self.text_obs.get("1.0", "end-1c"); data['anexos'] = json.dumps(self.anexos_list); return data

    def salvar_rascunho(self):
        data = self._get_form_data()
        if not data.get("eqpto", "").strip(): messagebox.showwarning("Campo Obrigatório", "O campo 'Eqpto' é obrigatório.", parent=self.parent_window); return
        self.controller.salvar_rascunho(self, data)

    def exportar_documento(self):
        try:
            maps = self.controller.get_all_map_names()
            if not maps:
                messagebox.showerror("Erro", "Nenhum mapa de exportação foi configurado no Módulo de Gestão.", parent=self.parent_window)
                return
            
            dialog = MapSelectDialog(self.parent_window, "Selecionar Mapa de Exportação", maps, controller=self.controller)
            if dialog.result:
                map_id = dialog.result
                self.controller.export_to_excel(self, map_id)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao iniciar a exportação:\n{e}\n\nDetalhes:\n{error_details}", parent=self.parent_window)

    def salvar_e_enviar(self):
        data = self._get_form_data()
        if not data.get("eqpto", "").strip(): messagebox.showwarning("Campo Obrigatório", "O campo 'Eqpto' é obrigatório.", parent=self.parent_window); return
        self.controller.salvar_e_enviar(self, data)
        
    def reconstruir_lista_ajustes(self, *args):
        [w.destroy() for w in self.ajustes_items_frame.winfo_children()]
        termo = self.busca_ajustes_var.get().lower()
        filtrados = [a for a in self.lista_ajustes_completa if a.get('eqpto') and termo in a['eqpto'].lower()]
        
        for i, item in enumerate(filtrados):
            eqpto = item.get('eqpto', '')
            
            status = item.get('status', 'Pendente')
            cor_led = 'grey'
            if status == 'Andamento': cor_led = '#f0ad4e'
            elif status == 'Aprovado': cor_led = '#5cb85c'
            elif status == 'Reprovado': cor_led = '#d9534f'
            
            led = tk.Label(self.ajustes_items_frame, text="●", font=("Helvetica", 12), fg=cor_led, bg='white')
            led.grid(row=i, column=0, sticky='w', padx=(2,0))
            
            lbl_eqpto = tk.Label(self.ajustes_items_frame, text=eqpto, width=7, anchor='w', bg='white', padx=4, font=FONTE_PEQUENA)
            lbl_eqpto.grid(row=i, column=1, sticky='w')

            btn_dir = tk.Button(self.ajustes_items_frame, text="📁", font=FONTE_PEQUENA, relief="flat", bg="white", cursor="hand2")
            btn_dir.grid(row=i, column=2, sticky='w', padx=2)

            btn_obs = ttk.Button(self.ajustes_items_frame, text="Obs", width=4, style="Toolbutton", command=lambda e=eqpto: self._abrir_janela_obs(e))
            btn_obs.grid(row=i, column=3, sticky='w', padx=2)

            data_str = item.get('data_registro', '')
            data_formatada = ""
            if data_str:
                try:
                    data_formatada = datetime.strptime(data_str.split('.')[0], '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
                except (ValueError, TypeError):
                    data_formatada = "Data Inválida"
            if not data_formatada:
                data_formatada = item.get('data', 'N/A')

            tk.Label(self.ajustes_items_frame, text=item.get('alimentador', ''), width=8, anchor='w', bg='white', padx=5, font=FONTE_PEQUENA).grid(row=i, column=4, sticky='w')
            tk.Label(self.ajustes_items_frame, text=f"NS: {item.get('ns','')}", width=12, anchor='w', bg='white', padx=5, font=FONTE_PEQUENA).grid(row=i, column=5, sticky='w')
            tk.Label(self.ajustes_items_frame, text=data_formatada, width=10, anchor='w', bg='white', padx=5, font=FONTE_PEQUENA).grid(row=i, column=6, sticky='w')

            for child in [led, lbl_eqpto]:
                child.bind("<Double-1>", lambda e, eq=eqpto: self.carregar_ajuste_pelo_nome(eq))
        
        self.ajustes_canvas.yview_moveto(0)

    def reconstruir_lista_rascunhos(self, *args):
        [w.destroy() for w in self.rascunhos_items_frame.winfo_children()]
        self.rascunho_check_vars.clear()
        termo = self.busca_rascunhos_var.get().lower()
        filtrados = [r for r in self.lista_rascunhos_completa if r.get('eqpto') and termo in r['eqpto'].lower()]
        
        for i, item in enumerate(filtrados):
            eqpto = item.get('eqpto')
            var = tk.BooleanVar()
            self.rascunho_check_vars[eqpto] = var
            
            check = ttk.Checkbutton(self.rascunhos_items_frame, variable=var)
            check.grid(row=i, column=0, sticky='w')
            
            lbl_eqpto = tk.Label(self.rascunhos_items_frame, text=eqpto, width=7, anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_eqpto.grid(row=i, column=1, sticky='w', padx=(5, 0))
            
            lbl_alim = tk.Label(self.rascunhos_items_frame, text=item.get('alimentador', ''), width=8, anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_alim.grid(row=i, column=2, sticky='w', padx=5)
            
            lbl_ns = tk.Label(self.rascunhos_items_frame, text=f"NS: {item.get('ns','')}", width=12, anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_ns.grid(row=i, column=3, sticky='w', padx=5)

            data_str = item.get('data', '')
            data_formatada = ""
            if data_str:
                try:
                    data_obj = datetime.strptime(data_str, '%d/%m/%Y')
                    data_formatada = data_obj.strftime('%d/%m/%Y')
                except ValueError:
                    try:
                        data_obj = datetime.strptime(data_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                        data_formatada = data_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        data_formatada = "Data Inválida"
            
            lbl_data = tk.Label(self.rascunhos_items_frame, text=data_formatada, width=10, anchor='w', bg='white', font=FONTE_PEQUENA)
            lbl_data.grid(row=i, column=4, sticky='w', padx=5)
            
            btn_del = tk.Button(self.rascunhos_items_frame, text="X", fg="red", relief="flat", cursor="hand2", font=("Helvetica", 8, "bold"), command=lambda e=eqpto: self.deletar_rascunho_individual(e), bg='white')
            btn_del.grid(row=i, column=5, sticky='e', padx=(0,5))
            
            self.rascunhos_items_frame.grid_columnconfigure(5, weight=1)

            for lbl in [lbl_eqpto, lbl_alim, lbl_ns, lbl_data]:
                lbl.bind("<Double-1>", lambda e, eq=eqpto: self.carregar_rascunho_pelo_nome(eq))
                
        self.selecionar_tudo_rascunhos_var.set(False)
        self.rascunhos_canvas.yview_moveto(0)
        
    def _abrir_janela_obs(self, eqpto):
        autor_atual = self.campos_dict["Autor"].get()
        ObsWindow(self.parent_window, self.controller, eqpto, autor_atual)

    def carregar_ajuste_pelo_nome(self, eqpto): self.controller.carregar_ficha_pelo_nome(self, eqpto, 'cadastros')
    def carregar_rascunho_pelo_nome(self, eqpto): self.controller.carregar_ficha_pelo_nome(self, eqpto, 'rascunhos')
    
    def preencher_formulario(self, dados_dict):
        self.limpar_formulario()

        for nome, var in self.campos_dict.items():
            valor = dados_dict.get(nome.lower().replace(" ", "_"))
            var.set(valor if valor is not None else "")
        
        for i, widget in enumerate(self.tempo_morto_widgets, 1):
            valor = dados_dict.get(f"tempo_morto_v{i}")
            if valor is not None:
                widget.insert("1.0", valor)

        for i in range(1, 4):
            if f'grupo_{i}' in self.vars_grupos:
                for k, v in self.vars_grupos[f'grupo_{i}'].items():
                    valor = dados_dict.get(f"g{i}_{k}")
                    v.set(valor if valor is not None else "")

        for i in range(1, 4):
            if f'grupo_{i}' in self.vars_grupos_rep:
                for k, v in self.vars_grupos_rep[f'grupo_{i}'].items():
                    valor = dados_dict.get(f"g{i}_{k}_rep")
                    v.set(valor if valor is not None else "")

        for i in range(1, 4):
            if f'grupo_{i}' in self.vars_grupos_secc:
                for k, v in self.vars_grupos_secc[f'grupo_{i}'].items():
                    valor = dados_dict.get(f"g{i}_{k}_secc")
                    v.set(valor if valor is not None else "")

        obs_text = dados_dict.get("observacoes")
        self.text_obs.insert("1.0", obs_text if obs_text is not None else "")

        anexos_json = dados_dict.get("anexos", "[]")
        try:
            self.anexos_list = json.loads(anexos_json if anexos_json else "[]")
        except json.JSONDecodeError:
            self.anexos_list = []

    def abrir_janela_busca(self):
        dialog = BuscaDialog(self.parent_window, self.controller)
        if dialog.selected_id:
            self.controller.carregar_ficha_pelo_nome(self, dialog.selected_id, 'cadastros', by_id=True)
            
    def abrir_anexos(self):
        win = tk.Toplevel(self.parent_window); win.title("Gerenciar Anexos"); win.geometry("500x350"); win.transient(self.parent_window); win.grab_set(); win.configure(bg='white')
        self.controller.center_window(win)
        ctrl_frame = tk.Frame(win, bg='white'); ctrl_frame.pack(pady=10, padx=10, fill='x'); add_frame = tk.Frame(ctrl_frame, bg='white'); add_frame.pack(side='left', padx=(0, 20)); tk.Button(add_frame, text="+", font=("Helvetica", 10, "bold"), relief="solid", bd=1, cursor="hand2", command=lambda: self.adicionar_arquivo(win)).pack(side='left', padx=(0, 5)); tk.Label(add_frame, text="Adicionar", font=FONTE_PADRAO, bg='white').pack(side='left'); rem_frame = tk.Frame(ctrl_frame, bg='white'); rem_frame.pack(side='left'); tk.Button(rem_frame, text="-", font=("Helvetica", 10, "bold"), relief="solid", bd=1, cursor="hand2", command=lambda: self.remover_arquivo(win)).pack(side='left', padx=(0, 5)); tk.Label(rem_frame, text="Remover", font=FONTE_PADRAO, bg='white').pack(side='left')
        list_frame = tk.Frame(win, bg='white'); list_frame.pack(pady=10, padx=10, fill='both', expand=True); scrollbar = ttk.Scrollbar(list_frame); scrollbar.pack(side='right', fill='y'); listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, selectmode=tk.EXTENDED, font=FONTE_PEQUENA); listbox.pack(side='left', fill='both', expand=True); scrollbar.config(command=listbox.yview)
        for anexo in self.anexos_list: listbox.insert(tk.END, os.path.basename(anexo))
        win.listbox = listbox
    def adicionar_arquivo(self, window):
        paths = filedialog.askopenfilenames(title="Selecionar arquivos", parent=window)
        if paths:
            for p in paths:
                if p not in self.anexos_list:
                    self.anexos_list.append(p)
                    window.listbox.insert(tk.END, os.path.basename(p))
    def remover_arquivo(self, window):
        indices = window.listbox.curselection()
        if not indices: messagebox.showwarning("Nenhuma Seleção", "Selecione arquivos para remover.", parent=window); return
        for i in sorted(indices, reverse=True): self.anexos_list.pop(i); window.listbox.delete(i)
    def limpar_formulario(self):
        for var in self.campos_dict.values(): var.set("")
        for widget in self.tempo_morto_widgets: widget.delete("1.0", "end")
        for widget in self.tempo_morto_widgets_rep: widget.delete("1.0", "end")
        for widget in self.tempo_morto_widgets_secc: widget.delete("1.0", "end")
        self.campos_dict["Data"].set(datetime.now().strftime('%d/%m/%Y'))
        for g in self.vars_grupos.values(): [v.set("") for v in g.values()]
        for g in self.vars_grupos_rep.values(): [v.set("") for v in g.values()]
        for g in self.vars_grupos_secc.values(): [v.set("") for v in g.values()]
        self.text_obs.delete("1.0", "end"); self.anexos_list.clear()
