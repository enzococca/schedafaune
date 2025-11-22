"""
Script per integrare Fauna Manager con QGIS
Può essere usato come Action nelle proprietà del layer o come standalone
"""

import os
import sys

# Aggiunge il percorso corrente al PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from qgis.PyQt.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox
    from qgis.PyQt.QtCore import Qt
    from qgis.core import QgsProject
    from qgis.utils import iface
    QGIS_AVAILABLE = True
except ImportError:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox
    from PyQt5.QtCore import Qt
    QGIS_AVAILABLE = False
    iface = None

from fauna_manager import FaunaManager
from database_selector import DatabaseSelectorDialog
from db_config_manager import DBConfigManager

# IMPORTANTE: Variabile globale per mantenere la finestra in memoria
# Senza questo, la finestra viene garbage-collected in QGIS
_fauna_window = None


class FaunaQGISIntegration:
    """Classe per integrare Fauna Manager con QGIS"""

    def __init__(self, iface=None):
        """
        Inizializza l'integrazione

        Args:
            iface: interfaccia di QGIS (opzionale)
        """
        self.iface = iface
        self.fauna_manager = None
        self.window = None

    def open_fauna_manager(self, db_path=None, db_config=None):
        """
        Apre l'interfaccia Fauna Manager

        Args:
            db_path: percorso del database (opzionale)
            db_config: configurazione database (opzionale)
        """
        global _fauna_window

        try:
            # Se db_config non è fornito, prova a caricare l'ultima configurazione
            if db_config is None and db_path is None:
                config_manager = DBConfigManager()
                saved_config = config_manager.load_config()

                if saved_config:
                    print("📂 Caricamento ultima configurazione database...")
                    db_config = saved_config
                else:
                    # Nessuna configurazione salvata, mostra il dialog
                    print("📝 Nessuna configurazione salvata, mostra dialog di selezione...")
                    db_config = self.select_database()
                    if db_config is None:
                        # Utente ha annullato
                        return

            # Tenta di creare il widget con retry in caso di errore
            try:
                self.fauna_manager = FaunaManager(db_path=db_path, db_config=db_config)
            except Exception as conn_error:
                # Errore di connessione - mostra dialog per reinserire i dati
                print(f"⚠ Errore connessione database: {conn_error}")
                print("📝 Richiesta nuova configurazione database...")

                # Determina il messaggio di errore
                error_short = str(conn_error)
                if "no password supplied" in error_short:
                    retry_msg = "Password mancante. Inserisci la password PostgreSQL per continuare."
                elif "authentication failed" in error_short:
                    retry_msg = "Autenticazione fallita. Verifica username e password."
                elif "could not connect" in error_short or "Connection refused" in error_short:
                    retry_msg = "Impossibile connettersi al server. Verifica host e porta."
                else:
                    retry_msg = f"Errore di connessione: {error_short[:100]}"

                # Mostra il dialog per selezionare/reinserire i dati CON il messaggio
                # NON salvare la config durante retry (verrà salvata dopo connessione riuscita)
                parent = self.iface.mainWindow() if (QGIS_AVAILABLE and self.iface) else None
                dialog = DatabaseSelectorDialog(
                    parent,
                    retry_message=retry_msg,
                    load_saved=False,
                    save_on_accept=False  # Non salvare ancora, salveremo dopo connessione riuscita
                )

                # Pre-carica la configurazione fallita (così l'utente deve solo inserire la password)
                dialog.load_config_to_ui(db_config)

                # Forza il dialog in primo piano
                dialog.raise_()
                dialog.activateWindow()

                print("🔐 Apertura dialog per inserimento password...")
                print(f"   Database: {db_config.get('database')} @ {db_config.get('host')}:{db_config.get('port')}")

                result = dialog.exec_()
                print(f"📝 Dialog chiuso con risultato: {result} ({'Accepted' if result == QDialog.Accepted else 'Rejected'})")

                if result == QDialog.Accepted:
                    # Ottieni la nuova configurazione (con password inserita dall'utente)
                    db_config = dialog.get_db_config()

                    # Debug: verifica che la password sia presente
                    has_password = bool(db_config.get('password'))
                    print(f"✓ Nuova configurazione ottenuta (password presente: {has_password})")

                    if not has_password and db_config.get('type') == 'postgres':
                        print("⚠️ ATTENZIONE: Password ancora vuota!")

                    # Riprova con la nuova configurazione
                    self.fauna_manager = FaunaManager(db_path=db_path, db_config=db_config)

                    # Se arriviamo qui, la connessione ha avuto successo!
                    # Salva la configurazione (senza password se SAVE_PASSWORD=False)
                    config_manager = DBConfigManager()
                    config_manager.save_config(db_config)
                    print("✅ Connessione riuscita, configurazione salvata")
                else:
                    # Utente ha annullato
                    return

            if QGIS_AVAILABLE and self.iface:
                # In QGIS, crea una finestra con parent corretto
                parent = self.iface.mainWindow() if self.iface else None
                self.window = QMainWindow(parent)
                self.window.setWindowTitle("Gestione Schede Fauna - pyArchInit")
                self.window.setCentralWidget(self.fauna_manager)
                self.window.resize(900, 700)

                # Imposta come finestra floating (non dock)
                self.window.setWindowFlags(Qt.Window)

                # IMPORTANTE: Salva nella variabile globale
                _fauna_window = self.window

                # Mostra la finestra
                self.window.show()
                self.window.raise_()
                self.window.activateWindow()

                # Messaggio di conferma
                if self.iface:
                    self.iface.messageBar().pushSuccess(
                        "Fauna Manager",
                        "Interfaccia Fauna Manager aperta con successo"
                    )
            else:
                # Standalone
                self.fauna_manager.show()
                _fauna_window = self.fauna_manager

        except Exception as e:
            error_msg = f"Errore nell'apertura: {str(e)}"
            if QGIS_AVAILABLE and self.iface:
                self.iface.messageBar().pushCritical(
                    "Fauna Manager",
                    error_msg
                )
            else:
                print(error_msg)

            # Mostra anche un dialog con l'errore
            QMessageBox.critical(None, "Errore", error_msg)

            import traceback
            traceback.print_exc()

    def select_database(self):
        """
        Mostra dialog per selezionare il database

        Returns:
            Configurazione database o None se annullato
        """
        parent = self.iface.mainWindow() if (QGIS_AVAILABLE and self.iface) else None

        dialog = DatabaseSelectorDialog(parent)

        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_db_config()

        return None

    def open_from_us_layer(self, us_id=None):
        """
        Apre Fauna Manager con filtro su una US specifica

        Args:
            us_id: ID della US selezionata
        """
        self.open_fauna_manager()

        if us_id and self.fauna_manager:
            # Imposta il filtro sulla US
            # Questa funzionalità può essere estesa per pre-filtrare i record
            pass

    def get_selected_us(self):
        """
        Recupera l'US selezionata dal layer QGIS

        Returns:
            ID dell'US selezionata o None
        """
        if not QGIS_AVAILABLE or not self.iface:
            return None

        # Ottiene il layer attivo
        layer = self.iface.activeLayer()

        if not layer or layer.selectedFeatureCount() == 0:
            return None

        # Ottiene la feature selezionata
        selected_features = layer.selectedFeatures()
        if selected_features:
            feature = selected_features[0]

            # Cerca il campo id_us
            if 'id_us' in feature.fields().names():
                return feature['id_us']

        return None


def open_fauna_manager_action():
    """
    Funzione da usare come Action in QGIS
    Può essere richiamata dalle proprietà del layer
    """
    integration = FaunaQGISIntegration(iface if QGIS_AVAILABLE else None)
    integration.open_fauna_manager()


def open_fauna_manager_from_us(us_id):
    """
    Apre Fauna Manager con filtro su una US specifica
    Da usare come Action parametrica in QGIS

    Args:
        us_id: ID della US (può essere passato come [% "id_us" %] in QGIS Action)
    """
    integration = FaunaQGISIntegration(iface if QGIS_AVAILABLE else None)
    integration.open_from_us_layer(us_id)


# Script principale
if __name__ == '__main__':
    # Se eseguito standalone, crea l'applicazione Qt
    if not QGIS_AVAILABLE:
        app = QApplication(sys.argv)

    integration = FaunaQGISIntegration(iface if QGIS_AVAILABLE else None)
    integration.open_fauna_manager()

    if not QGIS_AVAILABLE:
        sys.exit(app.exec_())
