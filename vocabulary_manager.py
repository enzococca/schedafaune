"""
Interfaccia per la gestione del vocabolario controllato
Permette di aggiungere, modificare ed eliminare valori dal vocabolario
"""

try:
    from qgis.PyQt.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
        QDialogButtonBox, QMessageBox, QHeaderView, QSpinBox, QCheckBox, QTextEdit
    )
    from qgis.PyQt.QtCore import Qt
except ImportError:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
        QDialogButtonBox, QMessageBox, QHeaderView, QSpinBox, QCheckBox, QTextEdit
    )
    from PyQt5.QtCore import Qt


class VocabularyManagerDialog(QDialog):
    """Dialog per gestire il vocabolario controllato"""

    # Campi disponibili nel vocabolario
    AVAILABLE_FIELDS = [
        'metodologia_recupero',
        'contesto',
        'resti_connessione_anatomica',
        'tipologia_accumulo',
        'deposizione',
        'numero_stimato_resti',
        'specie',
        'parti_scheletriche',
        'stato_frammentazione',
        'tracce_combustione',
        'tipo_combustione',
        'segni_tafonomici_evidenti',
        'caratterizzazione_segni_tafonomici',
        'stato_conservazione'
    ]

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_field = None
        self.setup_ui()
        self.load_fields()

    def setup_ui(self):
        """Configura l'interfaccia"""
        self.setWindowTitle("Gestione Vocabolario Controllato")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # Titolo
        title = QLabel("<h2>Gestione Vocabolario Controllato</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Selezione campo
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel("Campo:"))

        self.combo_field = QComboBox()
        self.combo_field.currentTextChanged.connect(self.load_values)
        field_layout.addWidget(self.combo_field)

        layout.addLayout(field_layout)

        # Tabella valori
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Valore", "Descrizione", "Ordinamento", "Attivo"
        ])

        # Nascondi colonna ID
        self.table.setColumnHidden(0, True)

        # Ridimensiona colonne
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        layout.addWidget(self.table)

        # Bottoni gestione
        buttons_layout = QHBoxLayout()

        btn_add = QPushButton("➕ Aggiungi Valore")
        btn_add.clicked.connect(self.add_value)
        buttons_layout.addWidget(btn_add)

        btn_edit = QPushButton("✏ Modifica")
        btn_edit.clicked.connect(self.edit_value)
        buttons_layout.addWidget(btn_edit)

        btn_delete = QPushButton("🗑 Elimina")
        btn_delete.clicked.connect(self.delete_value)
        buttons_layout.addWidget(btn_delete)

        buttons_layout.addStretch()

        btn_refresh = QPushButton("🔄 Ricarica")
        btn_refresh.clicked.connect(self.load_values)
        buttons_layout.addWidget(btn_refresh)

        layout.addLayout(buttons_layout)

        # Bottoni dialog
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Close)
        dialog_buttons.rejected.connect(self.accept)
        layout.addWidget(dialog_buttons)

    def load_fields(self):
        """Carica la lista dei campi"""
        self.combo_field.clear()
        self.combo_field.addItems(self.AVAILABLE_FIELDS)

    def load_values(self):
        """Carica i valori del campo selezionato"""
        self.current_field = self.combo_field.currentText()

        if not self.current_field:
            return

        # Recupera i valori dal database
        try:
            cursor = self.db.conn.cursor()

            # Query dipende dal tipo di database
            if hasattr(self.db, 'psycopg2'):
                # PostgreSQL
                cursor.execute("""
                    SELECT id_voc, valore, descrizione, ordinamento, attivo
                    FROM fauna_voc
                    WHERE campo = %s
                    ORDER BY ordinamento, valore
                """, (self.current_field,))
            else:
                # SQLite
                cursor.execute("""
                    SELECT id_voc, valore, descrizione, ordinamento, attivo
                    FROM fauna_voc
                    WHERE campo = ?
                    ORDER BY ordinamento, valore
                """, (self.current_field,))

            rows = cursor.fetchall()

            # Popola la tabella
            self.table.setRowCount(len(rows))

            for i, row in enumerate(rows):
                # ID (nascosto)
                self.table.setItem(i, 0, QTableWidgetItem(str(row[0] if isinstance(row, tuple) else row['id_voc'])))

                # Valore
                self.table.setItem(i, 1, QTableWidgetItem(str(row[1] if isinstance(row, tuple) else row['valore'])))

                # Descrizione
                desc = row[2] if isinstance(row, tuple) else row['descrizione']
                self.table.setItem(i, 2, QTableWidgetItem(str(desc or '')))

                # Ordinamento
                ord_val = row[3] if isinstance(row, tuple) else row['ordinamento']
                self.table.setItem(i, 3, QTableWidgetItem(str(ord_val or 0)))

                # Attivo
                attivo = row[4] if isinstance(row, tuple) else row['attivo']
                item_attivo = QTableWidgetItem("✓" if attivo else "✗")
                item_attivo.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 4, item_attivo)

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel caricamento: {str(e)}")

    def add_value(self):
        """Aggiunge un nuovo valore al vocabolario"""
        if not self.current_field:
            QMessageBox.warning(self, "Attenzione", "Seleziona un campo!")
            return

        dialog = AddEditValueDialog(self.current_field, parent=self)

        if dialog.exec_() == QDialog.Accepted:
            value_data = dialog.get_value_data()

            try:
                cursor = self.db.conn.cursor()

                # Insert dipende dal tipo di database
                if hasattr(self.db, 'psycopg2'):
                    # PostgreSQL
                    cursor.execute("""
                        INSERT INTO fauna_voc (campo, valore, descrizione, ordinamento, attivo)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        self.current_field,
                        value_data['valore'],
                        value_data['descrizione'],
                        value_data['ordinamento'],
                        value_data['attivo']
                    ))
                    self.db.conn.commit()
                else:
                    # SQLite
                    cursor.execute("""
                        INSERT INTO fauna_voc (campo, valore, descrizione, ordinamento, attivo)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        self.current_field,
                        value_data['valore'],
                        value_data['descrizione'],
                        value_data['ordinamento'],
                        value_data['attivo']
                    ))
                    self.db.conn.commit()

                QMessageBox.information(self, "Successo", "Valore aggiunto con successo!")
                self.load_values()

            except Exception as e:
                if hasattr(self.db, 'psycopg2'):
                    self.db.conn.rollback()
                QMessageBox.critical(self, "Errore", f"Errore nell'inserimento: {str(e)}")

    def edit_value(self):
        """Modifica il valore selezionato"""
        current_row = self.table.currentRow()

        if current_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona un valore da modificare!")
            return

        id_voc = int(self.table.item(current_row, 0).text())
        current_value = self.table.item(current_row, 1).text()
        current_desc = self.table.item(current_row, 2).text()
        current_ord = int(self.table.item(current_row, 3).text())
        current_attivo = self.table.item(current_row, 4).text() == "✓"

        dialog = AddEditValueDialog(
            self.current_field,
            valore=current_value,
            descrizione=current_desc,
            ordinamento=current_ord,
            attivo=current_attivo,
            parent=self
        )

        if dialog.exec_() == QDialog.Accepted:
            value_data = dialog.get_value_data()

            try:
                cursor = self.db.conn.cursor()

                # Update dipende dal tipo di database
                if hasattr(self.db, 'psycopg2'):
                    # PostgreSQL
                    cursor.execute("""
                        UPDATE fauna_voc
                        SET valore = %s, descrizione = %s, ordinamento = %s, attivo = %s
                        WHERE id_voc = %s
                    """, (
                        value_data['valore'],
                        value_data['descrizione'],
                        value_data['ordinamento'],
                        value_data['attivo'],
                        id_voc
                    ))
                    self.db.conn.commit()
                else:
                    # SQLite
                    cursor.execute("""
                        UPDATE fauna_voc
                        SET valore = ?, descrizione = ?, ordinamento = ?, attivo = ?
                        WHERE id_voc = ?
                    """, (
                        value_data['valore'],
                        value_data['descrizione'],
                        value_data['ordinamento'],
                        value_data['attivo'],
                        id_voc
                    ))
                    self.db.conn.commit()

                QMessageBox.information(self, "Successo", "Valore modificato con successo!")
                self.load_values()

            except Exception as e:
                if hasattr(self.db, 'psycopg2'):
                    self.db.conn.rollback()
                QMessageBox.critical(self, "Errore", f"Errore nella modifica: {str(e)}")

    def delete_value(self):
        """Elimina il valore selezionato"""
        current_row = self.table.currentRow()

        if current_row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona un valore da eliminare!")
            return

        id_voc = int(self.table.item(current_row, 0).text())
        valore = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self,
            "Conferma",
            f"Sei sicuro di voler eliminare '{valore}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                cursor = self.db.conn.cursor()

                # Delete dipende dal tipo di database
                if hasattr(self.db, 'psycopg2'):
                    # PostgreSQL
                    cursor.execute("DELETE FROM fauna_voc WHERE id_voc = %s", (id_voc,))
                    self.db.conn.commit()
                else:
                    # SQLite
                    cursor.execute("DELETE FROM fauna_voc WHERE id_voc = ?", (id_voc,))
                    self.db.conn.commit()

                QMessageBox.information(self, "Successo", "Valore eliminato con successo!")
                self.load_values()

            except Exception as e:
                if hasattr(self.db, 'psycopg2'):
                    self.db.conn.rollback()
                QMessageBox.critical(self, "Errore", f"Errore nell'eliminazione: {str(e)}")


