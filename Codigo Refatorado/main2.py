import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import tempfile
import atexit

try:
    import psutil
except ImportError:
    messagebox.showerror(
        "Biblioteca Faltando",
        "A biblioteca 'psutil' é necessária para o funcionamento do app.\n\n"
        "Por favor, instale-a abrindo o terminal e digitando:\n"
        "pip install psutil"
    )
    sys.exit(1)

# Importa os módulos do aplicativo
from model import DatabaseModel
from memorial_frame import MemorialCalculoFrame
from visualizacao_frame import VisualizacaoFrame
from ajustes_frame import AjustesFrame
from gestao_frame import GestaoFrame

# --- LÓGICA DE SINGLE INSTANCE ---
lock_file_path = os.path.join(tempfile.gettempdir(), 'central_eventos.lock')
current_script_path = os.path.abspath(sys.argv[0])

def is_process_running(pid):
    """Verifica se o processo com o PID e o nome do script correspondem ao aplicativo."""
    if pid is None: return False
    try:
        process = psutil.Process(pid)
        if any(current_script_path in arg for arg in process.cmdline()):
            return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False
    return False

def remover_lock_file():
    """Remove o arquivo de lock de forma segura."""
    try:
        if os.path.exists(lock_file_path): os.remove(lock_file_path)
    except OSError as e:
        print(f"Não foi possível remover o arquivo de lock: {e}")

if os.path.exists(lock_file_path):
    old_pid = None
    try:
        with open(lock_file_path, 'r') as f:
            content = f.read().strip()
            if content: old_pid = int(content)
    except (IOError, ValueError): old_pid = None

    if is_process_running(old_pid):
        messagebox.showerror("Aplicação já em execução", "A Central de Eventos já está aberta.")
        sys.exit(1)
    else:
        remover_lock_file()

try:
    with open(lock_file_path, 'w') as f: f.write(str(os.getpid()))
    atexit.register(remover_lock_file)
except IOError:
    messagebox.showerror("Erro de Permissão", "Não foi possível criar o arquivo de lock.")
    sys.exit(1)

# === CONFIGURAÇÕES GLOBAIS ===
FONTE_TITULO = ("Helvetica", 22, "bold")
FONTE_BOTAO_MENU = ("Helvetica", 14)
CAMINHO_BD = r'C:\BD_APP_Cemig\Primeiro_banco.db'

