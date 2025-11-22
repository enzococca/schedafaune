"""
Interfaccia Qt per la gestione dei dati faunistici
Integrabile con QGIS tramite le proprietà dei layer
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QLineEdit,
    QComboBox, QTextEdit, QDateEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QToolBar, QMessageBox, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QDialogButtonBox, QHeaderView, QAction,
    QGroupBox, QGridLayout, QSplitter
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QIcon
from typing import Dict, List, Optional
import os

from fauna_db_wrapper import create_fauna_db
from database_selector import DatabaseSelectorDialog


class FaunaSearchDialog(QDialog):
    """Dialog per la ricerca avanzata"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        """Configura l'interfaccia del dialog di ricerca"""
        self.setWindowTitle("Ricerca Schede Fauna")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Campo di ricerca
        form = QFormLayout()

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Inserisci termine di ricerca...")
        form.addRow("Cerca:", self.txt_search)

        # Filtri
        self.combo_sito = QComboBox()
        self.combo_sito.addItem("Tutti i siti", "")
        for sito in self.db.get_siti_list():
            self.combo_sito.addItem(sito, sito)
        form.addRow("Sito:", self.combo_sito)

        self.combo_contesto = QComboBox()
        self.combo_contesto.addItem("Tutti i contesti", "")
        for val in self.db.get_voc_values('contesto'):
            self.combo_contesto.addItem(val, val)
        form.addRow("Contesto:", self.combo_contesto)

        self.combo_specie = QComboBox()
        self.combo_specie.addItem("Tutte le specie", "")
        for val in self.db.get_voc_values('specie'):
            self.combo_specie.addItem(val, val)
        form.addRow("Specie:", self.combo_specie)

        layout.addLayout(form)

        # Bottoni
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_filters(self) -> Dict:
        """Restituisce i filtri impostati"""
        filters = {}

        if self.combo_sito.currentData():
            filters['sito'] = self.combo_sito.currentData()

        if self.combo_contesto.currentData():
            filters['contesto'] = self.combo_contesto.currentData()

        if self.combo_specie.currentData():
            filters['specie'] = self.combo_specie.currentData()

        return filters

    def get_search_term(self) -> str:
        """Restituisce il termine di ricerca"""
        return self.txt_search.text().strip()


