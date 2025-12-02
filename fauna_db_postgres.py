"""
Implementazione PostgreSQL per FaunaDB
Estende FaunaDB con supporto PostgreSQL
"""

import os
from typing import List, Dict, Optional
from datetime import datetime


class FaunaDBPostgres:
    """Classe per gestire le operazioni sul database fauna con PostgreSQL"""

    def __init__(self, db_config: Dict):
        """
        Inizializza la connessione al database PostgreSQL

        Args:
            db_config: dict con host, port, database, user, password
        """
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            self.psycopg2 = psycopg2
            self.RealDictCursor = RealDictCursor
        except ImportError:
            raise ImportError(
                "Il modulo psycopg2 è richiesto per PostgreSQL.\n"
                "Installare con: pip install psycopg2-binary"
            )

        self.db_config = db_config
        self.conn = None

        # Prima connetti (può fallire con errore password)
        self.connect()

        # Solo se la connessione ha successo, verifica/crea le tabelle
        if self.conn:
            self.ensure_tables_exist()

    def connect(self):
        """Stabilisce la connessione al database PostgreSQL"""
        try:
            self.conn = self.psycopg2.connect(
                host=self.db_config.get('host', 'localhost'),
                port=self.db_config.get('port', 5432),
                database=self.db_config.get('database', 'pyarchinit'),
                user=self.db_config.get('user', 'postgres'),
                password=self.db_config.get('password', ''),
                cursor_factory=self.RealDictCursor
            )
            # IMPORTANTE: Usa autocommit=True per operazioni DDL (CREATE TABLE, CREATE INDEX)
            # Le operazioni DDL in PostgreSQL devono essere committate immediatamente
            self.conn.autocommit = True
        except Exception as e:
            raise Exception(f"Errore nella connessione a PostgreSQL: {e}")

    def verify_table_exists(self, table_name: str) -> bool:
        """Verifica che una tabella esista nel database"""
        cursor = self.conn.cursor()
        # Usa pg_catalog invece di information_schema per vedere immediatamente i cambiamenti DDL
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM pg_catalog.pg_tables
                WHERE schemaname = 'public' AND tablename = %s
            ) as exists
        """, (table_name,))
        result = cursor.fetchone()
        return result['exists'] if result else False

    def drop_table_if_exists(self, table_name: str):
        """Elimina una tabella se esiste (per cleanup)"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            print(f"    🗑 Tabella {table_name} eliminata (cleanup)")
        except Exception as e:
            print(f"    ⚠ Errore eliminazione {table_name}: {e}")

    def ensure_tables_exist(self):
        """Verifica che le tabelle fauna esistano, altrimenti le crea"""
        if not self.conn:
            return

        cursor = self.conn.cursor()

        try:
            # Verifica se fauna_table esiste
            fauna_exists = self.verify_table_exists('fauna_table')

            # Verifica se fauna_voc esiste
            voc_exists = self.verify_table_exists('fauna_voc')

            if not fauna_exists or not voc_exists:
                print("⚠ Tabelle fauna non trovate nel database PostgreSQL")
                print("📦 Creazione tabelle in corso...")

                # Cleanup: elimina eventuali tabelle parzialmente create
                if not voc_exists:
                    self.drop_table_if_exists('fauna_voc')
                if not fauna_exists:
                    self.drop_table_if_exists('fauna_table')

                # Crea le tabelle eseguendo gli script SQL
                script_dir = os.path.dirname(os.path.abspath(__file__))
                sql_dir = os.path.join(script_dir, "sql")

                # Crea fauna_voc prima
                if not voc_exists:
                    voc_sql_path = os.path.join(sql_dir, "create_fauna_voc.sql")
                    if os.path.exists(voc_sql_path):
                        print("  → Creazione tabella fauna_voc...")
                        with open(voc_sql_path, 'r', encoding='utf-8') as f:
                            sql = f.read()

                            # PRIMA: Rimuovi i commenti SQL (linee che iniziano con --)
                            # Mantieni solo le linee che non sono commenti puri
                            lines = sql.split('\n')
                            clean_lines = []
                            for line in lines:
                                stripped = line.strip()
                                # Salta linee vuote o linee che sono solo commenti
                                if stripped and not stripped.startswith('--'):
                                    # Rimuovi commenti in-line (es: "campo TEXT, -- commento")
                                    # Ma attenzione a non rimuovere -- dentro stringhe!
                                    # Per ora rimuoviamo semplicemente tutto dopo --
                                    line_without_comment = line.split('--')[0]
                                    clean_lines.append(line_without_comment)

                            sql = '\n'.join(clean_lines)

                            # POI: Adatta sintassi per PostgreSQL
                            sql = sql.replace('AUTOINCREMENT', 'GENERATED ALWAYS AS IDENTITY')
                            sql = sql.replace('CREATE TABLE IF NOT EXISTS', 'CREATE TABLE')
                            sql = sql.replace('INSERT OR IGNORE INTO', 'INSERT INTO')
                            # PostgreSQL richiede TRUE/FALSE per BOOLEAN, non 1/0
                            sql = sql.replace('BOOLEAN DEFAULT 1', 'BOOLEAN DEFAULT TRUE')
                            sql = sql.replace('BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE')

                            # Aggiungi ON CONFLICT DO NOTHING prima di ogni punto e virgola che segue un INSERT
                            import re
                            sql = re.sub(
                                r'(\bINSERT INTO fauna_voc\b[^;]+);',
                                r'\1 ON CONFLICT (campo, valore) DO NOTHING;',
                                sql
                            )

                            # Separa in 3 categorie: CREATE TABLE, INSERT, CREATE INDEX
                            create_table_statements = []
                            insert_statements = []
                            create_index_statements = []

                            statements = sql.split(';')
                            print(f"    📋 Trovati {len(statements)} statement totali")

                            # Debug: stampa il primo statement completo
                            if len(statements) > 0:
                                first_stmt = statements[0].strip()
                                print(f"    🔍 Primo statement (primi 500 char):\n{first_stmt[:500]}\n")

                            for i, statement in enumerate(statements):
                                statement = statement.strip()
                                if not statement:
                                    print(f"    ⏭ Statement {i}: vuoto, skip")
                                    continue

                                # Debug: mostra primi 100 caratteri di ogni statement
                                preview = statement[:100].replace('\n', ' ')
                                print(f"    🔍 Statement {i}: {preview}...")

                                if 'CREATE TABLE' in statement:
                                    create_table_statements.append(statement)
                                    print(f"    ➕ Aggiunto CREATE TABLE (lunghezza: {len(statement)})")
                                elif 'CREATE INDEX' in statement:
                                    create_index_statements.append(statement)
                                    print(f"    ➕ Aggiunto CREATE INDEX")
                                elif 'INSERT INTO' in statement:
                                    insert_statements.append(statement)
                                    print(f"    ➕ Aggiunto INSERT INTO")
                                else:
                                    print(f"    ❓ Statement {i} non riconosciuto")

                            print(f"    📊 Totali: {len(create_table_statements)} CREATE TABLE, {len(insert_statements)} INSERT, {len(create_index_statements)} CREATE INDEX")

                            # 1. Prima esegui CREATE TABLE
                            for statement in create_table_statements:
                                try:
                                    # Debug: mostra i primi 200 caratteri dello statement
                                    print(f"    🔧 Esecuzione CREATE TABLE: {statement[:200]}...")
                                    cursor.execute(statement)
                                    print(f"    ✓ CREATE TABLE eseguito senza errori")
                                except Exception as e:
                                    print(f"    ❌ ERRORE durante CREATE TABLE: {e}")
                                    print(f"    📝 Statement completo:\n{statement}")
                                    if 'already exists' not in str(e).lower():
                                        raise

                            # Con autocommit=True non serve commit esplicito
                            print("    ✓ Tabella creata (autocommit)")

                            # VERIFICA IMMEDIATA che la tabella esista davvero
                            print("    🔍 Verifica esistenza tabella fauna_voc...")

                            # Debug: verifica manualmente con un cursore fresco
                            verify_cursor = self.conn.cursor()
                            verify_cursor.execute("""
                                SELECT COUNT(*) as count
                                FROM pg_catalog.pg_tables
                                WHERE schemaname = 'public' AND tablename = 'fauna_voc'
                            """)
                            count_result = verify_cursor.fetchone()
                            print(f"    📊 Query pg_tables restituisce: {count_result}")

                            if self.verify_table_exists('fauna_voc'):
                                print("    ✓✓ Tabella fauna_voc verificata nel database")
                            else:
                                print("    ✗✗ ERRORE: Tabella fauna_voc NON TROVATA dopo commit!")

                                # Debug aggiuntivo: proviamo a fare SELECT sulla tabella
                                try:
                                    test_cursor = self.conn.cursor()
                                    test_cursor.execute("SELECT COUNT(*) FROM fauna_voc")
                                    print(f"    🤔 Ma SELECT COUNT(*) sulla tabella funziona! Risultato: {test_cursor.fetchone()}")
                                except Exception as e:
                                    print(f"    ❌ SELECT sulla tabella fallisce: {e}")

                                raise Exception("Tabella fauna_voc non creata correttamente")

                            # Nuovo cursore dopo commit
                            cursor = self.conn.cursor()

                            # 2. Poi esegui INSERT
                            for statement in insert_statements:
                                try:
                                    cursor.execute(statement)
                                except Exception as e:
                                    if 'duplicate' not in str(e).lower() and 'already exists' not in str(e).lower():
                                        print(f"    Attenzione INSERT: {e}")

                            # Con autocommit=True non serve commit esplicito
                            print("    ✓ Dati inseriti (autocommit)")

                            # Nuovo cursore
                            cursor = self.conn.cursor()

                            # 3. Infine crea gli indici (ognuno in una transazione separata)
                            # Ma solo se la tabella esiste davvero
                            if self.verify_table_exists('fauna_voc'):
                                for statement in create_index_statements:
                                    try:
                                        cursor.execute(statement)
                                        # Con autocommit=True ogni statement è già committato
                                    except Exception as e:
                                        if 'already exists' not in str(e).lower():
                                            print(f"    Attenzione INDEX: {e}")

                                print("    ✓ Indici creati (autocommit)")
                            else:
                                print("    ⚠ Indici non creati (tabella non verificata)")

                        print("  ✓ Tabella fauna_voc creata")
                    else:
                        print(f"  ✗ File SQL non trovato: {voc_sql_path}")

                # Crea fauna_table
                if not fauna_exists:
                    table_sql_path = os.path.join(sql_dir, "create_fauna_table.sql")
                    if os.path.exists(table_sql_path):
                        print("  → Creazione tabella fauna_table...")
                        with open(table_sql_path, 'r', encoding='utf-8') as f:
                            sql = f.read()

                            # PRIMA: Rimuovi i commenti SQL
                            lines = sql.split('\n')
                            clean_lines = []
                            for line in lines:
                                stripped = line.strip()
                                if stripped and not stripped.startswith('--'):
                                    line_without_comment = line.split('--')[0]
                                    clean_lines.append(line_without_comment)

                            sql = '\n'.join(clean_lines)

                            # POI: Adatta sintassi per PostgreSQL
                            sql = sql.replace('AUTOINCREMENT', 'GENERATED ALWAYS AS IDENTITY')
                            sql = sql.replace('CREATE TABLE IF NOT EXISTS', 'CREATE TABLE')
                            sql = sql.replace('NUMERIC (6, 2)', 'NUMERIC(6, 2)')
                            # PostgreSQL richiede TRUE/FALSE per BOOLEAN, non 1/0
                            sql = sql.replace('BOOLEAN DEFAULT 1', 'BOOLEAN DEFAULT TRUE')
                            sql = sql.replace('BOOLEAN DEFAULT 0', 'BOOLEAN DEFAULT FALSE')

                            # Separa in 3 categorie come per fauna_voc
                            create_table_statements = []
                            create_index_statements = []

                            statements = sql.split(';')
                            for statement in statements:
                                statement = statement.strip()
                                if not statement or statement.startswith('--'):
                                    continue

                                if 'CREATE TABLE' in statement:
                                    create_table_statements.append(statement)
                                elif 'CREATE INDEX' in statement:
                                    create_index_statements.append(statement)

                            # 1. Prima esegui CREATE TABLE
                            for statement in create_table_statements:
                                try:
                                    cursor.execute(statement)
                                except Exception as e:
                                    if 'already exists' not in str(e).lower():
                                        print(f"    Errore CREATE TABLE: {e}")
                                        raise

                            # Con autocommit=True non serve commit esplicito
                            print("    ✓ Tabella creata (autocommit)")

                            # VERIFICA IMMEDIATA che la tabella esista davvero
                            if self.verify_table_exists('fauna_table'):
                                print("    ✓✓ Tabella fauna_table verificata nel database")
                            else:
                                print("    ✗✗ ERRORE: Tabella fauna_table NON TROVATA dopo autocommit!")
                                raise Exception("Tabella fauna_table non creata correttamente")

                            # Nuovo cursore
                            cursor = self.conn.cursor()

                            # 2. Crea gli indici
                            # Ma solo se la tabella esiste davvero
                            if self.verify_table_exists('fauna_table'):
                                for statement in create_index_statements:
                                    try:
                                        cursor.execute(statement)
                                        # Con autocommit=True ogni statement è già committato
                                    except Exception as e:
                                        if 'already exists' not in str(e).lower():
                                            print(f"    Attenzione INDEX: {e}")

                                print("    ✓ Indici creati (autocommit)")
                            else:
                                print("    ⚠ Indici non creati (tabella non verificata)")

                        print("  ✓ Tabella fauna_table creata")
                    else:
                        print(f"  ✗ File SQL non trovato: {table_sql_path}")

                print("✅ Tabelle fauna create con successo nel database PostgreSQL!")

            else:
                print("✓ Tabelle fauna già presenti nel database PostgreSQL")

        except Exception as e:
            # Con autocommit=True non serve rollback
            print(f"❌ Errore nella verifica/creazione tabelle PostgreSQL: {e}")
            import traceback
            traceback.print_exc()
            # Non sollevare eccezione per permettere all'app di continuare

    def get_us_list(self, sito: str = None) -> List[Dict]:
        """Recupera la lista delle US dal database"""
        cursor = self.conn.cursor()

        if sito:
            cursor.execute("""
                SELECT id_us, sito, area, us, saggio, datazione
                FROM us_table
                WHERE sito = %s
                ORDER BY sito, area, us
            """, (sito,))
        else:
            cursor.execute("""
                SELECT id_us, sito, area, us, saggio, datazione
                FROM us_table
                ORDER BY sito, area, us
            """)

        return [dict(row) for row in cursor.fetchall()]

    def get_us_by_id(self, id_us: int) -> Optional[Dict]:
        """Recupera i dati di una US specifica"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id_us, sito, area, us, saggio, datazione
            FROM us_table
            WHERE id_us = %s
        """, (id_us,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_voc_values(self, campo: str) -> List[str]:
        """Recupera i valori del vocabolario controllato"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT valore
            FROM fauna_voc
            WHERE campo = %s AND attivo = TRUE
            ORDER BY ordinamento, valore
        """, (campo,))

        return [row['valore'] for row in cursor.fetchall()]

    def get_all_fauna_records(self, filters: Dict = None) -> List[Dict]:
        """Recupera tutti i record fauna"""
        cursor = self.conn.cursor()

        query = "SELECT * FROM fauna_table"
        params = []

        if filters:
            where_clauses = []
            for field, value in filters.items():
                if value:
                    where_clauses.append(f"{field} = %s")
                    params.append(value)

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY sito, area, us, id_fauna"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_fauna_record(self, id_fauna: int) -> Optional[Dict]:
        """Recupera un singolo record fauna"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM fauna_table WHERE id_fauna = %s", (id_fauna,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def insert_fauna_record(self, data: Dict) -> int:
        """Inserisce un nuovo record fauna"""
        data = data.copy()
        data.pop('id_fauna', None)

        fields = list(data.keys())
        placeholders = ['%s' for _ in fields]
        values = [data[f] for f in fields]

        query = f"""
            INSERT INTO fauna_table ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
            RETURNING id_fauna
        """

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        new_id = cursor.fetchone()['id_fauna']
        # autocommit=True committò automaticamente

        return new_id

    def update_fauna_record(self, id_fauna: int, data: Dict) -> bool:
        """Aggiorna un record fauna esistente"""
        data = data.copy()
        data.pop('id_fauna', None)

        fields = list(data.keys())
        set_clause = ', '.join([f"{f} = %s" for f in fields])
        values = [data[f] for f in fields]
        values.append(id_fauna)

        query = f"UPDATE fauna_table SET {set_clause} WHERE id_fauna = %s"

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        # autocommit=True committa automaticamente

        return cursor.rowcount > 0

    def delete_fauna_record(self, id_fauna: int) -> bool:
        """Elimina un record fauna"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM fauna_table WHERE id_fauna = %s", (id_fauna,))
        # autocommit=True committa automaticamente

        return cursor.rowcount > 0

    def delete_multiple_fauna_records(self, id_list: List[int]) -> int:
        """Elimina multipli record fauna"""
        if not id_list:
            return 0

        placeholders = ','.join(['%s' for _ in id_list])
        query = f"DELETE FROM fauna_table WHERE id_fauna IN ({placeholders})"

        cursor = self.conn.cursor()
        cursor.execute(query, id_list)
        # autocommit=True committa automaticamente

        return cursor.rowcount

    def search_fauna_records(self, search_term: str, fields: List[str] = None) -> List[Dict]:
        """Cerca record fauna"""
        if not search_term:
            return self.get_all_fauna_records()

        if fields is None:
            fields = [
                'sito', 'area', 'us', 'saggio', 'responsabile_scheda',
                'contesto', 'specie', 'descrizione_contesto', 'osservazioni',
                'interpretazione'
            ]

        cursor = self.conn.cursor()

        where_clauses = [f"{field}::text ILIKE %s" for field in fields]
        query = f"""
            SELECT * FROM fauna_table
            WHERE {' OR '.join(where_clauses)}
            ORDER BY sito, area, us, id_fauna
        """

        search_pattern = f"%{search_term}%"
        params = [search_pattern for _ in fields]

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_siti_list(self) -> List[str]:
        """Recupera la lista dei siti"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT sito
            FROM us_table
            WHERE sito IS NOT NULL
            ORDER BY sito
        """)
        return [row['sito'] for row in cursor.fetchall()]

    def get_aree_list(self, sito: str = None) -> List[str]:
        """
        Recupera la lista delle aree distinte

        Args:
            sito: filtro opzionale per sito

        Returns:
            Lista di aree distinte
        """
        cursor = self.conn.cursor()
        if sito:
            cursor.execute("""
                SELECT DISTINCT area FROM us_table
                WHERE sito = %s AND area IS NOT NULL
                ORDER BY area
            """, (sito,))
        else:
            cursor.execute("""
                SELECT DISTINCT area FROM us_table
                WHERE area IS NOT NULL
                ORDER BY area
            """)
        return [row['area'] for row in cursor.fetchall()]

    def get_saggi_list(self, sito: str = None, area: str = None) -> List[str]:
        """
        Recupera la lista dei saggi distinti

        Args:
            sito: filtro opzionale per sito
            area: filtro opzionale per area

        Returns:
            Lista di saggi distinti
        """
        cursor = self.conn.cursor()
        conditions = ["saggio IS NOT NULL"]
        params = []

        if sito:
            conditions.append("sito = %s")
            params.append(sito)
        if area:
            conditions.append("area = %s")
            params.append(area)

        query = f"""
            SELECT DISTINCT saggio FROM us_table
            WHERE {' AND '.join(conditions)}
            ORDER BY saggio
        """
        cursor.execute(query, params)
        return [row['saggio'] for row in cursor.fetchall()]

    def get_us_values_list(self, sito: str = None, area: str = None) -> List[str]:
        """
        Recupera la lista dei valori US distinti

        Args:
            sito: filtro opzionale per sito
            area: filtro opzionale per area

        Returns:
            Lista di valori US distinti
        """
        cursor = self.conn.cursor()
        conditions = ["us IS NOT NULL"]
        params = []

        if sito:
            conditions.append("sito = %s")
            params.append(sito)
        if area:
            conditions.append("area = %s")
            params.append(area)

        query = f"""
            SELECT DISTINCT us FROM us_table
            WHERE {' AND '.join(conditions)}
            ORDER BY us
        """
        cursor.execute(query, params)
        return [row['us'] for row in cursor.fetchall()]

    def close(self):
        """Chiude la connessione al database"""
        if self.conn:
            self.conn.close()
