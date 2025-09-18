import sqlite3
import os
from datetime import datetime
import hashlib

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
                    row = cursor.fetchone()
                    return dict(row) if row else None
                if fetch == 'all':
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows] if rows else []
        except sqlite3.Error as e:
            print(f"Erro no banco de dados: {e}")
            return None

    def create_tables(self, columns_for_creation):
        # Renomeia a tabela antiga de forma segura
        tables = self._execute("SELECT name FROM sqlite_master WHERE type='table';", fetch='all')
        table_names = [t['name'] for t in tables] if tables else []
        if 'opcoes_combobox' in table_names and 'opcoes_gerais' not in table_names:
            try:
                self._execute("ALTER TABLE opcoes_combobox RENAME TO opcoes_gerais", commit=True)
            except sqlite3.OperationalError as e:
                print(f"Não foi possível renomear opcoes_combobox: {e}")

        colunas_sql = ', '.join([f'"{c}" TEXT' for c in columns_for_creation])
        
        self._execute(f"CREATE TABLE IF NOT EXISTS cadastros (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})", commit=True)
        self._execute(f"CREATE TABLE IF NOT EXISTS rascunhos (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS ajustes (id INTEGER PRIMARY KEY AUTOINCREMENT, eqpto TEXT NOT NULL UNIQUE, data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT)", commit=True) # Coluna observacao removida
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
        # --- NOVA TABELA DE OBSERVAÇÕES ---
        self._execute("""
            CREATE TABLE IF NOT EXISTS observacoes_ajustes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                eqpto TEXT NOT NULL,
                autor TEXT,
                data_obs TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                texto TEXT NOT NULL
            )
        """, commit=True)

        self._check_and_add_columns(columns_for_creation)
    
    def _check_and_add_columns(self, columns_for_creation):
        tabelas_para_verificar = ['cadastros', 'rascunhos', 'ajustes']
        for tabela in tabelas_para_verificar:
            rows = self._execute(f"PRAGMA table_info({tabela})", fetch='all')
            if not rows: continue
            
            colunas_existentes = {row['name'] for row in rows}
            
            if tabela in ['cadastros', 'rascunhos']:
                cols_to_add = columns_for_creation
            elif tabela == 'ajustes':
                cols_to_add = ['status'] # A coluna 'observacao' não é mais necessária aqui
            else:
                continue

            for col in cols_to_add:
                if col not in colunas_existentes:
                    try:
                        self._execute(f"ALTER TABLE {tabela} ADD COLUMN {col} TEXT", commit=True)
                    except sqlite3.OperationalError:
                        pass
    
    # --- NOVOS MÉTODOS PARA O SISTEMA DE OBSERVAÇÕES ---
    def add_observation(self, eqpto, autor, texto):
        """Adiciona uma nova observação ao histórico de um equipamento."""
        query = "INSERT INTO observacoes_ajustes (eqpto, autor, texto) VALUES (?, ?, ?)"
        self._execute(query, (eqpto, autor, texto), commit=True)

    def get_observations(self, eqpto):
        """Recupera todas as observações de um equipamento, ordenadas por data."""
        query = "SELECT autor, data_obs, texto FROM observacoes_ajustes WHERE eqpto = ? ORDER BY data_obs ASC"
        return self._execute(query, (eqpto,), fetch='all')
    # ---------------------------------------------------------

    def get_categorias_gerais(self):
        rows = self._execute("SELECT DISTINCT categoria FROM opcoes_gerais ORDER BY categoria", fetch='all')
        categorias_db = [row['categoria'] for row in rows] if rows else []
        categorias_fixas = ['bypass', 'malha', 'condicao', 'motivador', 'midia', 'telecontrolado', 'manobra_efetiva', 'vinculado_acessante', 'alimentador', 'tensao_kv_rede']
        return sorted(list(set(categorias_db + categorias_fixas)))

    def get_opcoes_por_categoria_geral(self, categoria):
        # ALTERADO: "ORDER BY valor" para "ORDER BY id" para manter a ordem de inserção
        return self._execute("SELECT id, valor FROM opcoes_gerais WHERE categoria = ? ORDER BY id", (categoria,), fetch='all')

    def adicionar_opcao_geral(self, categoria, valor):
        self._execute("INSERT OR IGNORE INTO opcoes_gerais (categoria, valor) VALUES (?, ?)", (categoria, valor), commit=True)

    def editar_opcao_geral(self, id_opcao, novo_valor):
        self._execute("UPDATE opcoes_gerais SET valor = ? WHERE id = ?", (novo_valor, id_opcao), commit=True)

    def deletar_opcao_geral(self, id_opcao):
        self._execute("DELETE FROM opcoes_gerais WHERE id = ?", (id_opcao,), commit=True)

    def deletar_opcoes_por_categoria_geral(self, categoria):
        self._execute("DELETE FROM opcoes_gerais WHERE categoria = ?", (categoria,), commit=True)
        
    def get_opcoes_hierarquicas(self, id_pai=None):
        # ALTERADO: "ORDER BY valor" para "ORDER BY id" para manter a ordem de inserção
        if id_pai is None:
            return self._execute("SELECT * FROM opcoes_hierarquicas WHERE id_pai IS NULL ORDER BY id", fetch='all')
        else:
            return self._execute("SELECT * FROM opcoes_hierarquicas WHERE id_pai = ? ORDER BY id", (id_pai,), fetch='all')

    def adicionar_opcao_hierarquica(self, categoria, valor, id_pai=None):
        self._execute("INSERT INTO opcoes_hierarquicas (categoria, valor, id_pai) VALUES (?, ?, ?)", (categoria, valor, id_pai), commit=True)

    def editar_opcao_hierarquica(self, id_opcao, novo_valor):
        self._execute("UPDATE opcoes_hierarquicas SET valor = ? WHERE id = ?", (novo_valor, id_opcao), commit=True)

    def deletar_opcao_hierarquica(self, id_opcao):
        self._execute("DELETE FROM opcoes_hierarquicas WHERE id = ?", (id_opcao,), commit=True)

    def get_todos_cabos(self):
        # ALTERADO: "ORDER BY trecho" para "ORDER BY id" para manter a ordem de inserção
        return self._execute("SELECT * FROM cabos_propriedades ORDER BY id", fetch='all')

    def get_propriedades_cabo(self, trecho):
        return self._execute("SELECT nominal, admissivel FROM cabos_propriedades WHERE trecho = ?", (trecho,), fetch='one')

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
        # Define o status inicial como 'Pendente' ao ser adicionado na lista de ajustes
        self._execute("INSERT OR IGNORE INTO ajustes (eqpto, status) VALUES (?, ?)", (eqpto, 'Pendente'), commit=True)
        self._execute("UPDATE ajustes SET status = 'Pendente' WHERE eqpto = ?", (eqpto,), commit=True)
        self._execute("DELETE FROM rascunhos WHERE eqpto = ?", (eqpto,), commit=True)

    def get_record_by_id(self, record_id, table_name='cadastros'):
        return self._execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,), fetch='one')
    
    def get_latest_id_for_equipment(self, eqpto, table_name):
        return self._execute(f"SELECT id FROM {table_name} WHERE eqpto = ? ORDER BY data_registro DESC LIMIT 1", (eqpto,), fetch='one')

    def search_records(self, filters):
        query = "SELECT id, eqpto, malha, alimentador, data_registro FROM (SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn FROM cadastros) WHERE rn = 1"
        condicoes, params = [], []
        for campo, valor in filters.items():
            if valor:
                condicoes.append(f"{campo} LIKE ?")
                params.append(f"%{valor}%")
        if condicoes: query += " AND " + " AND ".join(condicoes)
        query += " ORDER BY data_registro DESC"
        return self._execute(query, tuple(params), fetch='all')

    def get_recent_equipments_with_status(self, limit=50):
        """
        Busca equipamentos recentes da tabela de cadastros, juntando o status
        mais atualizado a partir das tabelas 'ajustes' ou 'historico_ajustes'.
        """
        query = """
            SELECT
                c.eqpto, c.ns, c.data_registro, c.alimentador,
                COALESCE(a.status, latest_h.status, 'Pendente') as status
            FROM (
                SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn
                FROM cadastros
                WHERE eqpto != ''
            ) c
            LEFT JOIN ajustes a ON c.eqpto = a.eqpto
            LEFT JOIN (
                SELECT eqpto, status, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_conclusao DESC) as rn
                FROM historico_ajustes
            ) latest_h ON c.eqpto = latest_h.eqpto AND latest_h.rn = 1
            WHERE c.rn = 1
            ORDER BY c.data_registro DESC
            LIMIT ?
        """
        return self._execute(query, (limit,), fetch='all')

    def get_all_draft_equipments(self):
        return self._execute("SELECT eqpto, ns, data, alimentador FROM rascunhos WHERE eqpto != '' ORDER BY data_registro DESC", fetch='all')

    def delete_drafts(self, eqpto_list):
        params = [(eq,) for eq in eqpto_list]
        self._execute("DELETE FROM rascunhos WHERE eqpto = ?", params, commit=True, executemany=True)

    def get_pending_adjustments(self):
        return self._execute("""
            SELECT a.eqpto, a.status, c.autor, c.data, c.malha, c.alimentador, c.fabricante, c.comando
            FROM ajustes a
            JOIN (
                SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn 
                FROM cadastros
            ) c ON a.eqpto = c.eqpto 
            WHERE c.rn = 1 
            ORDER BY a.data_adicao DESC
        """, fetch='all')

    def complete_adjustment(self, eqpto, status):
        self._execute("INSERT INTO historico_ajustes (eqpto, status) VALUES (?, ?)", (eqpto, status), commit=True)
        self._execute("DELETE FROM ajustes WHERE eqpto = ?", (eqpto,), commit=True)
        
    def update_adjustment_status(self, eqpto_list, status):
        params = [(status, eq,) for eq in eqpto_list]
        self._execute("UPDATE ajustes SET status = ? WHERE eqpto = ?", params, commit=True, executemany=True)

    def get_adjustments_history(self, limit=100):
        return self._execute("SELECT eqpto, data_conclusao, status FROM historico_ajustes ORDER BY data_conclusao DESC LIMIT ?", (limit,), fetch='all')
