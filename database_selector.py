"""
Dialog per selezionare la configurazione del database pyArchInit
Supporta SQLite e PostgreSQL
"""

import os
try:
    from qgis.PyQt.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QRadioButton, QButtonGroup, QGroupBox,
        QFormLayout, QFileDialog, QDialogButtonBox, QSpinBox
    )
    from qgis.PyQt.QtCore import Qt
except ImportError:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QRadioButton, QButtonGroup, QGroupBox,
        QFormLayout, QFileDialog, QDialogButtonBox, QSpinBox
    )
    from PyQt5.QtCore import Qt

from db_config_manager import DBConfigManager


class DatabaseSelectorDialog(QDialog):
    """Dialog per selezionare e configurare il database"""

    def __init__(self, parent=None, retry_message=None, load_saved=True, save_on_accept=True):
        super().__init__(parent)
        self.config_manager = DBConfigManager()
        self.retry_message = retry_message
        self.save_on_accept = save_on_accept  # Se False, non salva quando clicchi OK (usato durante retry)
        self.setup_ui()

        # Carica configurazione salvata solo se richiesto
        # Durante retry, il chiamante passerà già la config pre-compilata
        if load_saved:
            self.load_saved_or_default_settings()

    def setup_ui(self):
        """Configura l'interfaccia del dialog"""
        self.setWindowTitle("Selezione Database pyArchInit")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Titolo
        title = QLabel("<h2>Configurazione Database</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Messaggio di retry se presente
        if self.retry_message:
            retry_label = QLabel(f"<b style='color: #d9534f;'>⚠ {self.retry_message}</b>")
            retry_label.setWordWrap(True)
            retry_label.setAlignment(Qt.AlignCenter)
            retry_label.setStyleSheet("padding: 10px; background-color: #f8d7da; border-radius: 5px; margin: 10px;")
            layout.addWidget(retry_label)

        # Gruppo selezione tipo database
        type_group = QGroupBox("Tipo di Database")
        type_layout = QVBoxLayout(type_group)

        self.radio_sqlite = QRadioButton("SQLite (File locale)")
        self.radio_postgres = QRadioButton("PostgreSQL (Server)")
        self.radio_sqlite.setChecked(True)

        self.db_type_group = QButtonGroup(self)
        self.db_type_group.addButton(self.radio_sqlite)
        self.db_type_group.addButton(self.radio_postgres)

        type_layout.addWidget(self.radio_sqlite)
        type_layout.addWidget(self.radio_postgres)

        layout.addWidget(type_group)

        # Configurazione SQLite
        self.sqlite_group = QGroupBox("Configurazione SQLite")
        sqlite_layout = QFormLayout(self.sqlite_group)

        self.txt_sqlite_path = QLineEdit()
        self.txt_sqlite_path.setPlaceholderText("Percorso del file database...")

        btn_browse = QPushButton("Sfoglia...")
        btn_browse.clicked.connect(self.browse_sqlite)

        sqlite_path_layout = QHBoxLayout()
        sqlite_path_layout.addWidget(self.txt_sqlite_path)
        sqlite_path_layout.addWidget(btn_browse)

        sqlite_layout.addRow("Percorso Database:", sqlite_path_layout)

        layout.addWidget(self.sqlite_group)

        # Configurazione PostgreSQL
        self.postgres_group = QGroupBox("Configurazione PostgreSQL")
        postgres_layout = QFormLayout(self.postgres_group)

        self.txt_pg_host = QLineEdit()
        self.txt_pg_host.setPlaceholderText("localhost")
        postgres_layout.addRow("Host:", self.txt_pg_host)

        self.spin_pg_port = QSpinBox()
        self.spin_pg_port.setMinimum(1)
        self.spin_pg_port.setMaximum(65535)
        self.spin_pg_port.setValue(5432)
        postgres_layout.addRow("Porta:", self.spin_pg_port)

        self.txt_pg_database = QLineEdit()
        self.txt_pg_database.setPlaceholderText("pyarchinit")
        postgres_layout.addRow("Database:", self.txt_pg_database)

        self.txt_pg_user = QLineEdit()
        self.txt_pg_user.setPlaceholderText("postgres")
        postgres_layout.addRow("Utente:", self.txt_pg_user)

        self.txt_pg_password = QLineEdit()
        self.txt_pg_password.setEchoMode(QLineEdit.Password)
        postgres_layout.addRow("Password:", self.txt_pg_password)

        layout.addWidget(self.postgres_group)

        # Test connessione
        self.btn_test = QPushButton("🔍 Test Connessione")
        self.btn_test.clicked.connect(self.test_connection)
        layout.addWidget(self.btn_test)

        # Label risultato test
        self.lbl_test_result = QLabel("")
        self.lbl_test_result.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_test_result)

        # Bottoni OK/Cancel
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Connetti i radio button per mostrare/nascondere gruppi
        self.radio_sqlite.toggled.connect(self.update_visible_groups)
        self.radio_postgres.toggled.connect(self.update_visible_groups)

        # Inizializza visibilità
        self.update_visible_groups()

    def load_saved_or_default_settings(self):
        """Carica l'ultima configurazione salvata o quella predefinita"""
        # Prova a caricare l'ultima configurazione
        saved_config = self.config_manager.load_config()

        if saved_config:
            print("📂 Caricamento ultima configurazione salvata...")
            self.load_config_to_ui(saved_config)
        else:
            print("📝 Caricamento configurazione predefinita...")
            self.load_default_settings()

    def load_default_settings(self):
        """Carica le impostazioni predefinite"""
        # Percorso predefinito SQLite
        home = os.path.expanduser("~")
        default_sqlite = os.path.join(home, "pyarchinit", "pyarchinit_DB_folder", "pyarchinit_db.sqlite")
        self.txt_sqlite_path.setText(default_sqlite)

        # Impostazioni predefinite PostgreSQL
        self.txt_pg_host.setText("localhost")
        self.spin_pg_port.setValue(5432)
        self.txt_pg_database.setText("pyarchinit")
        self.txt_pg_user.setText("postgres")

    def load_config_to_ui(self, config):
        """
        Carica una configurazione nell'interfaccia

        Args:
            config: dizionario con la configurazione
        """
        if config['type'] == 'sqlite':
            self.radio_sqlite.setChecked(True)
            self.txt_sqlite_path.setText(config.get('path', ''))
        else:
            self.radio_postgres.setChecked(True)
            self.txt_pg_host.setText(config.get('host', 'localhost'))
            self.spin_pg_port.setValue(config.get('port', 5432))
            self.txt_pg_database.setText(config.get('database', 'pyarchinit'))
            self.txt_pg_user.setText(config.get('user', 'postgres'))
            # Non carichiamo la password per sicurezza
            self.txt_pg_password.setText(config.get('password', ''))

            # Se c'è un messaggio di retry (errore password), metti focus sul campo password
            if self.retry_message and "password" in self.retry_message.lower():
                self.txt_pg_password.setFocus()
                self.txt_pg_password.selectAll()

    def update_visible_groups(self):
        """Aggiorna la visibilità dei gruppi in base al tipo selezionato"""
        is_sqlite = self.radio_sqlite.isChecked()

        self.sqlite_group.setVisible(is_sqlite)
        self.postgres_group.setVisible(not is_sqlite)

    def browse_sqlite(self):
        """Apre dialog per selezionare il file SQLite"""
        home = os.path.expanduser("~")
        default_dir = os.path.join(home, "pyarchinit", "pyarchinit_DB_folder")

        if not os.path.exists(default_dir):
            default_dir = home

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona Database SQLite",
            default_dir,
            "Database SQLite (*.sqlite *.db);;Tutti i file (*.*)"
        )

        if filename:
            self.txt_sqlite_path.setText(filename)

    def test_connection(self):
        """Testa la connessione al database"""
        self.lbl_test_result.setText("⏳ Test in corso...")
        self.lbl_test_result.setStyleSheet("color: blue;")

        try:
            config = self.get_db_config()

            if config['type'] == 'sqlite':
                # Test SQLite
                import sqlite3

                if not os.path.exists(config['path']):
                    self.lbl_test_result.setText("✗ File database non trovato")
                    self.lbl_test_result.setStyleSheet("color: red;")
                    return

                conn = sqlite3.connect(config['path'])
                cursor = conn.cursor()

                # Verifica che sia un database pyarchinit
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='us_table'")
                if not cursor.fetchone():
                    self.lbl_test_result.setText("⚠ Database valido ma senza tabella us_table")
                    self.lbl_test_result.setStyleSheet("color: orange;")
                else:
                    cursor.execute("SELECT COUNT(*) FROM us_table")
                    count = cursor.fetchone()[0]
                    self.lbl_test_result.setText(f"✓ Connessione OK - {count} US trovate")
                    self.lbl_test_result.setStyleSheet("color: green;")

                conn.close()

            else:
                # Test PostgreSQL
                try:
                    import psycopg2
                except ImportError:
                    self.lbl_test_result.setText("✗ Modulo psycopg2 non installato")
                    self.lbl_test_result.setStyleSheet("color: red;")
                    return

                conn = psycopg2.connect(
                    host=config['host'],
                    port=config['port'],
                    database=config['database'],
                    user=config['user'],
                    password=config['password']
                )

                cursor = conn.cursor()

                # Verifica tabella us_table
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'us_table'
                    )
                """)

                if not cursor.fetchone()[0]:
                    self.lbl_test_result.setText("⚠ Connessione OK ma senza tabella us_table")
                    self.lbl_test_result.setStyleSheet("color: orange;")
                else:
                    cursor.execute("SELECT COUNT(*) FROM us_table")
                    count = cursor.fetchone()[0]
                    self.lbl_test_result.setText(f"✓ Connessione OK - {count} US trovate")
                    self.lbl_test_result.setStyleSheet("color: green;")

                conn.close()

        except Exception as e:
            self.lbl_test_result.setText(f"✗ Errore: {str(e)}")
            self.lbl_test_result.setStyleSheet("color: red;")

    def on_accept(self):
        """Gestisce il click su OK - salva la configurazione se richiesto"""
        if self.save_on_accept:
            config = self.get_db_config()
            self.config_manager.save_config(config)
        self.accept()

    def get_db_config(self):
        """
        Restituisce la configurazione del database

        Returns:
            Dict con la configurazione
        """
        if self.radio_sqlite.isChecked():
            return {
                'type': 'sqlite',
                'path': self.txt_sqlite_path.text()
            }
        else:
            return {
                'type': 'postgres',
                'host': self.txt_pg_host.text() or 'localhost',
                'port': self.spin_pg_port.value(),
                'database': self.txt_pg_database.text() or 'pyarchinit',
                'user': self.txt_pg_user.text() or 'postgres',
                'password': self.txt_pg_password.text()
            }


# Test standalone
if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    dialog = DatabaseSelectorDialog()

    if dialog.exec_() == QDialog.Accepted:
        config = dialog.get_db_config()
        print("Configurazione selezionata:")
        print(config)
    else:
        print("Annullato")

    sys.exit(0)
