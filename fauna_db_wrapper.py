"""
Wrapper per FaunaDB che supporta sia SQLite che PostgreSQL
"""

import os
from typing import Dict, Optional
from fauna_db import FaunaDB


def create_fauna_db(db_path: str = None, db_config: Dict = None):
    """
    Factory function per creare l'istanza corretta di FaunaDB

    Args:
        db_path: percorso database SQLite (deprecato, usa db_config)
        db_config: configurazione database
            Per SQLite: {'type': 'sqlite', 'path': '/path/to/db.sqlite'}
            Per PostgreSQL: {'type': 'postgres', 'host': 'localhost', 'port': 5432,
                            'database': 'pyarchinit', 'user': 'postgres', 'password': '...'}

    Returns:
        Istanza di FaunaDB o FaunaDBPostgres
    """
    # Se viene passato db_path, crea config SQLite
    if db_path is not None and db_config is None:
        db_config = {
            'type': 'sqlite',
            'path': db_path
        }

    # Se nessuna config, usa default SQLite
    if db_config is None:
        home = os.path.expanduser("~")
        db_path = os.path.join(home, "pyarchinit", "pyarchinit_DB_folder", "pyarchinit_db.sqlite")
        db_config = {
            'type': 'sqlite',
            'path': db_path
        }

    # Crea l'istanza appropriata
    if db_config['type'] == 'sqlite':
        return FaunaDB(db_config['path'])
    elif db_config['type'] == 'postgres':
        from fauna_db_postgres import FaunaDBPostgres
        return FaunaDBPostgres(db_config)
    else:
        raise ValueError(f"Tipo database non supportato: {db_config['type']}")
