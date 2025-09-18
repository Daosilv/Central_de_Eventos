import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import tempfile
import atexit
import hashlib
import random
import openpyxl

try:
    import psutil
except ImportError:
    messagebox.showerror("Biblioteca Faltando", "A biblioteca 'psutil' é necessária. Instale com: pip install psutil")
    sys.exit(1)

from model import DatabaseModel
from memorial_frame import MemorialCalculoFrame
from visualizacao_frame import VisualizacaoFrame
from ajustes_frame import AjustesFrame
from gestao_frame import GestaoFrame

FONTE_TITULO = ("Helvetica", 22, "bold")
FONTE_BOTAO_MENU = ("Helvetica", 14)
CAMINHO_BD = r'C:\BD_APP_Cemig\Primeiro_banco.db'

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
        menu_frame = MenuFrame(container, self)
        self.frames[MenuFrame.__name__] = menu_frame
        menu_frame.grid(row=0, column=0, sticky="nsew")
        menu_frame.tkraise()

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
        gestao_window.geometry("950x600")
        gestao_window.transient(self)
        gestao_window.grab_set()
        gestao_frame = GestaoFrame(parent=gestao_window, controller=self)
        gestao_frame.pack(side="top", fill="both", expand=True)
        
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
        view.lista_ajustes_completa = self.model.get_recent_equipments_with_status()
        view.lista_rascunhos_completa = self.model.get_all_draft_equipments()
        view.reconstruir_lista_ajustes()
        view.reconstruir_lista_rascunhos()

    def export_to_excel(self, view):
        template_dir = r'C:\Central_de_Eventos\Diretório Excel Padrão'
        save_dir = r'C:\Central_de_Eventos\Diretório Excel Final'
        template_filename = 'Planilha_MonoTrifasico_vs35_REDE.xlsm'
        template_path = os.path.join(template_dir, template_filename)

        try:
            os.makedirs(save_dir, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Erro de Diretório", f"Não foi possível criar o diretório final:\n{e}", parent=view.parent_window)
            return

        data = view._get_form_data()
        eqpto = data.get("eqpto")
        if not eqpto:
            messagebox.showwarning("Atenção", "Preencha ao menos o campo 'Eqpto' para exportar.", parent=view.parent_window)
            return
            
        mapeamentos_db = self.model.get_all_mapeamentos()
        if not mapeamentos_db:
            messagebox.showerror("Erro", "Nenhum mapeamento para o Excel foi encontrado.\nPor favor, cadastre os campos na aba 'Mapeamento Excel' do Módulo de Gestão.", parent=view.parent_window)
            return
        
        mapeamento = {item['campo_app']: (item['aba_excel'], item['celula_excel']) for item in mapeamentos_db}

        random_suffix = random.randint(100, 999)
        new_filename = f"Planilha_MonoTrifasico_vs35_REDE_{eqpto}_{random_suffix}.xlsm"
        save_path = os.path.join(save_dir, new_filename)

        try:
            workbook = openpyxl.load_workbook(template_path, keep_vba=True)

            for campo, (aba, celula) in mapeamento.items():
                if aba in workbook.sheetnames:
                    sheet = workbook[aba]
                    valor = data.get(campo, "")
                    sheet[celula] = valor

            workbook.save(save_path)
            messagebox.showinfo("Sucesso", f"Planilha salva com sucesso em:\n{save_path}", parent=view.parent_window)

        except FileNotFoundError:
            messagebox.showerror("Erro", f"O template da planilha não foi encontrado em:\n{template_path}", parent=view.parent_window)
        except Exception as e:
            messagebox.showerror("Erro Inesperado", f"Ocorreu um erro ao gerar a planilha:\n{e}", parent=view.parent_window)

    def carregar_ficha_pelo_nome(self, view, eqpto, tabela):
        id_result = self.model.get_latest_id_for_equipment(eqpto, tabela)
        if id_result:
            record_data = self.model.get_record_by_id(id_result['id'], tabela)
            if record_data:
                view.preencher_formulario(record_data)

    def deletar_rascunhos(self, view, eqpto_list):
        self.model.delete_drafts(eqpto_list)
        messagebox.showinfo("Sucesso", f"{len(eqpto_list)} rascunhos foram deletados.", parent=view.parent_window)
        self.atualizar_listas_memorial(view)

    def carregar_ajustes_pendentes(self):
        return self.model.get_pending_adjustments()

    def concluir_ajuste(self, eqpto, status):
        self.model.complete_adjustment(eqpto, status)

    def carregar_observacoes(self, eqpto):
        return self.model.get_observations(eqpto)

    def adicionar_observacao(self, eqpto, autor, texto):
        self.model.add_observation(eqpto, autor, texto)

    def buscar_registros(self, filtros):
        return self.model.search_records(filtros)

    def get_record_by_id(self, record_id, table_name='cadastros'):
        return self.model.get_record_by_id(record_id, table_name)
        
    def update_ajuste_status(self, eqpto_list, status):
        self.model.update_adjustment_status(eqpto_list, status)

    def get_historico_ajustes(self):
        return self.model.get_adjustments_history()

    def get_categorias_gerais(self):
        return self.model.get_categorias_gerais()

    def get_opcoes_por_categoria_geral(self, categoria):
        return self.model.get_opcoes_por_categoria_geral(categoria)

    def adicionar_opcao_geral(self, categoria, valor):
        self.model.adicionar_opcao_geral(categoria, valor)

    def editar_opcao_geral(self, id_opcao, novo_valor):
        self.model.editar_opcao_geral(id_opcao, novo_valor)

    def deletar_opcao_geral(self, id_opcao):
        self.model.deletar_opcao_geral(id_opcao)
        
    def deletar_opcoes_por_categoria_geral(self, categoria):
        self.model.deletar_opcoes_por_categoria_geral(categoria)

    def get_opcoes_hierarquicas(self, id_pai=None):
        return self.model.get_opcoes_hierarquicas(id_pai)

    def adicionar_opcao_hierarquica(self, categoria, valor, id_pai=None):
        self.model.adicionar_opcao_hierarquica(categoria, valor, id_pai)

    def editar_opcao_hierarquica(self, id_opcao, novo_valor):
        self.model.editar_opcao_hierarquica(id_opcao, novo_valor)

    def deletar_opcao_hierarquica(self, id_opcao):
        self.model.deletar_opcao_hierarquica(id_opcao)

    def get_todos_cabos(self):
        return self.model.get_todos_cabos()
    
    def get_propriedades_cabo(self, trecho):
        return self.model.get_propriedades_cabo(trecho)

    def adicionar_cabo(self, trecho, nominal, admissivel):
        self.model.adicionar_cabo(trecho, nominal, admissivel)

    def editar_cabo(self, id_cabo, trecho, nominal, admissivel):
        self.model.editar_cabo(id_cabo, trecho, nominal, admissivel)

    def deletar_cabo(self, id_cabo):
        self.model.deletar_cabo(id_cabo)

    # --- NOVAS FUNÇÕES PARA CONECTAR A ABA MAPEAMENTO COM O BANCO DE DADOS ---
    def get_all_mapeamentos(self):
        return self.model.get_all_mapeamentos()

    def adicionar_mapeamentos_massa(self, mapeamentos_lista):
        self.model.adicionar_mapeamentos_massa(mapeamentos_lista)

    def deletar_mapeamento(self, map_id):
        self.model.deletar_mapeamento(map_id)

    def deletar_todos_mapeamentos(self):
        self.model.deletar_todos_mapeamentos()


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
    lock_file_path = os.path.join(tempfile.gettempdir(), 'central_eventos.lock')
    current_script_path = os.path.abspath(sys.argv[0])

    def is_process_running(pid):
        if pid is None: return False
        try:
            process = psutil.Process(pid)
            if any(current_script_path in arg for arg in process.cmdline()):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False
        return False

    def remover_lock_file():
        try:
            if os.path.exists(lock_file_path): os.remove(lock_file_path)
        except OSError: pass

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

    app = App()
    app.mainloop()