class AddEditValueDialog(QDialog):
    """Dialog per aggiungere o modificare un valore del vocabolario"""

    def __init__(self, campo, valore='', descrizione='', ordinamento=0, attivo=True, parent=None):
        super().__init__(parent)
        self.campo = campo
        self.setup_ui()

        # Popola con valori esistenti (se modifica)
        self.txt_valore.setText(valore)
        self.txt_descrizione.setPlainText(descrizione)
        self.spin_ordinamento.setValue(ordinamento)
        self.check_attivo.setChecked(attivo)

    def setup_ui(self):
        """Configura l'interfaccia"""
        self.setWindowTitle("Aggiungi/Modifica Valore")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Campo (read-only)
        layout.addWidget(QLabel(f"<b>Campo:</b> {self.campo}"))

        # Valore
        layout.addWidget(QLabel("Valore:"))
        self.txt_valore = QLineEdit()
        layout.addWidget(self.txt_valore)

        # Descrizione
        layout.addWidget(QLabel("Descrizione (opzionale):"))
        self.txt_descrizione = QTextEdit()
        self.txt_descrizione.setMaximumHeight(80)
        layout.addWidget(self.txt_descrizione)

        # Ordinamento
        layout.addWidget(QLabel("Ordinamento:"))
        self.spin_ordinamento = QSpinBox()
        self.spin_ordinamento.setMinimum(0)
        self.spin_ordinamento.setMaximum(9999)
        layout.addWidget(self.spin_ordinamento)

        # Attivo
        self.check_attivo = QCheckBox("Valore attivo")
        self.check_attivo.setChecked(True)
        layout.addWidget(self.check_attivo)

        # Bottoni
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_and_accept(self):
        """Valida i dati prima di accettare"""
        if not self.txt_valore.text().strip():
            QMessageBox.warning(self, "Attenzione", "Il valore non può essere vuoto!")
            return

        self.accept()

    def get_value_data(self):
        """Restituisce i dati del valore"""
        return {
            'valore': self.txt_valore.text().strip(),
            'descrizione': self.txt_descrizione.toPlainText().strip(),
            'ordinamento': self.spin_ordinamento.value(),
            'attivo': 1 if self.check_attivo.isChecked() else 0
        }


# Test standalone
if __name__ == '__main__':
    import sys
    try:
        from qgis.PyQt.QtWidgets import QApplication
    except ImportError:
        from PyQt5.QtWidgets import QApplication

    from fauna_db_wrapper import create_fauna_db

    app = QApplication(sys.argv)

    db = create_fauna_db()
    dialog = VocabularyManagerDialog(db)
    dialog.exec_()

    db.close()