class FaunaManager(QWidget):
    """Widget principale per la gestione delle schede fauna"""

    record_changed = pyqtSignal(int)  # Emesso quando cambia il record corrente

    def __init__(self, db_path: str = None, db_config: Dict = None, parent=None):
        super().__init__(parent)
        self.db = create_fauna_db(db_path, db_config)
        self.current_record_id = None
        self.records = []
        self.current_index = -1

        self.setup_ui()
        self.load_records()

    def setup_ui(self):
        """Configura l'interfaccia utente"""
        self.setWindowTitle("Gestione Schede Fauna - pyArchInit")
        self.setMinimumSize(900, 700)

        main_layout = QVBoxLayout(self)

        # Toolbar
        self.create_toolbar()
        main_layout.addWidget(self.toolbar)

        # Barra informazioni record
        info_layout = QHBoxLayout()
        self.lbl_record_info = QLabel("Nessun record")
        self.lbl_record_info.setStyleSheet("font-weight: bold; color: #2c3e50;")
        info_layout.addWidget(self.lbl_record_info)
        info_layout.addStretch()
        main_layout.addLayout(info_layout)

        # Tab widget per organizzare i campi
        self.tab_widget = QTabWidget()

        # Tab 1: Dati Identificativi e Deposizionali
        self.tab_identificativi = self.create_tab_identificativi()
        self.tab_widget.addTab(self.tab_identificativi, "Dati Identificativi")

        # Tab 2: Dati Archeozoologici
        self.tab_archeozoologici = self.create_tab_archeozoologici()
        self.tab_widget.addTab(self.tab_archeozoologici, "Dati Archeozoologici")

        # Tab 3: Dati Tafonomici
        self.tab_tafonomici = self.create_tab_tafonomici()
        self.tab_widget.addTab(self.tab_tafonomici, "Dati Tafonomici")

        # Tab 4: Dati Contestuali
        self.tab_contestuali = self.create_tab_contestuali()
        self.tab_widget.addTab(self.tab_contestuali, "Dati Contestuali")

        main_layout.addWidget(self.tab_widget)

    def create_toolbar(self):
        """Crea la toolbar di navigazione e gestione"""
        self.toolbar = QToolBar("Navigazione")
        self.toolbar.setMovable(False)

        # Navigazione
        self.act_first = QAction("⏮ Primo", self)
        self.act_first.triggered.connect(self.first_record)
        self.toolbar.addAction(self.act_first)

        self.act_prev = QAction("◀ Precedente", self)
        self.act_prev.triggered.connect(self.previous_record)
        self.toolbar.addAction(self.act_prev)

        self.act_next = QAction("Successivo ▶", self)
        self.act_next.triggered.connect(self.next_record)
        self.toolbar.addAction(self.act_next)

        self.act_last = QAction("Ultimo ⏭", self)
        self.act_last.triggered.connect(self.last_record)
        self.toolbar.addAction(self.act_last)

        self.toolbar.addSeparator()

        # Gestione record
        self.act_new = QAction("➕ Nuovo", self)
        self.act_new.triggered.connect(self.new_record)
        self.toolbar.addAction(self.act_new)

        self.act_save = QAction("💾 Salva", self)
        self.act_save.triggered.connect(self.save_record)
        self.toolbar.addAction(self.act_save)

        self.act_delete = QAction("🗑 Elimina", self)
        self.act_delete.triggered.connect(self.delete_record)
        self.toolbar.addAction(self.act_delete)

        self.toolbar.addSeparator()

        # Ricerca
        self.act_search = QAction("🔍 Cerca", self)
        self.act_search.triggered.connect(self.search_records)
        self.toolbar.addAction(self.act_search)

        self.toolbar.addSeparator()

        # Gestione Vocabolario
        self.act_vocabulary = QAction("📚 Gestione Vocabolario", self)
        self.act_vocabulary.triggered.connect(self.manage_vocabulary)
        self.toolbar.addAction(self.act_vocabulary)

        self.toolbar.addSeparator()

        # Cambia Database
        self.act_change_db = QAction("🔄 Cambia Database", self)
        self.act_change_db.triggered.connect(self.change_database)
        self.toolbar.addAction(self.act_change_db)

        self.toolbar.addSeparator()

        # Esportazione
        self.act_export_pdf = QAction("📄 Esporta PDF", self)
        self.act_export_pdf.triggered.connect(self.export_pdf)
        self.toolbar.addAction(self.act_export_pdf)

    def create_tab_identificativi(self) -> QWidget:
        """Crea il tab dei dati identificativi e deposizionali"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Gruppo Dati Identificativi (da US)
        group_id = QGroupBox("Dati Identificativi (da US)")
        form_id = QFormLayout(group_id)

        self.txt_id_fauna = QLineEdit()
        self.txt_id_fauna.setReadOnly(True)
        form_id.addRow("ID Fauna:", self.txt_id_fauna)

        # ComboBox per selezionare US
        self.combo_us = QComboBox()
        self.combo_us.currentIndexChanged.connect(self.on_us_selected)
        form_id.addRow("US *:", self.combo_us)

        self.txt_sito = QLineEdit()
        self.txt_sito.setReadOnly(True)
        form_id.addRow("Sito:", self.txt_sito)

        self.txt_area = QLineEdit()
        self.txt_area.setReadOnly(True)
        form_id.addRow("Area:", self.txt_area)

        self.txt_saggio = QLineEdit()
        self.txt_saggio.setReadOnly(True)
        form_id.addRow("Saggio:", self.txt_saggio)

        self.txt_datazione_us = QLineEdit()
        self.txt_datazione_us.setReadOnly(True)
        form_id.addRow("Datazione US:", self.txt_datazione_us)

        layout.addWidget(group_id)

        # Gruppo Dati Deposizionali
        group_dep = QGroupBox("Dati Deposizionali")
        form_dep = QFormLayout(group_dep)

        self.txt_responsabile = QLineEdit()
        form_dep.addRow("Responsabile Scheda:", self.txt_responsabile)

        self.date_compilazione = QDateEdit()
        self.date_compilazione.setDate(QDate.currentDate())
        self.date_compilazione.setCalendarPopup(True)
        form_dep.addRow("Data Compilazione:", self.date_compilazione)

        self.txt_doc_fotografica = QLineEdit()
        form_dep.addRow("Doc. Fotografica:", self.txt_doc_fotografica)

        self.combo_metodologia = QComboBox()
        self.combo_metodologia.setEditable(True)
        form_dep.addRow("Metodologia Recupero:", self.combo_metodologia)

        self.combo_contesto = QComboBox()
        self.combo_contesto.setEditable(True)
        form_dep.addRow("Contesto:", self.combo_contesto)

        self.txt_desc_contesto = QTextEdit()
        self.txt_desc_contesto.setMaximumHeight(100)
        form_dep.addRow("Descrizione Contesto:", self.txt_desc_contesto)

        layout.addWidget(group_dep)
        layout.addStretch()

        return widget

    def create_tab_archeozoologici(self) -> QWidget:
        """Crea il tab dei dati archeozoologici"""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.combo_connessione = QComboBox()
        self.combo_connessione.setEditable(True)
        layout.addRow("Connessione Anatomica:", self.combo_connessione)

        self.combo_tipologia_accumulo = QComboBox()
        self.combo_tipologia_accumulo.setEditable(True)
        layout.addRow("Tipologia Accumulo:", self.combo_tipologia_accumulo)

        self.combo_deposizione = QComboBox()
        self.combo_deposizione.setEditable(True)
        layout.addRow("Deposizione:", self.combo_deposizione)

        self.combo_num_stimato = QComboBox()
        self.combo_num_stimato.setEditable(True)
        layout.addRow("Numero Stimato Resti:", self.combo_num_stimato)

        self.spin_nmi = QDoubleSpinBox()
        self.spin_nmi.setDecimals(2)
        self.spin_nmi.setMaximum(9999.99)
        layout.addRow("NMI:", self.spin_nmi)

        self.combo_specie = QComboBox()
        self.combo_specie.setEditable(True)
        layout.addRow("Specie:", self.combo_specie)

        self.combo_parti_scheletriche = QComboBox()
        self.combo_parti_scheletriche.setEditable(True)
        layout.addRow("Parti Scheletriche:", self.combo_parti_scheletriche)

        self.spin_misure = QDoubleSpinBox()
        self.spin_misure.setDecimals(2)
        self.spin_misure.setMaximum(9999.99)
        layout.addRow("Misure Ossa (mm):", self.spin_misure)

        return widget

    def create_tab_tafonomici(self) -> QWidget:
        """Crea il tab dei dati tafonomici"""
        widget = QWidget()
        layout = QFormLayout(widget)

        self.combo_frammentazione = QComboBox()
        self.combo_frammentazione.setEditable(True)
        layout.addRow("Stato Frammentazione:", self.combo_frammentazione)

        self.combo_tracce_combustione = QComboBox()
        self.combo_tracce_combustione.setEditable(True)
        layout.addRow("Tracce Combustione:", self.combo_tracce_combustione)

        self.check_combustione_altri = QCheckBox()
        layout.addRow("Combustione su Altri Materiali US:", self.check_combustione_altri)

        self.combo_tipo_combustione = QComboBox()
        self.combo_tipo_combustione.setEditable(True)
        layout.addRow("Tipo Combustione:", self.combo_tipo_combustione)

        self.combo_segni_tafonomici = QComboBox()
        self.combo_segni_tafonomici.setEditable(True)
        layout.addRow("Segni Tafonomici Evidenti:", self.combo_segni_tafonomici)

        self.combo_caratterizzazione_tafonomici = QComboBox()
        self.combo_caratterizzazione_tafonomici.setEditable(True)
        layout.addRow("Caratterizzazione Segni:", self.combo_caratterizzazione_tafonomici)

        self.combo_stato_conservazione = QComboBox()
        layout.addRow("Stato Conservazione:", self.combo_stato_conservazione)

        self.txt_alterazioni = QLineEdit()
        layout.addRow("Alterazioni Morfologiche:", self.txt_alterazioni)

        return widget

    def create_tab_contestuali(self) -> QWidget:
        """Crea il tab dei dati contestuali"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        form = QFormLayout()

        self.txt_note_terreno = QTextEdit()
        self.txt_note_terreno.setMaximumHeight(80)
        form.addRow("Note Terreno Giacitura:", self.txt_note_terreno)

        self.txt_campionature = QTextEdit()
        self.txt_campionature.setMaximumHeight(80)
        form.addRow("Campionature Effettuate:", self.txt_campionature)

        self.txt_affidabilita = QTextEdit()
        self.txt_affidabilita.setMaximumHeight(80)
        form.addRow("Affidabilità Stratigrafica:", self.txt_affidabilita)

        self.txt_classi_reperti = QTextEdit()
        self.txt_classi_reperti.setMaximumHeight(80)
        form.addRow("Classi Reperti Associazione:", self.txt_classi_reperti)

        self.txt_osservazioni = QTextEdit()
        self.txt_osservazioni.setMaximumHeight(100)
        form.addRow("Osservazioni:", self.txt_osservazioni)

        self.txt_interpretazione = QTextEdit()
        self.txt_interpretazione.setMaximumHeight(100)
        form.addRow("Interpretazione:", self.txt_interpretazione)

        layout.addLayout(form)
        layout.addStretch()

        return widget

    def populate_combos(self):
        """Popola le combo box con i valori del vocabolario"""
        # Metodologia recupero
        self.combo_metodologia.clear()
        self.combo_metodologia.addItem("")
        self.combo_metodologia.addItems(self.db.get_voc_values('metodologia_recupero'))

        # Contesto
        self.combo_contesto.clear()
        self.combo_contesto.addItem("")
        self.combo_contesto.addItems(self.db.get_voc_values('contesto'))

        # Connessione anatomica
        self.combo_connessione.clear()
        self.combo_connessione.addItem("")
        self.combo_connessione.addItems(self.db.get_voc_values('resti_connessione_anatomica'))

        # Tipologia accumulo
        self.combo_tipologia_accumulo.clear()
        self.combo_tipologia_accumulo.addItem("")
        self.combo_tipologia_accumulo.addItems(self.db.get_voc_values('tipologia_accumulo'))

        # Deposizione
        self.combo_deposizione.clear()
        self.combo_deposizione.addItem("")
        self.combo_deposizione.addItems(self.db.get_voc_values('deposizione'))

        # Numero stimato resti
        self.combo_num_stimato.clear()
        self.combo_num_stimato.addItem("")
        self.combo_num_stimato.addItems(self.db.get_voc_values('numero_stimato_resti'))

        # Specie
        self.combo_specie.clear()
        self.combo_specie.addItem("")
        self.combo_specie.addItems(self.db.get_voc_values('specie'))

        # Parti scheletriche
        self.combo_parti_scheletriche.clear()
        self.combo_parti_scheletriche.addItem("")
        self.combo_parti_scheletriche.addItems(self.db.get_voc_values('parti_scheletriche'))

        # Frammentazione
        self.combo_frammentazione.clear()
        self.combo_frammentazione.addItem("")
        self.combo_frammentazione.addItems(self.db.get_voc_values('stato_frammentazione'))

        # Tracce combustione
        self.combo_tracce_combustione.clear()
        self.combo_tracce_combustione.addItem("")
        self.combo_tracce_combustione.addItems(self.db.get_voc_values('tracce_combustione'))

        # Tipo combustione
        self.combo_tipo_combustione.clear()
        self.combo_tipo_combustione.addItem("")
        self.combo_tipo_combustione.addItems(self.db.get_voc_values('tipo_combustione'))

        # Segni tafonomici
        self.combo_segni_tafonomici.clear()
        self.combo_segni_tafonomici.addItem("")
        self.combo_segni_tafonomici.addItems(self.db.get_voc_values('segni_tafonomici_evidenti'))

        # Caratterizzazione tafonomici
        self.combo_caratterizzazione_tafonomici.clear()
        self.combo_caratterizzazione_tafonomici.addItem("")
        self.combo_caratterizzazione_tafonomici.addItems(self.db.get_voc_values('caratterizzazione_segni_tafonomici'))

        # Stato conservazione
        self.combo_stato_conservazione.clear()
        self.combo_stato_conservazione.addItem("")
        for val in self.db.get_voc_values('stato_conservazione'):
            # Recupera anche la descrizione
            desc_map = {
                '0': '0 - Pessimo', '1': '1 - Molto cattivo', '2': '2 - Cattivo',
                '3': '3 - Discreto', '4': '4 - Buono', '5': '5 - Ottimo'
            }
            self.combo_stato_conservazione.addItem(desc_map.get(val, val), val)

        # Popola combo US
        self.populate_us_combo()

    def populate_us_combo(self):
        """Popola la combo box con le US"""
        self.combo_us.clear()
        self.combo_us.addItem("Seleziona US...", None)

        us_list = self.db.get_us_list()
        for us in us_list:
            label = f"{us['sito']} - {us['area']} - US {us['us']}"
            self.combo_us.addItem(label, us['id_us'])

    def on_us_selected(self, index):
        """Gestisce la selezione di una US"""
        id_us = self.combo_us.currentData()

        if id_us:
            us_data = self.db.get_us_by_id(id_us)
            if us_data:
                self.txt_sito.setText(us_data.get('sito', ''))
                self.txt_area.setText(us_data.get('area', ''))
                self.txt_saggio.setText(us_data.get('saggio', ''))
                self.txt_datazione_us.setText(us_data.get('datazione', ''))
        else:
            self.txt_sito.clear()
            self.txt_area.clear()
            self.txt_saggio.clear()
            self.txt_datazione_us.clear()

    def load_records(self, filters: Dict = None):
        """Carica i record dal database"""
        self.records = self.db.get_all_fauna_records(filters)
        self.populate_combos()

        if self.records:
            self.current_index = 0
            self.display_record(self.records[0])
        else:
            self.current_index = -1
            self.clear_form()

        self.update_navigation_buttons()
        self.update_record_info()

    def display_record(self, record: Dict):
        """Visualizza un record nel form"""
        if not record:
            return

        self.current_record_id = record.get('id_fauna')

        # Dati identificativi
        self.txt_id_fauna.setText(str(record.get('id_fauna', '')))

        # Trova e seleziona la US corretta
        id_us = record.get('id_us')
        if id_us:
            for i in range(self.combo_us.count()):
                if self.combo_us.itemData(i) == id_us:
                    self.combo_us.setCurrentIndex(i)
                    break

        # Dati deposizionali
        self.txt_responsabile.setText(record.get('responsabile_scheda', ''))

        data_comp = record.get('data_compilazione')
        if data_comp:
            try:
                date = QDate.fromString(data_comp, "yyyy-MM-dd")
                self.date_compilazione.setDate(date)
            except:
                self.date_compilazione.setDate(QDate.currentDate())
        else:
            self.date_compilazione.setDate(QDate.currentDate())

        self.txt_doc_fotografica.setText(record.get('documentazione_fotografica', ''))
        self.set_combo_value(self.combo_metodologia, record.get('metodologia_recupero', ''))
        self.set_combo_value(self.combo_contesto, record.get('contesto', ''))
        self.txt_desc_contesto.setPlainText(record.get('descrizione_contesto', ''))

        # Dati archeozoologici
        self.set_combo_value(self.combo_connessione, record.get('resti_connessione_anatomica', ''))
        self.set_combo_value(self.combo_tipologia_accumulo, record.get('tipologia_accumulo', ''))
        self.set_combo_value(self.combo_deposizione, record.get('deposizione', ''))
        self.set_combo_value(self.combo_num_stimato, record.get('numero_stimato_resti', ''))

        nmi = record.get('numero_minimo_individui', 0)
        self.spin_nmi.setValue(float(nmi) if nmi else 0)

        self.set_combo_value(self.combo_specie, record.get('specie', ''))
        self.set_combo_value(self.combo_parti_scheletriche, record.get('parti_scheletriche', ''))

        misure = record.get('misure_ossa', 0)
        self.spin_misure.setValue(float(misure) if misure else 0)

        # Dati tafonomici
        self.set_combo_value(self.combo_frammentazione, record.get('stato_frammentazione', ''))
        self.set_combo_value(self.combo_tracce_combustione, record.get('tracce_combustione', ''))
        self.check_combustione_altri.setChecked(bool(record.get('combustione_altri_materiali_us', False)))
        self.set_combo_value(self.combo_tipo_combustione, record.get('tipo_combustione', ''))
        self.set_combo_value(self.combo_segni_tafonomici, record.get('segni_tafonomici_evidenti', ''))
        self.set_combo_value(self.combo_caratterizzazione_tafonomici, record.get('caratterizzazione_segni_tafonomici', ''))
        self.set_combo_value(self.combo_stato_conservazione, record.get('stato_conservazione', ''))
        self.txt_alterazioni.setText(record.get('alterazioni_morfologiche', ''))

        # Dati contestuali
        self.txt_note_terreno.setPlainText(record.get('note_terreno_giacitura', ''))
        self.txt_campionature.setPlainText(record.get('campionature_effettuate', ''))
        self.txt_affidabilita.setPlainText(record.get('affidabilita_stratigrafica', ''))
        self.txt_classi_reperti.setPlainText(record.get('classi_reperti_associazione', ''))
        self.txt_osservazioni.setPlainText(record.get('osservazioni', ''))
        self.txt_interpretazione.setPlainText(record.get('interpretazione', ''))

    def set_combo_value(self, combo: QComboBox, value: str):
        """Imposta il valore di una combo box"""
        if not value:
            combo.setCurrentIndex(0)
            return

        # Cerca per valore
        index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            # Cerca per data
            index = combo.findData(value)
            if index >= 0:
                combo.setCurrentIndex(index)
            else:
                # Se non trovato, imposta come testo (per combo editabili)
                if combo.isEditable():
                    combo.setCurrentText(value)

    def get_form_data(self) -> Dict:
        """Recupera i dati dal form"""
        data = {}

        # ID US
        data['id_us'] = self.combo_us.currentData()

        # Dati identificativi (read-only, ma li includiamo per completezza)
        data['sito'] = self.txt_sito.text()
        data['area'] = self.txt_area.text()
        data['saggio'] = self.txt_saggio.text()
        data['us'] = self.combo_us.currentText().split('US ')[-1] if 'US' in self.combo_us.currentText() else ''
        data['datazione_us'] = self.txt_datazione_us.text()

        # Dati deposizionali
        data['responsabile_scheda'] = self.txt_responsabile.text()
        data['data_compilazione'] = self.date_compilazione.date().toString("yyyy-MM-dd")
        data['documentazione_fotografica'] = self.txt_doc_fotografica.text()
        data['metodologia_recupero'] = self.combo_metodologia.currentText()
        data['contesto'] = self.combo_contesto.currentText()
        data['descrizione_contesto'] = self.txt_desc_contesto.toPlainText()

        # Dati archeozoologici
        data['resti_connessione_anatomica'] = self.combo_connessione.currentText()
        data['tipologia_accumulo'] = self.combo_tipologia_accumulo.currentText()
        data['deposizione'] = self.combo_deposizione.currentText()
        data['numero_stimato_resti'] = self.combo_num_stimato.currentText()
        data['numero_minimo_individui'] = self.spin_nmi.value()
        data['specie'] = self.combo_specie.currentText()
        data['parti_scheletriche'] = self.combo_parti_scheletriche.currentText()
        data['misure_ossa'] = self.spin_misure.value()

        # Dati tafonomici
        data['stato_frammentazione'] = self.combo_frammentazione.currentText()
        data['tracce_combustione'] = self.combo_tracce_combustione.currentText()
        data['combustione_altri_materiali_us'] = 1 if self.check_combustione_altri.isChecked() else 0
        data['tipo_combustione'] = self.combo_tipo_combustione.currentText()
        data['segni_tafonomici_evidenti'] = self.combo_segni_tafonomici.currentText()
        data['caratterizzazione_segni_tafonomici'] = self.combo_caratterizzazione_tafonomici.currentText()

        # Per stato conservazione, usa il data se disponibile
        stato_cons = self.combo_stato_conservazione.currentData()
        if stato_cons is None:
            stato_cons = self.combo_stato_conservazione.currentText().split(' -')[0].strip()
        data['stato_conservazione'] = stato_cons

        data['alterazioni_morfologiche'] = self.txt_alterazioni.text()

        # Dati contestuali
        data['note_terreno_giacitura'] = self.txt_note_terreno.toPlainText()
        data['campionature_effettuate'] = self.txt_campionature.toPlainText()
        data['affidabilita_stratigrafica'] = self.txt_affidabilita.toPlainText()
        data['classi_reperti_associazione'] = self.txt_classi_reperti.toPlainText()
        data['osservazioni'] = self.txt_osservazioni.toPlainText()
        data['interpretazione'] = self.txt_interpretazione.toPlainText()

        return data

    def clear_form(self):
        """Pulisce il form"""
        self.current_record_id = None
        self.txt_id_fauna.clear()
        self.combo_us.setCurrentIndex(0)
        self.txt_responsabile.clear()
        self.date_compilazione.setDate(QDate.currentDate())
        self.txt_doc_fotografica.clear()
        self.txt_desc_contesto.clear()
        self.spin_nmi.setValue(0)
        self.spin_misure.setValue(0)
        self.txt_alterazioni.clear()
        self.txt_note_terreno.clear()
        self.txt_campionature.clear()
        self.txt_affidabilita.clear()
        self.txt_classi_reperti.clear()
        self.txt_osservazioni.clear()
        self.txt_interpretazione.clear()
        self.check_combustione_altri.setChecked(False)

        # Reset combo boxes
        for combo in [self.combo_metodologia, self.combo_contesto, self.combo_connessione,
                      self.combo_tipologia_accumulo, self.combo_deposizione, self.combo_num_stimato,
                      self.combo_specie, self.combo_parti_scheletriche, self.combo_frammentazione,
                      self.combo_tracce_combustione, self.combo_tipo_combustione,
                      self.combo_segni_tafonomici, self.combo_caratterizzazione_tafonomici,
                      self.combo_stato_conservazione]:
            combo.setCurrentIndex(0)

    def new_record(self):
        """Crea un nuovo record"""
        self.clear_form()
        self.current_record_id = None
        self.current_index = -1
        self.update_navigation_buttons()
        self.update_record_info()

    def save_record(self):
        """Salva il record corrente"""
        # Validazione base
        if not self.combo_us.currentData():
            QMessageBox.warning(self, "Attenzione", "Seleziona una US prima di salvare!")
            return

        data = self.get_form_data()

        try:
            if self.current_record_id:
                # Aggiorna record esistente
                success = self.db.update_fauna_record(self.current_record_id, data)
                if success:
                    QMessageBox.information(self, "Successo", "Record aggiornato con successo!")
                    self.load_records()  # Ricarica per aggiornare la lista
            else:
                # Inserisci nuovo record
                new_id = self.db.insert_fauna_record(data)
                self.current_record_id = new_id
                QMessageBox.information(self, "Successo", f"Nuovo record creato con ID: {new_id}")
                self.load_records()  # Ricarica per aggiornare la lista

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel salvataggio: {str(e)}")

    def delete_record(self):
        """Elimina il record corrente"""
        if not self.current_record_id:
            QMessageBox.warning(self, "Attenzione", "Nessun record da eliminare!")
            return

        reply = QMessageBox.question(
            self, "Conferma",
            "Sei sicuro di voler eliminare questo record?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                success = self.db.delete_fauna_record(self.current_record_id)
                if success:
                    QMessageBox.information(self, "Successo", "Record eliminato con successo!")
                    self.load_records()
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore nell'eliminazione: {str(e)}")

    def first_record(self):
        """Va al primo record"""
        if self.records:
            self.current_index = 0
            self.display_record(self.records[0])
            self.update_navigation_buttons()
            self.update_record_info()

    def previous_record(self):
        """Va al record precedente"""
        if self.records and self.current_index > 0:
            self.current_index -= 1
            self.display_record(self.records[self.current_index])
            self.update_navigation_buttons()
            self.update_record_info()

    def next_record(self):
        """Va al record successivo"""
        if self.records and self.current_index < len(self.records) - 1:
            self.current_index += 1
            self.display_record(self.records[self.current_index])
            self.update_navigation_buttons()
            self.update_record_info()

    def last_record(self):
        """Va all'ultimo record"""
        if self.records:
            self.current_index = len(self.records) - 1
            self.display_record(self.records[-1])
            self.update_navigation_buttons()
            self.update_record_info()

    def search_records(self):
        """Apre il dialog di ricerca"""
        dialog = FaunaSearchDialog(self.db, self)

        if dialog.exec_() == QDialog.Accepted:
            search_term = dialog.get_search_term()
            filters = dialog.get_filters()

            if search_term:
                self.records = self.db.search_fauna_records(search_term)
            else:
                self.records = self.db.get_all_fauna_records(filters)

            if self.records:
                self.current_index = 0
                self.display_record(self.records[0])
            else:
                self.current_index = -1
                self.clear_form()
                QMessageBox.information(self, "Ricerca", "Nessun record trovato")

            self.update_navigation_buttons()
            self.update_record_info()

    def manage_vocabulary(self):
        """Apre l'interfaccia di gestione del vocabolario"""
        try:
            from vocabulary_manager import VocabularyManagerDialog

            dialog = VocabularyManagerDialog(self.db, self)
            dialog.exec_()

            # Ricarica i valori delle combo box dopo la modifica del vocabolario
            self.populate_combos()

        except ImportError:
            QMessageBox.warning(
                self, "Modulo non disponibile",
                "Il modulo di gestione vocabolario non è disponibile."
            )
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'apertura gestione vocabolario: {str(e)}")

    def change_database(self):
        """Cambia il database connesso"""
        try:
            # Mostra dialog di selezione database
            dialog = DatabaseSelectorDialog(self)

            if dialog.exec_() == QDialog.Accepted:
                # Ottieni la nuova configurazione
                new_config = dialog.get_db_config()

                # Conferma il cambio database
                reply = QMessageBox.question(
                    self,
                    "Conferma cambio database",
                    f"Cambiare database a:\n{self.format_db_config(new_config)}\n\nEventuali modifiche non salvate andranno perse.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    # Chiudi la connessione corrente
                    if self.db:
                        self.db.close()

                    # Crea nuova connessione (chiamerà automaticamente ensure_tables_exist)
                    print("\n🔄 Cambio database in corso...")
                    self.db = create_fauna_db(db_config=new_config)
                    print("✅ Connessione al nuovo database stabilita!")

                    # Reset dello stato
                    self.current_record_id = None
                    self.current_index = -1

                    # Ricarica tutto
                    self.populate_combos()
                    self.load_records()

                    QMessageBox.information(
                        self,
                        "Database cambiato",
                        "Database cambiato con successo!\nLe tabelle sono state verificate/create automaticamente."
                    )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Errore",
                f"Errore nel cambio database:\n{str(e)}"
            )
            import traceback
            traceback.print_exc()

    def format_db_config(self, config: Dict) -> str:
        """Formatta la configurazione database per visualizzazione"""
        if config['type'] == 'sqlite':
            return f"SQLite: {config['path']}"
        else:
            return f"PostgreSQL: {config['user']}@{config['host']}:{config['port']}/{config['database']}"

    def export_pdf(self):
        """Esporta il record corrente in PDF"""
        if not self.current_record_id:
            QMessageBox.warning(self, "Attenzione", "Nessun record da esportare!")
            return

        try:
            from fauna_pdf import FaunaPDFExporter

            record = self.db.get_fauna_record(self.current_record_id)
            if record:
                exporter = FaunaPDFExporter()
                filename = f"Scheda_FR_{record['sito']}_{record['area']}_US{record['us']}.pdf"

                pdf_path = exporter.export_record(record, filename)
                QMessageBox.information(self, "Successo", f"PDF esportato in: {pdf_path}")

        except ImportError:
            QMessageBox.warning(
                self, "Modulo non disponibile",
                "Il modulo di esportazione PDF non è disponibile. Implementare fauna_pdf.py"
            )
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'esportazione PDF: {str(e)}")

    def update_navigation_buttons(self):
        """Aggiorna lo stato dei bottoni di navigazione"""
        has_records = len(self.records) > 0
        is_first = self.current_index <= 0
        is_last = self.current_index >= len(self.records) - 1

        self.act_first.setEnabled(has_records and not is_first)
        self.act_prev.setEnabled(has_records and not is_first)
        self.act_next.setEnabled(has_records and not is_last)
        self.act_last.setEnabled(has_records and not is_last)

        self.act_delete.setEnabled(self.current_record_id is not None)
        self.act_export_pdf.setEnabled(self.current_record_id is not None)

    def update_record_info(self):
        """Aggiorna l'etichetta con le informazioni sul record corrente"""
        if self.records and self.current_index >= 0:
            info = f"Record {self.current_index + 1} di {len(self.records)}"
            if self.current_record_id:
                info += f" (ID: {self.current_record_id})"
            self.lbl_record_info.setText(info)
        else:
            self.lbl_record_info.setText("Nessun record" if not self.records else "Nuovo record")

    def closeEvent(self, event):
        """Gestisce la chiusura del widget"""
        self.db.close()
        event.accept()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = FaunaManager()
    window.show()
    sys.exit(app.exec_())