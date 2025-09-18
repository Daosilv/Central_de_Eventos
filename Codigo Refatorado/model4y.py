import sqlite3
import os
from datetime import datetime

class DatabaseModel:
    def __init__(self, db_path):
        self.db_path = db_path
        db_dir = os.path.dirname(db_path)
        os.makedirs(db_dir, exist_ok=True)

    def _execute(self, query, params=(), commit=False, fetch=None, executemany=False):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                if executemany:
                    cursor.executemany(query, params)
                else:
                    cursor.execute(query, params)
                
                if commit:
                    conn.commit()
                
                if fetch == 'one':
                    return cursor.fetchone()
                if fetch == 'all':
                    return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro no banco de dados: {e}")
            return None

    def create_tables(self, columns_for_creation):
        try:
            self._execute("ALTER TABLE opcoes_combobox RENAME TO opcoes_gerais", commit=True)
        except sqlite3.OperationalError:
            pass

        colunas_sql = ', '.join([f'"{c}" TEXT' for c in columns_for_creation])
        
        self._execute(f"CREATE TABLE IF NOT EXISTS cadastros (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})", commit=True)
        self._execute(f"CREATE TABLE IF NOT EXISTS rascunhos (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS ajustes (id INTEGER PRIMARY KEY AUTOINCREMENT, eqpto TEXT NOT NULL UNIQUE, data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP, observacao TEXT, status TEXT)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS historico_ajustes (id INTEGER PRIMARY KEY AUTOINCREMENT, eqpto TEXT, data_conclusao TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS opcoes_gerais (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT NOT NULL, valor TEXT NOT NULL, UNIQUE(categoria, valor))", commit=True)
        self._execute("""
            CREATE TABLE IF NOT EXISTS opcoes_hierarquicas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                valor TEXT NOT NULL,
                id_pai INTEGER,
                FOREIGN KEY (id_pai) REFERENCES opcoes_hierarquicas(id) ON DELETE CASCADE
            )
        """, commit=True)
        self._execute("""
            CREATE TABLE IF NOT EXISTS cabos_propriedades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trecho TEXT NOT NULL UNIQUE,
                nominal TEXT,
                admissivel TEXT
            )
        """, commit=True)

        self._check_and_add_columns(columns_for_creation)

    def _check_and_add_columns(self, columns_for_creation):
        tabelas_para_verificar = ['cadastros', 'rascunhos']
        for tabela in tabelas_para_verificar:
            rows = self._execute(f"PRAGMA table_info({tabela})", fetch='all')
            if not rows: continue
            colunas_existentes = {row['name'] for row in rows}
            for col in columns_for_creation:
                if col not in colunas_existentes:
                    try: self._execute(f"ALTER TABLE {tabela} ADD COLUMN {col} TEXT", commit=True)
                    except sqlite3.OperationalError: pass
        try: self._execute("ALTER TABLE ajustes ADD COLUMN observacao TEXT", commit=True)
        except sqlite3.OperationalError: pass
        try: self._execute("ALTER TABLE ajustes ADD COLUMN status TEXT", commit=True)
        except sqlite3.OperationalError: pass

    def get_categorias_gerais(self):
        query = "SELECT DISTINCT categoria FROM opcoes_gerais ORDER BY categoria"
        rows = self._execute(query, fetch='all')
        return [row['categoria'] for row in rows] if rows else []

    def get_opcoes_por_categoria_geral(self, categoria):
        query = "SELECT id, valor FROM opcoes_gerais WHERE categoria = ? ORDER BY valor"
        rows = self._execute(query, (categoria,), fetch='all')
        return [dict(row) for row in rows] if rows else []

    def adicionar_opcao_geral(self, categoria, valor):
        query = "INSERT OR IGNORE INTO opcoes_gerais (categoria, valor) VALUES (?, ?)"
        self._execute(query, (categoria, valor), commit=True)

    def editar_opcao_geral(self, id_opcao, novo_valor):
        query = "UPDATE opcoes_gerais SET valor = ? WHERE id = ?"
        self._execute(query, (novo_valor, id_opcao), commit=True)

    def deletar_opcao_geral(self, id_opcao):
        query = "DELETE FROM opcoes_gerais WHERE id = ?"
        self._execute(query, (id_opcao,), commit=True)

    def deletar_opcoes_por_categoria_geral(self, categoria):
        query = "DELETE FROM opcoes_gerais WHERE categoria = ?"
        self._execute(query, (categoria,), commit=True)
        
    def get_opcoes_hierarquicas(self, id_pai=None):
        if id_pai is None:
            query = "SELECT * FROM opcoes_hierarquicas WHERE id_pai IS NULL ORDER BY valor"
            rows = self._execute(query, fetch='all')
        else:
            query = "SELECT * FROM opcoes_hierarquicas WHERE id_pai = ? ORDER BY valor"
            rows = self._execute(query, (id_pai,), fetch='all')
        return [dict(row) for row in rows] if rows else []

    def adicionar_opcao_hierarquica(self, categoria, valor, id_pai=None):
        query = "INSERT INTO opcoes_hierarquicas (categoria, valor, id_pai) VALUES (?, ?, ?)"
        self._execute(query, (categoria, valor, id_pai), commit=True)

    def editar_opcao_hierarquica(self, id_opcao, novo_valor):
        self._execute("UPDATE opcoes_hierarquicas SET valor = ? WHERE id = ?", (novo_valor, id_opcao), commit=True)

    def deletar_opcao_hierarquica(self, id_opcao):
        self._execute("DELETE FROM opcoes_hierarquicas WHERE id = ?", (id_opcao,), commit=True)

    def get_todos_cabos(self):
        rows = self._execute("SELECT * FROM cabos_propriedades ORDER BY trecho", fetch='all')
        return [dict(row) for row in rows] if rows else []

    def get_propriedades_cabo(self, trecho):
        row = self._execute("SELECT nominal, admissivel FROM cabos_propriedades WHERE trecho = ?", (trecho,), fetch='one')
        return dict(row) if row else None

    def adicionar_cabo(self, trecho, nominal, admissivel):
        self._execute("INSERT OR IGNORE INTO cabos_propriedades (trecho, nominal, admissivel) VALUES (?, ?, ?)", (trecho, nominal, admissivel), commit=True)

    def editar_cabo(self, id_cabo, trecho, nominal, admissivel):
        self._execute("UPDATE cabos_propriedades SET trecho = ?, nominal = ?, admissivel = ? WHERE id = ?", (trecho, nominal, admissivel, id_cabo), commit=True)

    def deletar_cabo(self, id_cabo):
        self._execute("DELETE FROM cabos_propriedades WHERE id = ?", (id_cabo,), commit=True)

    def save_record(self, data_dict, table_name):
        data_to_save = data_dict.copy()
        data_to_save.pop('id', None); data_to_save.pop('data_registro', None)
        keys = ', '.join([f'"{k}"' for k in data_to_save.keys()])
        placeholders = ', '.join(['?'] * len(data_to_save))
        values = list(data_to_save.values())
        self._execute(f"INSERT INTO {table_name} ({keys}) VALUES ({placeholders})", values, commit=True)

    def save_draft(self, data_dict):
        eqpto = data_dict.get('eqpto')
        if not eqpto: return
        self._execute("DELETE FROM rascunhos WHERE eqpto = ?", (eqpto,), commit=True)
        self.save_record(data_dict, 'rascunhos')

    def save_final_and_manage_lists(self, data_dict):
        eqpto = data_dict.get('eqpto')
        if not eqpto: return
        self._execute("DELETE FROM cadastros WHERE eqpto = ?", (eqpto,), commit=True)
        self.save_record(data_dict, 'cadastros')
        self._execute("INSERT OR IGNORE INTO ajustes (eqpto) VALUES (?)", (eqpto,), commit=True)
        self._execute("DELETE FROM rascunhos WHERE eqpto = ?", (eqpto,), commit=True)

    def get_record_by_id(self, record_id, table_name):
        row = self._execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,), fetch='one')
        return dict(row) if row else None
    
    def get_latest_id_for_equipment(self, eqpto, table_name):
        row = self._execute(f"SELECT id FROM {table_name} WHERE eqpto = ? ORDER BY data_registro DESC LIMIT 1", (eqpto,), fetch='one')
        return dict(row) if row else None

    def search_records(self, filters):
        query = "SELECT id, eqpto, malha, alimentador, data_registro FROM (SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn FROM cadastros) WHERE rn = 1"
        condicoes, params = [], []
        for campo, valor in filters.items():
            if valor:
                condicoes.append(f"{campo} LIKE ?")
                params.append(f"%{valor}%")
        if condicoes: query += " AND " + " AND ".join(condicoes)
        query += " ORDER BY data_registro DESC"
        rows = self._execute(query, tuple(params), fetch='all')
        return [dict(row) for row in rows] if rows else []

    def get_recent_equipments(self, limit=50):
        query = "SELECT eqpto, ns, data, alimentador FROM cadastros WHERE eqpto != '' ORDER BY data_registro DESC LIMIT ?"
        rows = self._execute(query, (limit,), fetch='all')
        return [dict(row) for row in rows] if rows else []

    def get_all_draft_equipments(self):
        query = "SELECT eqpto, ns, data, alimentador FROM rascunhos WHERE eqpto != '' ORDER BY data_registro DESC"
        rows = self._execute(query, fetch='all')
        return [dict(row) for row in rows] if rows else []

    def delete_drafts(self, eqpto_list):
        params = [(eq,) for eq in eqpto_list]
        self._execute("DELETE FROM rascunhos WHERE eqpto = ?", params, commit=True, executemany=True)

    def get_pending_adjustments(self):
        query = """
        SELECT a.eqpto, a.status, c.autor, c.data, c.malha, c.alimentador, c.fabricante, c.comando
        FROM ajustes a
        JOIN (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn 
            FROM cadastros
        ) c ON a.eqpto = c.eqpto 
        WHERE c.rn = 1 
        ORDER BY a.data_adicao DESC
        """
        rows = self._execute(query, fetch='all')
        return [dict(row) for row in rows] if rows else []

    def complete_adjustment(self, eqpto, status):
        self._execute("INSERT INTO historico_ajustes (eqpto, status) VALUES (?, ?)", (eqpto, status), commit=True)
        self._execute("DELETE FROM ajustes WHERE eqpto = ?", (eqpto,), commit=True)

    def get_observation(self, eqpto):
        row = self._execute("SELECT observacao FROM ajustes WHERE eqpto = ?", (eqpto,), fetch='one')
        return dict(row) if row else None

    def update_observation(self, eqpto, text):
        self._execute("UPDATE ajustes SET observacao = ? WHERE eqpto = ?", (text, eqpto), commit=True)
        
    def update_adjustment_status(self, eqpto_list, status):
        params = [(status, eq,) for eq in eqpto_list]
        self._execute("UPDATE ajustes SET status = ? WHERE eqpto = ?", params, commit=True, executemany=True)

    def get_adjustments_history(self, limit=100):
        query = "SELECT eqpto, data_conclusao, status FROM historico_ajustes ORDER BY data_conclusao DESC LIMIT ?"
        rows = self._execute(query, (limit,), fetch='all')
        return [dict(row) for row in rows] if rows else []
