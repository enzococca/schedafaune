"""
Gestione configurazione database
Salva e carica l'ultima configurazione utilizzata
"""

import json
import os
from typing import Dict, Optional


class DBConfigManager:
    """Gestisce il salvataggio e il caricamento della configurazione del database"""

    # CONFIGURAZIONE SICUREZZA
    # Cambia questo a True se vuoi salvare anche la password PostgreSQL
    # ATTENZIONE: La password sarà salvata in chiaro nel file di configurazione!
    SAVE_PASSWORD = True

    def __init__(self, config_file: str = None):
        """
        Inizializza il manager

        Args:
            config_file: percorso del file di configurazione
        """
        if config_file is None:
            # Usa file nella home dell'utente
            home = os.path.expanduser("~")
            config_dir = os.path.join(home, ".pyarchinit")

            # Crea directory se non esiste
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            config_file = os.path.join(config_dir, "fauna_db_config.json")

        self.config_file = config_file

    def save_config(self, db_config: Dict):
        """
        Salva la configurazione del database

        Args:
            db_config: dizionario con la configurazione
        """
        try:
            config_to_save = db_config.copy()

            # Gestione password in base alla configurazione di sicurezza
            if not self.SAVE_PASSWORD and 'password' in config_to_save:
                config_to_save['password'] = ''
                if config_to_save.get('type') == 'postgres':
                    print("ℹ Password PostgreSQL non salvata (per sicurezza)")
                    print("  Se vuoi salvarla, modifica SAVE_PASSWORD = True in db_config_manager.py")

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)

            print(f"✓ Configurazione salvata in: {self.config_file}")

        except Exception as e:
            print(f"⚠ Impossibile salvare configurazione: {e}")

    def load_config(self) -> Optional[Dict]:
        """
        Carica l'ultima configurazione salvata

        Returns:
            Dizionario con la configurazione o None
        """
        try:
            if not os.path.exists(self.config_file):
                return None

            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            print(f"✓ Configurazione caricata da: {self.config_file}")
            return config

        except Exception as e:
            print(f"⚠ Impossibile caricare configurazione: {e}")
            return None

    def get_default_config(self) -> Dict:
        """
        Restituisce la configurazione predefinita

        Returns:
            Dizionario con la configurazione predefinita
        """
        home = os.path.expanduser("~")
        default_sqlite = os.path.join(home, "pyarchinit", "pyarchinit_DB_folder", "pyarchinit_db.sqlite")

        return {
            'type': 'sqlite',
            'path': default_sqlite
        }
