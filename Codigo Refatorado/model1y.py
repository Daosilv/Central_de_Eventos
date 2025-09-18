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
        colunas_sql = ', '.join([f'"{c}" TEXT' for c in columns_for_creation])
        
        query_cadastros = f"CREATE TABLE IF NOT EXISTS cadastros (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})"
        query_rascunhos = f"CREATE TABLE IF NOT EXISTS rascunhos (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})"
        query_ajustes = "CREATE TABLE IF NOT EXISTS ajustes (id INTEGER PRIMARY KEY AUTOINCREMENT, eqpto TEXT NOT NULL UNIQUE, data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP, observacao TEXT)"
        
        self._execute(query_cadastros, commit=True)
        self._execute(query_rascunhos, commit=True)
        self._execute(query_ajustes, commit=True)
        
        tabelas_para_verificar = ['cadastros', 'rascunhos']
        colunas_existentes = {}
        for tabela in tabelas_para_verificar:
            rows = self._execute(f"PRAGMA table_info({tabela})", fetch='all')
            if rows:
                colunas_existentes[tabela] = {row['name'] for row in rows}

        for col in columns_for_creation:
            for tabela in tabelas_para_verificar:
                if col not in colunas_existentes.get(tabela, set()):
                    try:
                        self._execute(f"ALTER TABLE {tabela} ADD COLUMN {col} TEXT", commit=True)
                    except sqlite3.OperationalError:
                        pass
        try:
            self._execute("ALTER TABLE ajustes ADD COLUMN observacao TEXT", commit=True)
        except sqlite3.OperationalError:
            pass

    def save_record(self, data_dict, table_name):
        data_to_save = data_dict.copy()
        data_to_save.pop('id', None)
        data_to_save.pop('data_registro', None)
        keys = ', '.join([f'"{k}"' for k in data_to_save.keys()])
        placeholders = ', '.join(['?'] * len(data_to_save))
        values = list(data_to_save.values())
        query = f"INSERT INTO {table_name} ({keys}) VALUES ({placeholders})"
        self._execute(query, values, commit=True)

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

    def get_recent_equipments(self, limit=50):
        query = "SELECT eqpto, ns, data, alimentador FROM cadastros WHERE eqpto != '' ORDER BY data_registro DESC LIMIT ?"
        return self._execute(query, (limit,), fetch='all')

    def get_all_draft_equipments(self):
        query = "SELECT eqpto, ns, data, alimentador FROM rascunhos WHERE eqpto != '' ORDER BY data_registro DESC"
        return self._execute(query, fetch='all')

    def delete_drafts(self, eqpto_list):
        params = [(eq,) for eq in eqpto_list]
        self._execute("DELETE FROM rascunhos WHERE eqpto = ?", params, commit=True, executemany=True)

    def get_record_by_id(self, record_id, table_name):
        query = f"SELECT * FROM {table_name} WHERE id = ?"
        return self._execute(query, (record_id,), fetch='one')

    def get_latest_id_for_equipment(self, eqpto, table_name):
        query = f"SELECT id FROM {table_name} WHERE eqpto = ? ORDER BY data_registro DESC LIMIT 1"
        return self._execute(query, (eqpto,), fetch='one')

    def get_pending_adjustments(self):
        query = """
        SELECT a.eqpto, c.autor, c.data, c.malha, c.alimentador, c.fabricante, c.comando
        FROM ajustes a
        JOIN (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn 
            FROM cadastros
        ) c ON a.eqpto = c.eqpto 
        WHERE c.rn = 1 
        ORDER BY a.data_adicao DESC
        """
        return self._execute(query, fetch='all')

    def complete_adjustment(self, eqpto):
        self._execute("DELETE FROM ajustes WHERE eqpto = ?", (eqpto,), commit=True)

    def get_observation(self, eqpto):
        return self._execute("SELECT observacao FROM ajustes WHERE eqpto = ?", (eqpto,), fetch='one')

    def update_observation(self, eqpto, text):
        self._execute("UPDATE ajustes SET observacao = ? WHERE eqpto = ?", (text, eqpto), commit=True)

    def search_records(self, filters):
        query = """
        SELECT id, eqpto, malha, alimentador, data_registro
        FROM (
            SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn
            FROM cadastros
        )
        WHERE rn = 1
        """
        condicoes = []
        params = []
        for campo, valor in filters.items():
            if valor:
                condicoes.append(f"{campo} LIKE ?")
                params.append(f"%{valor}%")
        if condicoes:
            query += " AND " + " AND ".join(condicoes)
        query += " ORDER BY data_registro DESC"
        return self._execute(query, tuple(params), fetch='all')
