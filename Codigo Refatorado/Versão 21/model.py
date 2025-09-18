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
        colunas_sql = ', '.join([f'"{c}" TEXT' for c in columns_for_creation])
        
        self._execute(f"CREATE TABLE IF NOT EXISTS cadastros (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})", commit=True)
        self._execute(f"CREATE TABLE IF NOT EXISTS rascunhos (id INTEGER PRIMARY KEY AUTOINCREMENT, data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, {colunas_sql})", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS ajustes (id INTEGER PRIMARY KEY AUTOINCREMENT, eqpto TEXT NOT NULL UNIQUE, data_adicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS historico_ajustes (id INTEGER PRIMARY KEY AUTOINCREMENT, eqpto TEXT, data_conclusao TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS opcoes_gerais (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT NOT NULL, valor TEXT NOT NULL, UNIQUE(categoria, valor))", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS opcoes_hierarquicas (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT NOT NULL, valor TEXT NOT NULL, id_pai INTEGER, FOREIGN KEY (id_pai) REFERENCES opcoes_hierarquicas(id) ON DELETE CASCADE)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS cabos_propriedades (id INTEGER PRIMARY KEY AUTOINCREMENT, trecho TEXT NOT NULL UNIQUE, nominal TEXT, admissivel TEXT)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS observacoes_ajustes (id INTEGER PRIMARY KEY AUTOINCREMENT, eqpto TEXT NOT NULL, autor TEXT, data_obs TIMESTAMP DEFAULT CURRENT_TIMESTAMP, texto TEXT NOT NULL)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS mapeamento_excel (id INTEGER PRIMARY KEY AUTOINCREMENT, campo_app TEXT NOT NULL, aba_excel TEXT NOT NULL, celula_excel TEXT NOT NULL)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_completo TEXT NOT NULL, matricula TEXT NOT NULL UNIQUE, email TEXT, permissoes TEXT, dados_adicionais TEXT)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS mapas_excel (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS ajuda_conteudo (id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, texto TEXT, anexos TEXT)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS tempo_morto_config (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, v1 TEXT, v2 TEXT, v3 TEXT, v4 TEXT)", commit=True)
        self._execute("CREATE TABLE IF NOT EXISTS grupo4_config (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, v1 TEXT, v2 TEXT, v3 TEXT, v4 TEXT, v5 TEXT, v6 TEXT, v7 TEXT, v8 TEXT, v9 TEXT, v10 TEXT)", commit=True)
        self._execute("INSERT OR IGNORE INTO tempo_morto_config (nome, v1, v2, v3, v4) VALUES ('Tempo Morto Padrão', '', '', '', '')", commit=True)
        self._execute("INSERT OR IGNORE INTO grupo4_config (nome, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10) VALUES ('Grupo 4 Padrão', '', '', '', '', '', '', '', '', '', '')", commit=True)
        self._check_and_add_columns(columns_for_creation)
        self._migrate_user_table()
        self._migrate_mappings_table()

    def get_all_ajuda(self):
        return self._execute("SELECT id, titulo FROM ajuda_conteudo ORDER BY titulo ASC", fetch='all')

    def get_ajuda_by_id(self, ajuda_id):
        return self._execute("SELECT * FROM ajuda_conteudo WHERE id = ?", (ajuda_id,), fetch='one')

    def add_ajuda(self, titulo):
        self._execute("INSERT INTO ajuda_conteudo (titulo, texto, anexos) VALUES (?, ?, ?)", (titulo, "", "[]"), commit=True)

    def update_ajuda(self, ajuda_id, titulo, texto, anexos):
        self._execute("UPDATE ajuda_conteudo SET titulo = ?, texto = ?, anexos = ? WHERE id = ?", (titulo, texto, anexos, ajuda_id), commit=True)

    def delete_ajuda(self, ajuda_id):
        self._execute("DELETE FROM ajuda_conteudo WHERE id = ?", (ajuda_id,), commit=True)

    def get_all_tempo_morto(self):
        return self._execute("SELECT * FROM tempo_morto_config ORDER BY id ASC", fetch='all')

    def add_tempo_morto(self, data):
        self._execute("INSERT INTO tempo_morto_config (nome, v1, v2, v3, v4) VALUES (?, ?, ?, ?, ?)", (data['nome'], data['v1'], data['v2'], data['v3'], data['v4']), commit=True)

    def update_tempo_morto(self, config_id, data):
        self._execute("UPDATE tempo_morto_config SET nome = ?, v1 = ?, v2 = ?, v3 = ?, v4 = ? WHERE id = ?", (data['nome'], data['v1'], data['v2'], data['v3'], data['v4'], config_id), commit=True)

    def delete_tempo_morto(self, config_id):
        self._execute("DELETE FROM tempo_morto_config WHERE id = ?", (config_id,), commit=True)

    def get_all_grupo4(self):
        return self._execute("SELECT * FROM grupo4_config ORDER BY id ASC", fetch='all')

    def add_grupo4(self, data):
        params = [data['nome']] + [data.get(f'v{i+1}', '') for i in range(10)]
        self._execute("INSERT INTO grupo4_config (nome, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", params, commit=True)

    def update_grupo4(self, config_id, data):
        params = [data['nome']] + [data.get(f'v{i+1}', '') for i in range(10)] + [config_id]
        self._execute("UPDATE grupo4_config SET nome = ?, v1 = ?, v2 = ?, v3 = ?, v4 = ?, v5 = ?, v6 = ?, v7 = ?, v8 = ?, v9 = ?, v10 = ? WHERE id = ?", params, commit=True)

    def delete_grupo4(self, config_id):
        self._execute("DELETE FROM grupo4_config WHERE id = ?", (config_id,), commit=True)
    
    def _check_and_add_columns(self, columns_for_creation):
        tabelas_para_verificar = ['cadastros', 'rascunhos']
        for tabela in tabelas_para_verificar:
            rows = self._execute(f"PRAGMA table_info({tabela})", fetch='all')
            if not rows: continue
            colunas_existentes = {row['name'] for row in rows}
            for col in columns_for_creation:
                if col not in colunas_existentes:
                    self._execute(f"ALTER TABLE {tabela} ADD COLUMN {col} TEXT", commit=True)
    
    def _migrate_user_table(self):
        table_info = self._execute("PRAGMA table_info(usuarios)", fetch='all')
        if not table_info: return
        existing_columns = {col['name'] for col in table_info}
        required_columns = {"id", "nome_completo", "matricula", "email", "permissoes", "dados_adicionais"}
        missing_columns = required_columns - existing_columns
        for col_name in missing_columns:
            self._execute(f"ALTER TABLE usuarios ADD COLUMN {col_name} TEXT", commit=True)

    def _migrate_mappings_table(self):
        table_info = self._execute("PRAGMA table_info(mapeamento_excel)", fetch='all')
        if not table_info: return
        
        existing_columns = {col['name'] for col in table_info}
        if 'mapa_id' not in existing_columns:
            self._execute("ALTER TABLE mapeamento_excel ADD COLUMN mapa_id INTEGER REFERENCES mapas_excel(id) ON DELETE CASCADE", commit=True)
            self._execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mapa_campo ON mapeamento_excel (mapa_id, campo_app)", commit=True)

        orphans = self._execute("SELECT id FROM mapeamento_excel WHERE mapa_id IS NULL LIMIT 1", fetch='one')
        if orphans:
            self._execute("INSERT OR IGNORE INTO mapas_excel (nome) VALUES (?)", ("Mapa Padrão",), commit=True)
            default_map = self._execute("SELECT id FROM mapas_excel WHERE nome = ?", ("Mapa Padrão",), fetch='one')
            if default_map:
                self._execute("UPDATE mapeamento_excel SET mapa_id = ? WHERE mapa_id IS NULL", (default_map['id'],), commit=True)

    def get_all_map_names(self):
        return self._execute("SELECT id, nome FROM mapas_excel ORDER BY nome ASC", fetch='all')

    def add_map_name(self, name):
        self._execute("INSERT OR IGNORE INTO mapas_excel (nome) VALUES (?)", (name,), commit=True)

    def rename_map_name(self, map_id, new_name):
        self._execute("UPDATE mapas_excel SET nome = ? WHERE id = ?", (new_name, map_id), commit=True)

    def delete_map(self, map_id):
        self._execute("DELETE FROM mapas_excel WHERE id = ?", (map_id,), commit=True)

    def get_mappings_for_map(self, map_id):
        return self._execute("SELECT * FROM mapeamento_excel WHERE mapa_id = ? ORDER BY id", (map_id,), fetch='all')

    def add_mappings_to_map(self, map_id, mappings_list):
        params = [(map_id, item[0], item[1], item[2]) for item in mappings_list]
        campos_app = [item[0] for item in mappings_list]
        placeholders = ','.join('?' for _ in campos_app)
        self._execute(f"DELETE FROM mapeamento_excel WHERE mapa_id = ? AND campo_app IN ({placeholders})", [map_id] + campos_app, commit=True)
        self._execute("INSERT INTO mapeamento_excel (mapa_id, campo_app, aba_excel, celula_excel) VALUES (?, ?, ?, ?)", params, commit=True, executemany=True)

    def update_mapping(self, mapping_id, data):
        query = "UPDATE mapeamento_excel SET campo_app = ?, aba_excel = ?, celula_excel = ? WHERE id = ?"
        params = (data['campo_app'], data['aba_excel'], data['celula_excel'], mapping_id)
        self._execute(query, params, commit=True)

    def deletar_mapeamentos_por_mapa(self, map_id):
        self._execute("DELETE FROM mapeamento_excel WHERE mapa_id = ?", (map_id,), commit=True)

    def get_all_users(self):
        return self._execute("SELECT * FROM usuarios ORDER BY nome_completo ASC", fetch='all')
        
    def add_user(self, data):
        query = "INSERT INTO usuarios (nome_completo, matricula, email, permissoes, dados_adicionais) VALUES (:nome_completo, :matricula, :email, :permissoes, :dados_adicionais)"
        self._execute(query, data, commit=True)
        
    def update_user(self, user_id, data):
        query = "UPDATE usuarios SET nome_completo = :nome_completo, matricula = :matricula, email = :email, permissoes = :permissoes, dados_adicionais = :dados_adicionais WHERE id = :id"
        data['id'] = user_id
        self._execute(query, data, commit=True)
        
    def delete_user(self, user_id):
        self._execute("DELETE FROM usuarios WHERE id = ?", (user_id,), commit=True)
        
    def add_observation(self, eqpto, autor, texto):
        query = "INSERT INTO observacoes_ajustes (eqpto, autor, texto) VALUES (?, ?, ?)"
        self._execute(query, (eqpto, autor, texto), commit=True)
        
    def get_observations(self, eqpto):
        query = "SELECT autor, data_obs, texto FROM observacoes_ajustes WHERE eqpto = ? ORDER BY data_obs ASC"
        return self._execute(query, (eqpto,), fetch='all')
        
    def get_categorias_gerais(self):
        rows = self._execute("SELECT DISTINCT categoria FROM opcoes_gerais ORDER BY categoria", fetch='all')
        categorias_db = [row['categoria'] for row in rows] if rows else []
        categorias_fixas = ['bypass', 'malha', 'condicao', 'motivador', 'midia', 'telecontrolado', 'manobra_efetiva', 'vinculado_acessante', 'alimentador', 'tensao_kv_rede']
        return sorted(list(set(categorias_db + categorias_fixas)))
        
    def get_opcoes_por_categoria_geral(self, categoria):
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
        if id_pai is None: return self._execute("SELECT * FROM opcoes_hierarquicas WHERE id_pai IS NULL ORDER BY id", fetch='all')
        else: return self._execute("SELECT * FROM opcoes_hierarquicas WHERE id_pai = ? ORDER BY id", (id_pai,), fetch='all')
        
    def adicionar_opcao_hierarquica(self, categoria, valor, id_pai=None):
        self._execute("INSERT INTO opcoes_hierarquicas (categoria, valor, id_pai) VALUES (?, ?, ?)", (categoria, valor, id_pai), commit=True)
        
    def editar_opcao_hierarquica(self, id_opcao, novo_valor):
        self._execute("UPDATE opcoes_hierarquicas SET valor = ? WHERE id = ?", (novo_valor, id_opcao), commit=True)
        
    def deletar_opcao_hierarquica(self, id_opcao):
        self._execute("DELETE FROM opcoes_hierarquicas WHERE id = ?", (id_opcao,), commit=True)
        
    def get_todos_cabos(self):
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
        self.save_record(data_dict, 'cadastros')
        
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

    def buscar_todos_registros_para_visualizacao(self, filters):
        query = "SELECT id, eqpto, malha, alimentador, ns, condição, fabricante, mídia, data_registro FROM cadastros"
        condicoes, params = [], []
        for campo, valor in filters.items():
            if valor:
                condicoes.append(f"{campo} LIKE ?")
                params.append(f"%{valor}%")
        if condicoes:
            query += " WHERE " + " AND ".join(condicoes)
        query += " ORDER BY eqpto ASC, data_registro DESC"
        return self._execute(query, tuple(params), fetch='all')
        
    def get_recent_equipments_with_status(self, limit=50):
        # Query reescrita para diferenciar status de versões antigas e novas
        query = """
        WITH RankedCadastros AS (
            SELECT 
                *,
                ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn
            FROM cadastros
            WHERE eqpto != ''
        )
        SELECT
            rc.eqpto,
            rc.ns,
            rc.data,
            rc.data_registro,
            rc.alimentador,
            CASE 
                WHEN rc.rn = 1 THEN COALESCE(a.status, latest_h.status, 'Pendente')
                ELSE latest_h.status
            END as status
        FROM
            RankedCadastros rc
        LEFT JOIN 
            ajustes a ON rc.eqpto = a.eqpto
        LEFT JOIN 
            (SELECT eqpto, status, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_conclusao DESC) as rn 
             FROM historico_ajustes) latest_h ON rc.eqpto = latest_h.eqpto AND latest_h.rn = 1
        ORDER BY
            rc.data_registro DESC
        LIMIT ?
        """
        return self._execute(query, (limit,), fetch='all')
        
    def get_all_draft_equipments(self):
        return self._execute("SELECT eqpto, ns, data, alimentador FROM rascunhos WHERE eqpto != '' ORDER BY data_registro DESC", fetch='all')
        
    def delete_drafts(self, eqpto_list):
        params = [(eq,) for eq in eqpto_list]
        self._execute("DELETE FROM rascunhos WHERE eqpto = ?", params, commit=True, executemany=True)
        
    def get_pending_adjustments(self):
        query = """
        SELECT 
            a.eqpto, a.status, c.autor, c.data_registro, c.malha, 
            c.alimentador, c.fabricante, c.comando 
        FROM ajustes a 
        JOIN 
            (SELECT *, ROW_NUMBER() OVER(PARTITION BY eqpto ORDER BY data_registro DESC) as rn FROM cadastros) c 
            ON a.eqpto = c.eqpto 
        WHERE c.rn = 1 
        ORDER BY a.data_adicao DESC
        """
        return self._execute(query, fetch='all')
        
    def complete_adjustment(self, eqpto, status):
        self._execute("INSERT INTO historico_ajustes (eqpto, status) VALUES (?, ?)", (eqpto, status), commit=True)
        self._execute("DELETE FROM ajustes WHERE eqpto = ?", (eqpto,), commit=True)
        
    def update_adjustment_status(self, eqpto_list, status):
        params = [(status, eq,) for eq in eqpto_list]
        self._execute("UPDATE ajustes SET status = ? WHERE eqpto = ?", params, commit=True, executemany=True)
        
    def get_adjustments_history(self, limit=100):
        return self._execute("SELECT eqpto, data_conclusao, status FROM historico_ajustes ORDER BY data_conclusao DESC LIMIT ?", (limit,), fetch='all')
        
    def deletar_mapeamento(self, map_id):
        self._execute("DELETE FROM mapeamento_excel WHERE id = ?", (map_id,), commit=True)
        
    def deletar_todos_mapeamentos(self):
        self._execute("DELETE FROM mapeamento_excel", commit=True)
