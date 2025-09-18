import tkinter as tk
from tkinter import ttk, messagebox

# Importa as classes das telas que estão nos outros arquivos .py
from menu_frame import MenuFrame
from memorial_frame import MemorialCalculoFrame
# No futuro, importaremos os outros módulos aqui:
# from visualizacao_frame import VisualizacaoFrame
# from ajustes_frame import AjustesFrame


class App(tk.Tk):
    """
    Classe principal da aplicação. Atua como o "maestro",
    gerenciando a janela e a troca entre as diferentes telas (módulos).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("Central de Eventos")
        self.geometry("1280x768")

        # Container principal onde todas as telas (frames) serão empilhadas
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Lista de todas as páginas/módulos que o aplicativo terá.
        # Adicione as novas classes de frame aqui quando forem criadas.
        pages_to_load = (MenuFrame, MemorialCalculoFrame)

        for F in pages_to_load:
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Inicia mostrando o menu principal
        self.show_frame("MenuFrame")

    def show_frame(self, page_name):
        """Traz o frame solicitado para a frente."""
        frame = self.frames[page_name]
        frame.tkraise()

    def show_login_popup(self, target_page_name):
        """
        Abre a janela de login simulada. Se o login for "bem-sucedido",
        tenta navegar para a página de destino.
        """
        login_window = tk.Toplevel(self)
        login_window.title("Autenticação Necessária")
        login_window.geometry("350x200")
        login_window.resizable(False, False)
        login_window.transient(self) # Mantém a janela na frente da principal
        login_window.grab_set()      # Bloqueia interação com a janela principal

        # Centraliza a janela de login
        x = self.winfo_x() + (self.winfo_width() / 2) - (350 / 2)
        y = self.winfo_y() + (self.winfo_height() / 2) - (200 / 2)
        login_window.geometry(f"+{int(x)}+{int(y)}")

        main_frame = tk.Frame(login_window, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="Usuário:").grid(row=0, column=0, sticky="w", pady=5)
        tk.Entry(main_frame).grid(row=0, column=1, sticky="ew")

        tk.Label(main_frame, text="Senha:").grid(row=1, column=0, sticky="w", pady=5)
        tk.Entry(main_frame, show="*").grid(row=1, column=1, sticky="ew")

        def on_login_success():
            """Função chamada após o login simulado."""
            login_window.destroy()
            
            # Verifica se a página de destino já foi carregada no app
            if target_page_name in self.frames:
                self.show_frame(target_page_name)
            else:
                # Se o frame não existe (ex: "VisualizacaoFrame"), mostra placeholder
                messagebox.showinfo("Em Desenvolvimento", 
                                    f"O módulo '{target_page_name}' será implementado futuramente.", 
                                    parent=self)
        
        button_frame = tk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="Entrar", command=on_login_success).pack(side="left", padx=5)

        # Botões de simulação
        def show_info(feature_name):
            messagebox.showinfo("Simulação", f"A funcionalidade '{feature_name}' será implementada no futuro.", parent=login_window)

        other_buttons_frame = tk.Frame(main_frame)
        other_buttons_frame.grid(row=3, column=0, columnspan=2)
        ttk.Button(other_buttons_frame, text="Primeiro Acesso", command=lambda: show_info("Primeiro Acesso")).pack(side="left", padx=5)
        ttk.Button(other_buttons_frame, text="Recuperar Senha", command=lambda: show_info("Recuperar Senha")).pack(side="left", padx=5)


# --- Bloco de Execução Principal ---
if __name__ == "__main__":
    app = App()
    app.mainloop()