# =========================================================================================
# === CLASSE PRINCIPAL (CONTROLLER) ===
# =========================================================================================
class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        self.model = DatabaseModel(CAMINHO_BD)
        
        colunas_memorial = MemorialCalculoFrame.get_db_columns()
        self.model.create_tables(colunas_memorial)

        self.ajustes_window = None 
        self.title("Central de Eventos")
        self.geometry("1100x600") 
        self.minsize(1000, 400)

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        menu_frame = MenuFrame(parent=container, controller=self)
        self.frames[MenuFrame.__name__] = menu_frame
        menu_frame.grid(row=0, column=0, sticky="nsew")
        menu_frame.tkraise()

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def abrir_modulo_memorial(self):
        memorial_window = tk.Toplevel(self)
        memorial_window.title("Memorial de Cálculo")
        memorial_window.geometry("1800x950")
        memorial_frame = MemorialCalculoFrame(parent=memorial_window, controller=self)
        memorial_frame.pack(side="top", fill="both", expand=True)

    def abrir_modulo_visualizacao(self):
        visualizacao_window = tk.Toplevel(self)
        visualizacao_window.title("Visualização de Dados")
        visualizacao_window.geometry("1200x700")
        visualizacao_frame = VisualizacaoFrame(parent=visualizacao_window, controller=self)
        visualizacao_frame.pack(side="top", fill="both", expand=True)

    def abrir_modulo_ajustes(self):
        if self.ajustes_window is not None and self.ajustes_window.winfo_exists():
            messagebox.showinfo("Janela já aberta", "A janela de Ajustes já está em uso.", parent=self)
            self.ajustes_window.lift()
            return
        ajustes_window = tk.Toplevel(self)
        ajustes_window.title("Ajustes Pendentes")
        ajustes_window.geometry("1600x600")
        
        ajustes_window.resizable(True, True)
        
        ajustes_frame = AjustesFrame(parent=ajustes_window, controller=self)
        ajustes_frame.pack(side="top", fill="both", expand=True)
        self.ajustes_window = ajustes_window
        self.ajustes_window.protocol("WM_DELETE_WINDOW", self.on_ajustes_close)

    def on_ajustes_close(self):
        if self.ajustes_window:
            self.ajustes_window.destroy()
        self.ajustes_window = None

    def abrir_modulo_gestao(self):
        gestao_window = tk.Toplevel(self)
        gestao_window.title("Gestão de Opções")
        gestao_window.geometry("600x450") # Aumentei a altura para o novo botão
        gestao_window.transient(self)
        gestao_window.grab_set()
        gestao_frame = GestaoFrame(parent=gestao_window, controller=self)
        gestao_frame.pack(side="top", fill="both", expand=True)

    # =========================================================================================
    # === MÉTODOS DO CONTROLLER ===
    # =========================================================================================
    def salvar_rascunho(self, view, form_data):
        self.model.save_draft(form_data)
        messagebox.showinfo("Sucesso", "Rascunho salvo/atualizado com sucesso!", parent=view.parent_window)
        self.atualizar_listas_memorial(view)

    def salvar_e_enviar(self, view, form_data):
        self.model.save_final_and_manage_lists(form_data)
        messagebox.showinfo("Sucesso", "Ficha salva e enviada com sucesso!", parent=view.parent_window)
        view.limpar_formulario()
        self.atualizar_listas_memorial(view)
        
    def atualizar_listas_memorial(self, view):
        view.lista_ajustes_completa = self.model.get_recent_equipments() or []
        view.lista_rascunhos_completa = self.model.get_all_draft_equipments() or []
        view.reconstruir_lista_ajustes()
        view.reconstruir_lista_rascunhos()

    def carregar_ficha_pelo_nome(self, view, eqpto, tabela):
        id_result = self.model.get_latest_id_for_equipment(eqpto, tabela)
        if id_result:
            record_data = self.model.get_record_by_id(id_result['id'], tabela)
            if record_data:
                view.preencher_formulario(dict(record_data))

    def deletar_rascunhos(self, view, eqpto_list):
        self.model.delete_drafts(eqpto_list)
        messagebox.showinfo("Sucesso", f"{len(eqpto_list)} rascunhos foram deletados.", parent=view.parent_window)
        self.atualizar_listas_memorial(view)

    def carregar_ajustes_pendentes(self):
        ajustes = self.model.get_pending_adjustments()
        return [dict(row) for row in ajustes] if ajustes else []

    def concluir_ajuste(self, eqpto, status):
        self.model.complete_adjustment(eqpto, status)

    def carregar_observacao(self, eqpto):
        obs = self.model.get_observation(eqpto)
        return obs['observacao'] if obs and obs['observacao'] else ""

    def salvar_observacao(self, eqpto, texto):
        self.model.update_observation(eqpto, texto)

    def buscar_registros(self, filtros):
        resultados = self.model.search_records(filtros)
        return [dict(row) for row in resultados] if resultados else []

    def get_record_by_id(self, record_id, table_name='cadastros'):
        data = self.model.get_record_by_id(record_id, table_name)
        return dict(data) if data else None
        
    def update_ajuste_status(self, eqpto_list, status):
        self.model.update_adjustment_status(eqpto_list, status)

    def get_historico_ajustes(self):
        historico = self.model.get_adjustments_history()
        return [dict(row) for row in historico] if historico else []

    # --- Métodos para o Módulo de Gestão (pass-through) ---
    def get_categorias(self):
        return self.model.get_categorias()

    def get_opcoes_por_categoria(self, categoria):
        return self.model.get_opcoes_por_categoria(categoria)

    def adicionar_opcao(self, categoria, valor):
        self.model.adicionar_opcao(categoria, valor)

    def editar_opcao(self, id_opcao, novo_valor):
        self.model.editar_opcao(id_opcao, novo_valor)

    def deletar_opcao(self, id_opcao):
        self.model.deletar_opcao(id_opcao)
        
    def deletar_opcoes_por_categoria(self, categoria):
        self.model.deletar_opcoes_por_categoria(categoria)
        
# =========================================================================================
# === TELA 1: MENU PRINCIPAL (View) ===
# =========================================================================================
class MenuFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg="#f0f0f0")
        title_frame = tk.Frame(self, bg="#e0e0e0", relief="raised", bd=2)
        title_frame.pack(side="top", fill="x")
        lbl_title = tk.Label(title_frame, text="CENTRAL DE EVENTOS", font=FONTE_TITULO, bg="#e0e0e0", fg="#2a753a", pady=20)
        lbl_title.pack()
        buttons_frame = tk.Frame(self, bg="#f0f0f0")
        buttons_frame.pack(expand=True)
        style = ttk.Style()
        style.configure("Menu.TButton", font=FONTE_BOTAO_MENU, padding=20)
        ttk.Button(buttons_frame, text="Visualização", style="Menu.TButton", command=self.controller.abrir_modulo_visualizacao).grid(row=0, column=0, padx=20, pady=20)
        ttk.Button(buttons_frame, text="Memorial de Cálculo", style="Menu.TButton", command=self.controller.abrir_modulo_memorial).grid(row=0, column=1, padx=20, pady=20)
        ttk.Button(buttons_frame, text="Ajustes", style="Menu.TButton", command=self.controller.abrir_modulo_ajustes).grid(row=0, column=2, padx=20, pady=20)
        ttk.Button(buttons_frame, text="Gestão", style="Menu.TButton", command=self.controller.abrir_modulo_gestao).grid(row=0, column=3, padx=20, pady=20)

if __name__ == "__main__":
    app = App()
    app.mainloop()
