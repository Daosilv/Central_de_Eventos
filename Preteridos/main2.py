import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import tempfile
import atexit

# Tenta importar a biblioteca psutil e dá uma instrução clara se não for encontrada
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


# É importante importar as classes dos seus módulos
from memorial_frame import MemorialCalculoFrame
from visualizacao_frame import VisualizacaoFrame
from ajustes_frame import AjustesFrame


# --- LÓGICA APRIMORADA PARA SINGLE INSTANCE ---
lock_file_path = os.path.join(tempfile.gettempdir(), 'central_eventos.lock')

def is_process_running(pid):
    """Verifica se um processo com o dado PID está em execução."""
    if pid is None:
        return False
    return psutil.pid_exists(pid)

def remover_lock_file():
    """Função para remover o arquivo de lock ao fechar o app."""
    try:
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)
    except OSError:
        pass # Não se preocupe se o arquivo não puder ser removido

# Lógica principal de verificação
if os.path.exists(lock_file_path):
    old_pid = None
    try:
        with open(lock_file_path, 'r') as f:
            content = f.read().strip()
            if content:
                old_pid = int(content)
    except (IOError, ValueError):
        old_pid = None

    if is_process_running(old_pid):
        messagebox.showerror("Aplicação já em execução", "A Central de Eventos já está aberta.")
        sys.exit(1)

# Se chegou aqui, ou o arquivo não existia ou o PID era de um processo morto.
# Então, criamos/sobrescrevemos o arquivo de lock com o PID do processo atual.
try:
    with open(lock_file_path, 'w') as f:
        f.write(str(os.getpid()))
    atexit.register(remover_lock_file)
except IOError:
    messagebox.showerror("Erro de Permissão", "Não foi possível criar o arquivo de lock. Verifique as permissões do diretório temporário.")
    sys.exit(1)
# --- FIM DO BLOCO SINGLE INSTANCE ---


# === CONFIGURAÇÕES GLOBAIS ===
FONTE_TITULO = ("Helvetica", 22, "bold")
FONTE_BOTAO_MENU = ("Helvetica", 14)

# =========================================================================================
# === CLASSE PRINCIPAL DA APLICAÇÃO (GERENCIADOR DE TELAS) ===
# =========================================================================================
class App(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.ajustes_window = None 

        self.title("Central de Eventos")
        self.geometry("800x600")
        self.minsize(600, 400)

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

    def show_login_popup(self, target_module_name):
        login_window = tk.Toplevel(self)
        login_window.title("Autenticação Necessária")
        login_window.geometry("350x200")
        login_window.resizable(False, False)
        login_window.transient(self)
        login_window.grab_set()

        x = self.winfo_x() + (self.winfo_width() / 2) - (350 / 2)
        y = self.winfo_y() + (self.winfo_height() / 2) - (200 / 2)
        login_window.geometry(f"+{int(x)}+{int(y)}")

        main_frame = tk.Frame(login_window, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="Usuário:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(main_frame).grid(row=0, column=1, sticky="ew")
        tk.Label(main_frame, text="Senha:").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(main_frame, show="*").grid(row=1, column=1, sticky="ew")

        def login_success():
            login_window.destroy()
            if target_module_name == "Memorial de Cálculo":
                self.abrir_modulo_memorial()
            elif target_module_name == "Visualização":
                self.abrir_modulo_visualizacao()
            elif target_module_name == "Ajustes":
                self.abrir_modulo_ajustes()
        
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)
        ttk.Button(button_frame, text="Entrar", command=login_success).pack(side="left", padx=5)

        def show_info(feature_name):
            messagebox.showinfo("Simulação", f"A funcionalidade '{feature_name}' será implementada no futuro.", parent=login_window)

        other_buttons_frame = tk.Frame(main_frame)
        other_buttons_frame.grid(row=3, column=0, columnspan=2)
        ttk.Button(other_buttons_frame, text="Primeiro Acesso", command=lambda: show_info("Primeiro Acesso")).pack(side="left", padx=5)
        ttk.Button(other_buttons_frame, text="Recuperar Senha", command=lambda: show_info("Recuperar Senha")).pack(side="left", padx=5)

    def abrir_modulo_memorial(self):
        memorial_window = tk.Toplevel(self)
        memorial_window.title("Memorial de Cálculo")
        memorial_window.geometry("1400x850")
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
        ajustes_window.geometry("1400x600")
        ajustes_frame = AjustesFrame(parent=ajustes_window, controller=self)
        ajustes_frame.pack(side="top", fill="both", expand=True)
        
        self.ajustes_window = ajustes_window
        self.ajustes_window.protocol("WM_DELETE_WINDOW", self.on_ajustes_close)

    def on_ajustes_close(self):
        if self.ajustes_window:
            self.ajustes_window.destroy()
        self.ajustes_window = None

# =========================================================================================
# === TELA 1: MENU PRINCIPAL ===
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
        
        btn_visualizacao = ttk.Button(buttons_frame, text="Visualização", style="Menu.TButton",
                                      command=lambda: controller.show_login_popup("Visualização"))
        btn_visualizacao.grid(row=0, column=0, padx=20, pady=20)

        btn_memorial = ttk.Button(buttons_frame, text="Memorial de Cálculo", style="Menu.TButton",
                                  command=lambda: controller.show_login_popup("Memorial de Cálculo"))
        btn_memorial.grid(row=0, column=1, padx=20, pady=20)

        btn_ajustes = ttk.Button(buttons_frame, text="Ajustes", style="Menu.TButton",
                                 command=lambda: controller.show_login_popup("Ajustes"))
        btn_ajustes.grid(row=0, column=2, padx=20, pady=20)


# ==========================================================================================
if __name__ == "__main__":
    app = App()
    app.mainloop()
