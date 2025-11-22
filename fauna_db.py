"""
Modulo per la gestione del database fauna
Gestisce la connessione e le operazioni CRUD per fauna_table
"""

import sqlite3
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class FaunaDB:
    """Classe per gestire le operazioni sul database fauna"""

    def __init__(self, db_path: str = None):
        """
        Inizializza la connessione al database

        Args:
            db_path: percorso del database. Se None, usa il database di pyarchinit
        """
        if db_path is None:
            # Percorso predefinito al database pyarchinit
            home = os.path.expanduser("~")
            db_path = os.path.join(home, "pyarchinit", "pyarchinit_DB_folder", "pyarchinit_db.sqlite")

        self.db_path = db_path
        self.conn = None
        self.connect()
        self.ensure_tables_exist()

    def connect(self):
        """Stabilisce la connessione al database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Per accedere ai campi per nome
        except sqlite3.Error as e:
            raise Exception(f"Errore nella connessione al database: {e}")

    def ensure_tables_exist(self):
        """Verifica che le tabelle fauna esistano, altrimenti le crea"""
        cursor = self.conn.cursor()

        try:
            # Verifica se fauna_table esiste
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='fauna_table'
            """)

            fauna_exists = cursor.fetchone() is not None

            # Verifica se fauna_voc esiste
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='fauna_voc'
            """)

            voc_exists = cursor.fetchone() is not None

            if not fauna_exists or not voc_exists:
                print("⚠ Tabelle fauna non trovate nel database")
                print("📦 Creazione tabelle in corso...")

                # Crea le tabelle eseguendo gli script SQL
                script_dir = os.path.dirname(os.path.abspath(__file__))
                sql_dir = os.path.join(script_dir, "sql")

                # Crea fauna_voc prima
                if not voc_exists:
                    voc_sql_path = os.path.join(sql_dir, "create_fauna_voc.sql")
                    if os.path.exists(voc_sql_path):
                        print("  → Creazione tabella fauna_voc...")
                        with open(voc_sql_path, 'r', encoding='utf-8') as f:
                            cursor.executescript(f.read())
                        print("  ✓ Tabella fauna_voc creata")
                    else:
                        print(f"  ✗ File SQL non trovato: {voc_sql_path}")

                # Crea fauna_table
                if not fauna_exists:
                    table_sql_path = os.path.join(sql_dir, "create_fauna_table.sql")
                    if os.path.exists(table_sql_path):
                        print("  → Creazione tabella fauna_table...")
                        with open(table_sql_path, 'r', encoding='utf-8') as f:
                            cursor.executescript(f.read())
                        print("  ✓ Tabella fauna_table creata")
                    else:
                        print(f"  ✗ File SQL non trovato: {table_sql_path}")

                self.conn.commit()
                print("✅ Tabelle fauna create con successo!")

            else:
                print("✓ Tabelle fauna già presenti nel database")

        except Exception as e:
            print(f"❌ Errore nella verifica/creazione tabelle: {e}")
            import traceback
            traceback.print_exc()
            # Non sollevare eccezione per permettere all'app di continuare
            # L'utente vedrà l'errore ma potrà comunque provare a connettersi

    def get_us_list(self, sito: str = None) -> List[Dict]:
        """
        Recupera la lista delle US dal database

        Args:
            sito: filtro opzionale per sito

        Returns:
            Lista di dizionari con i dati US
        """
        cursor = self.conn.cursor()

        if sito:
            cursor.execute("""
                SELECT id_us, sito, area, us, saggio, datazione
                FROM us_table
                WHERE sito = ?
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
        """
        Recupera i dati di una US specifica

        Args:
            id_us: ID della US

        Returns:
            Dizionario con i dati US o None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id_us, sito, area, us, saggio, datazione
            FROM us_table
            WHERE id_us = ?
        """, (id_us,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_voc_values(self, campo: str) -> List[str]:
        """
        Recupera i valori del vocabolario controllato per un campo

        Args:
            campo: nome del campo

        Returns:
            Lista di valori
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT valore
            FROM fauna_voc
            WHERE campo = ? AND attivo = 1
            ORDER BY ordinamento, valore
        """, (campo,))

        return [row[0] for row in cursor.fetchall()]

    def get_all_fauna_records(self, filters: Dict = None) -> List[Dict]:
        """
        Recupera tutti i record fauna, con filtri opzionali

        Args:
            filters: dizionario con filtri (es. {'sito': 'Pompei', 'contesto': 'FUNERARIO'})

        Returns:
            Lista di dizionari con i record
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM fauna_table"
        params = []

        if filters:
            where_clauses = []
            for field, value in filters.items():
                if value:
                    where_clauses.append(f"{field} = ?")
                    params.append(value)

            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY sito, area, us, id_fauna"

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_fauna_record(self, id_fauna: int) -> Optional[Dict]:
        """
        Recupera un singolo record fauna

        Args:
            id_fauna: ID del record

        Returns:
            Dizionario con i dati o None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM fauna_table WHERE id_fauna = ?", (id_fauna,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def insert_fauna_record(self, data: Dict) -> int:
        """
        Inserisce un nuovo record fauna

        Args:
            data: dizionario con i dati del record

        Returns:
            ID del record inserito
        """
        # Rimuovi id_fauna se presente (viene auto-generato)
        data = data.copy()
        data.pop('id_fauna', None)

        fields = list(data.keys())
        placeholders = ['?' for _ in fields]
        values = [data[f] for f in fields]

        query = f"""
            INSERT INTO fauna_table ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
        """

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        self.conn.commit()

        return cursor.lastrowid

    def update_fauna_record(self, id_fauna: int, data: Dict) -> bool:
        """
        Aggiorna un record fauna esistente

        Args:
            id_fauna: ID del record da aggiornare
            data: dizionario con i nuovi dati

        Returns:
            True se l'aggiornamento ha successo
        """
        # Rimuovi id_fauna dai dati da aggiornare
        data = data.copy()
        data.pop('id_fauna', None)

        fields = list(data.keys())
        set_clause = ', '.join([f"{f} = ?" for f in fields])
        values = [data[f] for f in fields]
        values.append(id_fauna)

        query = f"UPDATE fauna_table SET {set_clause} WHERE id_fauna = ?"

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        self.conn.commit()

        return cursor.rowcount > 0

    def delete_fauna_record(self, id_fauna: int) -> bool:
        """
        Elimina un record fauna

        Args:
            id_fauna: ID del record da eliminare

        Returns:
            True se l'eliminazione ha successo
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM fauna_table WHERE id_fauna = ?", (id_fauna,))
        self.conn.commit()

        return cursor.rowcount > 0

    def delete_multiple_fauna_records(self, id_list: List[int]) -> int:
        """
        Elimina multipli record fauna

        Args:
            id_list: lista di ID dei record da eliminare

        Returns:
            Numero di record eliminati
        """
        if not id_list:
            return 0

        placeholders = ','.join(['?' for _ in id_list])
        query = f"DELETE FROM fauna_table WHERE id_fauna IN ({placeholders})"

        cursor = self.conn.cursor()
        cursor.execute(query, id_list)
        self.conn.commit()

        return cursor.rowcount

    def search_fauna_records(self, search_term: str, fields: List[str] = None) -> List[Dict]:
        """
        Cerca record fauna in base a un termine di ricerca

        Args:
            search_term: termine da cercare
            fields: lista di campi in cui cercare. Se None, cerca in tutti i campi testo

        Returns:
            Lista di record trovati
        """
        if not search_term:
            return self.get_all_fauna_records()

        if fields is None:
            fields = [
                'sito', 'area', 'us', 'saggio', 'responsabile_scheda',
                'contesto', 'specie', 'descrizione_contesto', 'osservazioni',
                'interpretazione'
            ]

        cursor = self.conn.cursor()

        where_clauses = [f"{field} LIKE ?" for field in fields]
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
        cursor.execute("SELECT DISTINCT sito FROM us_table WHERE sito IS NOT NULL ORDER BY sito")
        return [row[0] for row in cursor.fetchall()]

    def close(self):
        """Chiude la connessione al database"""
        if self.conn:
            self.conn.close()