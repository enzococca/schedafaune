"""
Interfaccia Qt per la gestione dei dati faunistici
Integrabile con QGIS tramite le proprietà dei layer
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QLineEdit,
    QComboBox, QTextEdit, QDateEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QPushButton, QToolBar, QMessageBox, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QDialogButtonBox, QHeaderView, QAction,
    QGroupBox, QGridLayout, QSplitter, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from typing import Dict, List, Optional
from datetime import datetime
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

        # Toolbars
        self.create_toolbars()
        main_layout.addWidget(self.nav_toolbar)
        main_layout.addWidget(self.action_toolbar)

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

        # Tab 5: Statistiche
        self.tab_statistiche = self.create_tab_statistiche()
        self.tab_widget.addTab(self.tab_statistiche, "📊 Statistiche")

        main_layout.addWidget(self.tab_widget)

    def create_toolbars(self):
        """Crea le toolbars separate per navigazione e azioni"""

        # ========== TOOLBAR NAVIGAZIONE ==========
        self.nav_toolbar = QToolBar("Navigazione Record")
        self.nav_toolbar.setMovable(False)

        # Navigazione
        self.act_first = QAction("⏮ Primo", self)
        self.act_first.triggered.connect(self.first_record)
        self.nav_toolbar.addAction(self.act_first)

        self.act_prev = QAction("◀ Precedente", self)
        self.act_prev.triggered.connect(self.previous_record)
        self.nav_toolbar.addAction(self.act_prev)

        self.act_next = QAction("Successivo ▶", self)
        self.act_next.triggered.connect(self.next_record)
        self.nav_toolbar.addAction(self.act_next)

        self.act_last = QAction("Ultimo ⏭", self)
        self.act_last.triggered.connect(self.last_record)
        self.nav_toolbar.addAction(self.act_last)

        # ========== TOOLBAR AZIONI ==========
        self.action_toolbar = QToolBar("Azioni")
        self.action_toolbar.setMovable(False)

        # Gestione record
        self.act_new = QAction("➕ Nuovo", self)
        self.act_new.triggered.connect(self.new_record)
        self.action_toolbar.addAction(self.act_new)

        self.act_save = QAction("💾 Salva", self)
        self.act_save.triggered.connect(self.save_record)
        self.action_toolbar.addAction(self.act_save)

        self.act_delete = QAction("🗑 Elimina", self)
        self.act_delete.triggered.connect(self.delete_record)
        self.action_toolbar.addAction(self.act_delete)

        self.action_toolbar.addSeparator()

        # Ricerca
        self.act_search = QAction("🔍 Cerca", self)
        self.act_search.triggered.connect(self.search_records)
        self.action_toolbar.addAction(self.act_search)

        self.action_toolbar.addSeparator()

        # Gestione Vocabolario
        self.act_vocabulary = QAction("📚 Gestione Vocabolario", self)
        self.act_vocabulary.triggered.connect(self.manage_vocabulary)
        self.action_toolbar.addAction(self.act_vocabulary)

        self.action_toolbar.addSeparator()

        # Cambia Database
        self.act_change_db = QAction("🔄 Cambia Database", self)
        self.act_change_db.triggered.connect(self.change_database)
        self.action_toolbar.addAction(self.act_change_db)

        self.action_toolbar.addSeparator()

        # Esportazione
        self.act_export_pdf = QAction("📄 Esporta PDF", self)
        self.act_export_pdf.triggered.connect(self.export_pdf)
        self.action_toolbar.addAction(self.act_export_pdf)

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

        # Campo Nome US separato (solo numero US)
        self.txt_us = QLineEdit()
        self.txt_us.setReadOnly(True)
        form_id.addRow("Nome US:", self.txt_us)

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
        self.txt_desc_contesto.setMinimumHeight(80)
        self.txt_desc_contesto.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_dep.addRow("Descrizione Contesto:", self.txt_desc_contesto)

        layout.addWidget(group_dep)

        return widget

    def create_tab_archeozoologici(self) -> QWidget:
        """Crea il tab dei dati archeozoologici"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Usa QGridLayout per una distribuzione più equilibrata
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)  # La colonna dei widget si espande

        row = 0

        # Connessione Anatomica
        grid.addWidget(QLabel("Connessione Anatomica:"), row, 0)
        self.combo_connessione = QComboBox()
        self.combo_connessione.setEditable(True)
        self.combo_connessione.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.combo_connessione, row, 1)
        row += 1

        # Tipologia Accumulo
        grid.addWidget(QLabel("Tipologia Accumulo:"), row, 0)
        self.combo_tipologia_accumulo = QComboBox()
        self.combo_tipologia_accumulo.setEditable(True)
        self.combo_tipologia_accumulo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.combo_tipologia_accumulo, row, 1)
        row += 1

        # Deposizione
        grid.addWidget(QLabel("Deposizione:"), row, 0)
        self.combo_deposizione = QComboBox()
        self.combo_deposizione.setEditable(True)
        self.combo_deposizione.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.combo_deposizione, row, 1)
        row += 1

        # Numero Stimato Resti
        grid.addWidget(QLabel("Numero Stimato Resti:"), row, 0)
        self.combo_num_stimato = QComboBox()
        self.combo_num_stimato.setEditable(True)
        self.combo_num_stimato.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.combo_num_stimato, row, 1)
        row += 1

        # NMI - Cambiato da QDoubleSpinBox a QSpinBox (solo interi)
        grid.addWidget(QLabel("NMI (Numero Minimo Individui):"), row, 0)
        self.spin_nmi = QSpinBox()
        self.spin_nmi.setMaximum(9999)
        self.spin_nmi.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.spin_nmi, row, 1)
        row += 1

        layout.addLayout(grid)

        # ========== TABELLA SPECIE E PSI ==========
        layout.addWidget(QLabel("<b>Specie e Parti Scheletriche (PSI):</b>"))

        # Toolbar per tabella specie/PSI
        toolbar_specie = QToolBar()
        toolbar_specie.setMovable(False)
        btn_add_specie = toolbar_specie.addAction("➕ Aggiungi Riga")
        btn_add_specie.triggered.connect(self.add_specie_psi_row)
        btn_remove_specie = toolbar_specie.addAction("➖ Rimuovi Riga")
        btn_remove_specie.triggered.connect(self.remove_specie_psi_row)
        layout.addWidget(toolbar_specie)

        # Tabella Specie e PSI
        self.table_specie_psi = QTableWidget()
        self.table_specie_psi.setColumnCount(2)
        self.table_specie_psi.setHorizontalHeaderLabels(["Specie", "PSI (Parti Scheletriche)"])
        self.table_specie_psi.horizontalHeader().setStretchLastSection(True)
        self.table_specie_psi.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_specie_psi.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_specie_psi.setMinimumHeight(150)
        self.table_specie_psi.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table_specie_psi)

        # ========== TABELLA MISURE ==========
        layout.addWidget(QLabel("<b>Misure Ossa:</b>"))

        # Toolbar per tabella misure
        toolbar_misure = QToolBar()
        toolbar_misure.setMovable(False)
        btn_add_misura = toolbar_misure.addAction("➕ Aggiungi Riga")
        btn_add_misura.triggered.connect(self.add_misura_row)
        btn_remove_misura = toolbar_misure.addAction("➖ Rimuovi Riga")
        btn_remove_misura.triggered.connect(self.remove_misura_row)
        layout.addWidget(toolbar_misure)

        # Tabella Misure (6 colonne)
        self.table_misure = QTableWidget()
        self.table_misure.setColumnCount(6)
        self.table_misure.setHorizontalHeaderLabels([
            "Elemento Anatomico", "Specie", "GL (mm)", "GB (mm)", "Bp (mm)", "Bd (mm)"
        ])
        self.table_misure.horizontalHeader().setStretchLastSection(True)
        for i in range(6):
            self.table_misure.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        self.table_misure.setMinimumHeight(150)
        self.table_misure.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table_misure)

        layout.addStretch()

        return widget

    def create_tab_tafonomici(self) -> QWidget:
        """Crea il tab dei dati tafonomici"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Usa QGridLayout per una distribuzione più equilibrata
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)  # La colonna dei widget si espande

        row = 0

        # Stato Frammentazione
        grid.addWidget(QLabel("Stato Frammentazione:"), row, 0)
        self.combo_frammentazione = QComboBox()
        self.combo_frammentazione.setEditable(True)
        self.combo_frammentazione.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.combo_frammentazione, row, 1)
        row += 1

        # Tracce Combustione
        grid.addWidget(QLabel("Tracce Combustione:"), row, 0)
        self.combo_tracce_combustione = QComboBox()
        self.combo_tracce_combustione.setEditable(True)
        self.combo_tracce_combustione.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.combo_tracce_combustione, row, 1)
        row += 1

        # Combustione su Altri Materiali
        grid.addWidget(QLabel("Combustione su Altri Materiali US:"), row, 0)
        self.check_combustione_altri = QCheckBox()
        grid.addWidget(self.check_combustione_altri, row, 1)
        row += 1

        # Tipo Combustione
        grid.addWidget(QLabel("Tipo Combustione:"), row, 0)
        self.combo_tipo_combustione = QComboBox()
        self.combo_tipo_combustione.setEditable(True)
        self.combo_tipo_combustione.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.combo_tipo_combustione, row, 1)
        row += 1

        # Segni Tafonomici Evidenti
        grid.addWidget(QLabel("Segni Tafonomici Evidenti:"), row, 0)
        self.combo_segni_tafonomici = QComboBox()
        self.combo_segni_tafonomici.setEditable(True)
        self.combo_segni_tafonomici.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.combo_segni_tafonomici, row, 1)
        row += 1

        # Caratterizzazione Segni
        grid.addWidget(QLabel("Caratterizzazione Segni:"), row, 0)
        self.combo_caratterizzazione_tafonomici = QComboBox()
        self.combo_caratterizzazione_tafonomici.setEditable(True)
        self.combo_caratterizzazione_tafonomici.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.combo_caratterizzazione_tafonomici, row, 1)
        row += 1

        # Stato Conservazione
        grid.addWidget(QLabel("Stato Conservazione:"), row, 0)
        self.combo_stato_conservazione = QComboBox()
        self.combo_stato_conservazione.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.combo_stato_conservazione, row, 1)
        row += 1

        # Alterazioni Morfologiche
        grid.addWidget(QLabel("Alterazioni Morfologiche:"), row, 0)
        self.txt_alterazioni = QLineEdit()
        self.txt_alterazioni.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        grid.addWidget(self.txt_alterazioni, row, 1)

        layout.addLayout(grid)
        layout.addStretch()

        return widget

    def create_tab_contestuali(self) -> QWidget:
        """Crea il tab dei dati contestuali"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Configura i QTextEdit per espandersi e adattarsi al ridimensionamento
        # Usa QVBoxLayout invece di QFormLayout per permettere l'espansione completa in larghezza

        # Note Terreno Giacitura
        lbl_note_terreno = QLabel("Note Terreno Giacitura:")
        layout.addWidget(lbl_note_terreno)
        self.txt_note_terreno = QTextEdit()
        self.txt_note_terreno.setMinimumHeight(60)
        self.txt_note_terreno.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.txt_note_terreno)

        # Campionature Effettuate
        lbl_campionature = QLabel("Campionature Effettuate:")
        layout.addWidget(lbl_campionature)
        self.txt_campionature = QTextEdit()
        self.txt_campionature.setMinimumHeight(60)
        self.txt_campionature.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.txt_campionature)

        # Affidabilità Stratigrafica
        lbl_affidabilita = QLabel("Affidabilità Stratigrafica:")
        layout.addWidget(lbl_affidabilita)
        self.txt_affidabilita = QTextEdit()
        self.txt_affidabilita.setMinimumHeight(60)
        self.txt_affidabilita.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.txt_affidabilita)

        # Classi Reperti Associazione
        lbl_classi_reperti = QLabel("Classi Reperti Associazione:")
        layout.addWidget(lbl_classi_reperti)
        self.txt_classi_reperti = QTextEdit()
        self.txt_classi_reperti.setMinimumHeight(60)
        self.txt_classi_reperti.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.txt_classi_reperti)

        # Osservazioni
        lbl_osservazioni = QLabel("Osservazioni:")
        layout.addWidget(lbl_osservazioni)
        self.txt_osservazioni = QTextEdit()
        self.txt_osservazioni.setMinimumHeight(80)
        self.txt_osservazioni.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.txt_osservazioni)

        # Interpretazione
        lbl_interpretazione = QLabel("Interpretazione:")
        layout.addWidget(lbl_interpretazione)
        self.txt_interpretazione = QTextEdit()
        self.txt_interpretazione.setMinimumHeight(80)
        self.txt_interpretazione.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.txt_interpretazione)

        return widget

    def create_tab_statistiche(self) -> QWidget:
        """Crea il tab delle statistiche riepilogative"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar con pulsanti per aggiornare ed esportare
        toolbar_layout = QHBoxLayout()

        btn_refresh = QPushButton("🔄 Aggiorna Statistiche")
        btn_refresh.clicked.connect(self.update_statistics)
        toolbar_layout.addWidget(btn_refresh)

        btn_export_excel = QPushButton("📊 Esporta Excel")
        btn_export_excel.clicked.connect(self.export_statistics_excel)
        toolbar_layout.addWidget(btn_export_excel)

        btn_export_pdf = QPushButton("📄 Esporta PDF")
        btn_export_pdf.clicked.connect(self.export_statistics_pdf)
        toolbar_layout.addWidget(btn_export_pdf)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # Area di testo per le statistiche
        self.txt_statistiche = QTextEdit()
        self.txt_statistiche.setReadOnly(True)
        self.txt_statistiche.setFont(QFont("Courier", 9))
        layout.addWidget(self.txt_statistiche)

        # Variabile per memorizzare le statistiche correnti
        self.current_stats_text = []
        self.current_stats_data = {}

        return widget

    def update_statistics(self):
        """Calcola e visualizza le statistiche riepilogative estese"""
        try:
            records = self.db.get_all_fauna_records()

            if not records:
                self.txt_statistiche.setText("Nessun record presente nel database.")
                return

            stats_text = []
            stats_text.append("=" * 100)
            stats_text.append("STATISTICHE RIEPILOGATIVE - SCHEDE FAUNA")
            stats_text.append("=" * 100)
            stats_text.append("")

            # === STATISTICHE GENERALI ===
            stats_text.append("📋 STATISTICHE GENERALI")
            stats_text.append("-" * 100)
            stats_text.append(f"Numero totale record: {len(records)}")

            siti = set(r.get('sito', '') for r in records if r.get('sito'))
            aree = set(r.get('area', '') for r in records if r.get('area'))
            saggi = set(r.get('saggio', '') for r in records if r.get('saggio'))
            us_list = set(r.get('us', '') for r in records if r.get('us'))

            stats_text.append(f"Numero siti univoci: {len(siti)}")
            if siti:
                stats_text.append(f"  Siti: {', '.join(sorted(siti))}")
            stats_text.append(f"Numero aree univoche: {len(aree)}")
            stats_text.append(f"Numero saggi univoci: {len(saggi)}")
            stats_text.append(f"Numero US univoche: {len(us_list)}")

            # Combinazioni Area+Saggio+US univoche
            combinazioni = set()
            for r in records:
                sito = r.get('sito', '')
                area = r.get('area', '')
                saggio = r.get('saggio', '')
                us = r.get('us', '')
                if sito and area and saggio and us:
                    combinazioni.add((sito, area, saggio, us))
            stats_text.append(f"Numero combinazioni Sito+Area+Saggio+US univoche: {len(combinazioni)}")
            stats_text.append("")

            # === STATISTICHE NUMERICHE GENERALI ===
            stats_text.append("🔢 STATISTICHE NUMERICHE - RIEPILOGO GENERALE")
            stats_text.append("-" * 100)

            nmi_values = [int(r['numero_minimo_individui']) for r in records
                         if r.get('numero_minimo_individui') not in (None, '', 0)]
            if nmi_values:
                stats_text.append(f"Numero Minimo Individui (NMI):")
                stats_text.append(f"  Totale record con NMI: {len(nmi_values)}")
                stats_text.append(f"  Media: {sum(nmi_values)/len(nmi_values):.1f}")
                stats_text.append(f"  Minimo: {min(nmi_values)}")
                stats_text.append(f"  Massimo: {max(nmi_values)}")
                stats_text.append(f"  Somma totale: {sum(nmi_values)}")

            # Parti Scheletriche (PSI) - distribuzione generale
            all_psi = {}
            for r in records:
                psi_list = self._extract_psi_from_record(r)
                for psi in psi_list:
                    if psi:
                        all_psi[psi] = all_psi.get(psi, 0) + 1

            if all_psi:
                stats_text.append(f"\nParti Scheletriche (PSI) - Distribuzione:")
                stats_text.append(f"  Totale parti identificate: {sum(all_psi.values())}")
                stats_text.append(f"  Tipi di parti univoche: {len(all_psi)}")
                sorted_psi = sorted(all_psi.items(), key=lambda x: x[1], reverse=True)[:10]
                for psi, cnt in sorted_psi:
                    pct = (cnt / sum(all_psi.values())) * 100
                    stats_text.append(f"  - {psi}: {cnt} ({pct:.1f}%)")

            # Associazioni Specie-PSI
            specie_psi_assoc = {}
            for r in records:
                pairs = self._extract_specie_psi_pairs_from_record(r)
                for specie, psi in pairs:
                    if specie and psi:
                        key = f"{specie} → {psi}"
                        specie_psi_assoc[key] = specie_psi_assoc.get(key, 0) + 1

            if specie_psi_assoc:
                stats_text.append(f"\nAssociazioni Specie-PSI più frequenti:")
                sorted_assoc = sorted(specie_psi_assoc.items(), key=lambda x: x[1], reverse=True)[:10]
                for assoc, cnt in sorted_assoc:
                    stats_text.append(f"  - {assoc}: {cnt}")

            # Misure Ossa (supporta JSON) - statistiche generali
            misure_values = []
            for r in records:
                measurements = self._extract_measurements_from_record(r)
                misure_values.extend(measurements)

            if misure_values:
                stats_text.append(f"\nMisure Ossa (mm) - Riepilogo:")
                stats_text.append(f"  Totale misurazioni: {len(misure_values)}")
                stats_text.append(f"  Media: {sum(misure_values)/len(misure_values):.2f} mm")
                stats_text.append(f"  Minimo: {min(misure_values):.2f} mm")
                stats_text.append(f"  Massimo: {max(misure_values):.2f} mm")

            # Misure dettagliate per tipo (GL, GB, Bp, Bd)
            all_detailed_measures = []
            for r in records:
                detailed = self._extract_detailed_measurements_from_record(r)
                all_detailed_measures.extend(detailed)

            if all_detailed_measures:
                stats_text.append(f"\nMisure dettagliate per tipo:")
                gl_vals = [m['GL'] for m in all_detailed_measures if m['GL'] > 0]
                gb_vals = [m['GB'] for m in all_detailed_measures if m['GB'] > 0]
                bp_vals = [m['Bp'] for m in all_detailed_measures if m['Bp'] > 0]
                bd_vals = [m['Bd'] for m in all_detailed_measures if m['Bd'] > 0]

                if gl_vals:
                    stats_text.append(f"  GL (Greatest Length): n={len(gl_vals)}, media={sum(gl_vals)/len(gl_vals):.2f}, min={min(gl_vals):.2f}, max={max(gl_vals):.2f}")
                if gb_vals:
                    stats_text.append(f"  GB (Greatest Breadth): n={len(gb_vals)}, media={sum(gb_vals)/len(gb_vals):.2f}, min={min(gb_vals):.2f}, max={max(gb_vals):.2f}")
                if bp_vals:
                    stats_text.append(f"  Bp (Proximal Breadth): n={len(bp_vals)}, media={sum(bp_vals)/len(bp_vals):.2f}, min={min(bp_vals):.2f}, max={max(bp_vals):.2f}")
                if bd_vals:
                    stats_text.append(f"  Bd (Distal Breadth): n={len(bd_vals)}, media={sum(bd_vals)/len(bd_vals):.2f}, min={min(bd_vals):.2f}, max={max(bd_vals):.2f}")

                # Misure per elemento anatomico
                elementi_count = {}
                for m in all_detailed_measures:
                    if m['elemento']:
                        elementi_count[m['elemento']] = elementi_count.get(m['elemento'], 0) + 1

                if elementi_count:
                    stats_text.append(f"\nMisure per Elemento Anatomico:")
                    sorted_elementi = sorted(elementi_count.items(), key=lambda x: x[1], reverse=True)
                    for el, cnt in sorted_elementi:
                        stats_text.append(f"  - {el}: {cnt} misurazioni")

            stats_text.append("")

            # === STATISTICHE PER SITO ===
            if siti and len(siti) > 0:
                stats_text.append("🏛 STATISTICHE PER SITO")
                stats_text.append("=" * 100)

                for sito in sorted(siti):
                    sito_records = [r for r in records if r.get('sito') == sito]
                    sito_pct = (len(sito_records) / len(records)) * 100

                    stats_text.append(f"\n{'#' * 100}")
                    stats_text.append(f"SITO: {sito}")
                    stats_text.append(f"{'#' * 100}")
                    stats_text.append(f"Totale record: {len(sito_records)} ({sito_pct:.1f}% del totale generale)")

                    # Aree, saggi, US nel sito
                    sito_aree = set(r.get('area', '') for r in sito_records if r.get('area'))
                    sito_saggi = set(r.get('saggio', '') for r in sito_records if r.get('saggio'))
                    sito_us = set(r.get('us', '') for r in sito_records if r.get('us'))

                    stats_text.append(f"Numero aree: {len(sito_aree)}")
                    stats_text.append(f"Numero saggi: {len(sito_saggi)}")
                    stats_text.append(f"Numero US: {len(sito_us)}")

                    # Specie principali nel sito
                    sito_species = {}
                    for r in sito_records:
                        species_list = self._extract_species_from_record(r)
                        for sp in species_list:
                            if sp:
                                sito_species[sp] = sito_species.get(sp, 0) + 1

                    if sito_species:
                        top_species = sorted(sito_species.items(), key=lambda x: x[1], reverse=True)[:5]
                        stats_text.append(f"\nSpecie principali:")
                        for sp, cnt in top_species:
                            sp_pct = (cnt / len(sito_records)) * 100
                            stats_text.append(f"  - {sp}: {cnt} record ({sp_pct:.1f}%)")

                    # NMI totale del sito
                    sito_nmi = [int(r['numero_minimo_individui']) for r in sito_records
                               if r.get('numero_minimo_individui') not in (None, '', 0)]
                    if sito_nmi:
                        stats_text.append(f"\nNMI totale sito: {sum(sito_nmi)}")
                        stats_text.append(f"NMI medio: {sum(sito_nmi)/len(sito_nmi):.1f}")
                        stats_text.append(f"NMI min: {min(sito_nmi)}, max: {max(sito_nmi)}")

                    # PSI per sito
                    sito_psi = {}
                    for r in sito_records:
                        psi_list = self._extract_psi_from_record(r)
                        for psi in psi_list:
                            if psi:
                                sito_psi[psi] = sito_psi.get(psi, 0) + 1
                    if sito_psi:
                        top_psi = sorted(sito_psi.items(), key=lambda x: x[1], reverse=True)[:5]
                        stats_text.append(f"\nParti scheletriche principali:")
                        for psi, cnt in top_psi:
                            stats_text.append(f"  - {psi}: {cnt}")

                    # Misure per sito
                    sito_measures = []
                    for r in sito_records:
                        sito_measures.extend(self._extract_detailed_measurements_from_record(r))
                    if sito_measures:
                        stats_text.append(f"\nMisure ossee: {len(sito_measures)} totali")
                        elem_count = {}
                        for m in sito_measures:
                            if m['elemento']:
                                elem_count[m['elemento']] = elem_count.get(m['elemento'], 0) + 1
                        if elem_count:
                            top_elem = sorted(elem_count.items(), key=lambda x: x[1], reverse=True)[:3]
                            stats_text.append(f"  Elementi misurati: {', '.join([f'{e} ({c})' for e, c in top_elem])}")

                    # === STATISTICHE PER AREA (all'interno del sito) ===
                    if sito_aree and len(sito_aree) > 0:
                        stats_text.append(f"\n{'-' * 100}")
                        stats_text.append(f"📍 STATISTICHE PER AREA (Sito: {sito})")
                        stats_text.append(f"{'-' * 100}")

                        for area in sorted(sito_aree):
                            area_records = [r for r in sito_records if r.get('area') == area]
                            area_pct_sito = (len(area_records) / len(sito_records)) * 100
                            area_pct_totale = (len(area_records) / len(records)) * 100

                            stats_text.append(f"\n  Area: {area}")
                            stats_text.append(f"    Record: {len(area_records)} ({area_pct_sito:.1f}% del sito, {area_pct_totale:.1f}% del totale)")

                            # Specie per area
                            area_species = {}
                            for r in area_records:
                                species_list = self._extract_species_from_record(r)
                                for sp in species_list:
                                    if sp:
                                        area_species[sp] = area_species.get(sp, 0) + 1

                            if area_species:
                                top_species = sorted(area_species.items(), key=lambda x: x[1], reverse=True)[:3]
                                stats_text.append(f"    Specie principali: {', '.join([f'{sp} ({cnt})' for sp, cnt in top_species])}")

                            # NMI per area
                            area_nmi = [int(r['numero_minimo_individui']) for r in area_records
                                       if r.get('numero_minimo_individui') not in (None, '', 0)]
                            if area_nmi:
                                stats_text.append(f"    NMI totale: {sum(area_nmi)}, Media: {sum(area_nmi)/len(area_nmi):.1f}")

                            # PSI per area
                            area_psi = {}
                            for r in area_records:
                                for psi in self._extract_psi_from_record(r):
                                    if psi:
                                        area_psi[psi] = area_psi.get(psi, 0) + 1
                            if area_psi:
                                top_psi = sorted(area_psi.items(), key=lambda x: x[1], reverse=True)[:3]
                                stats_text.append(f"    PSI: {', '.join([f'{p} ({c})' for p, c in top_psi])}")

                            # Misure per area
                            area_measures = []
                            for r in area_records:
                                area_measures.extend(self._extract_detailed_measurements_from_record(r))
                            if area_measures:
                                stats_text.append(f"    Misure: {len(area_measures)} totali")

                    # === STATISTICHE PER SAGGIO (all'interno del sito) ===
                    if sito_saggi and len(sito_saggi) > 0:
                        stats_text.append(f"\n{'-' * 100}")
                        stats_text.append(f"🔬 STATISTICHE PER SAGGIO (Sito: {sito})")
                        stats_text.append(f"{'-' * 100}")

                        for saggio in sorted(sito_saggi):
                            saggio_records = [r for r in sito_records if r.get('saggio') == saggio]
                            saggio_pct_sito = (len(saggio_records) / len(sito_records)) * 100
                            saggio_pct_totale = (len(saggio_records) / len(records)) * 100

                            stats_text.append(f"\n  Saggio: {saggio}")
                            stats_text.append(f"    Record: {len(saggio_records)} ({saggio_pct_sito:.1f}% del sito, {saggio_pct_totale:.1f}% del totale)")

                            # Specie per saggio
                            saggio_species = {}
                            for r in saggio_records:
                                species_list = self._extract_species_from_record(r)
                                for sp in species_list:
                                    if sp:
                                        saggio_species[sp] = saggio_species.get(sp, 0) + 1

                            if saggio_species:
                                top_species = sorted(saggio_species.items(), key=lambda x: x[1], reverse=True)[:3]
                                stats_text.append(f"    Specie principali: {', '.join([f'{sp} ({cnt})' for sp, cnt in top_species])}")

                            # NMI per saggio
                            saggio_nmi = [int(r['numero_minimo_individui']) for r in saggio_records
                                         if r.get('numero_minimo_individui') not in (None, '', 0)]
                            if saggio_nmi:
                                stats_text.append(f"    NMI totale: {sum(saggio_nmi)}, Media: {sum(saggio_nmi)/len(saggio_nmi):.1f}")

                            # PSI per saggio
                            saggio_psi = {}
                            for r in saggio_records:
                                for psi in self._extract_psi_from_record(r):
                                    if psi:
                                        saggio_psi[psi] = saggio_psi.get(psi, 0) + 1
                            if saggio_psi:
                                top_psi = sorted(saggio_psi.items(), key=lambda x: x[1], reverse=True)[:3]
                                stats_text.append(f"    PSI: {', '.join([f'{p} ({c})' for p, c in top_psi])}")

                            # Misure per saggio
                            saggio_measures = []
                            for r in saggio_records:
                                saggio_measures.extend(self._extract_detailed_measurements_from_record(r))
                            if saggio_measures:
                                stats_text.append(f"    Misure: {len(saggio_measures)} totali")

                    # === STATISTICHE PER US (all'interno del sito) ===
                    if sito_us and len(sito_us) > 0:
                        stats_text.append(f"\n{'-' * 100}")
                        stats_text.append(f"🏛 STATISTICHE PER US (Sito: {sito}, Top 10)")
                        stats_text.append(f"{'-' * 100}")

                        # Conta record per US
                        us_counts = {}
                        for r in sito_records:
                            us = r.get('us', '')
                            if us:
                                if us not in us_counts:
                                    us_counts[us] = []
                                us_counts[us].append(r)

                        # Ordina e prendi top 10
                        sorted_us = sorted(us_counts.items(), key=lambda x: len(x[1]), reverse=True)[:10]

                        for us, us_records in sorted_us:
                            us_pct_sito = (len(us_records) / len(sito_records)) * 100
                            us_pct_totale = (len(us_records) / len(records)) * 100

                            stats_text.append(f"\n  US: {us}")
                            stats_text.append(f"    Record: {len(us_records)} ({us_pct_sito:.1f}% del sito, {us_pct_totale:.1f}% del totale)")

                            # Specie per US
                            us_species = {}
                            for r in us_records:
                                species_list = self._extract_species_from_record(r)
                                for sp in species_list:
                                    if sp:
                                        us_species[sp] = us_species.get(sp, 0) + 1

                            if us_species:
                                top_species = sorted(us_species.items(), key=lambda x: x[1], reverse=True)[:3]
                                stats_text.append(f"    Specie principali: {', '.join([f'{sp} ({cnt})' for sp, cnt in top_species])}")

                            # NMI per US
                            us_nmi = [int(r['numero_minimo_individui']) for r in us_records
                                     if r.get('numero_minimo_individui') not in (None, '', 0)]
                            if us_nmi:
                                stats_text.append(f"    NMI totale: {sum(us_nmi)}, Media: {sum(us_nmi)/len(us_nmi):.1f}")

                            # PSI per US
                            us_psi = {}
                            for r in us_records:
                                for psi in self._extract_psi_from_record(r):
                                    if psi:
                                        us_psi[psi] = us_psi.get(psi, 0) + 1
                            if us_psi:
                                top_psi = sorted(us_psi.items(), key=lambda x: x[1], reverse=True)[:3]
                                stats_text.append(f"    PSI: {', '.join([f'{p} ({c})' for p, c in top_psi])}")

                            # Misure per US
                            us_measures = []
                            for r in us_records:
                                us_measures.extend(self._extract_detailed_measurements_from_record(r))
                            if us_measures:
                                stats_text.append(f"    Misure: {len(us_measures)} totali")

                    # === STATISTICHE DETTAGLIATE PER COMBINAZIONE AREA+SAGGIO+US ===
                    stats_text.append(f"\n{'-' * 100}")
                    stats_text.append(f"🔍 COMBINAZIONI AREA + SAGGIO + US (Sito: {sito})")
                    stats_text.append(f"{'-' * 100}")

                    # Raggruppa per combinazione
                    combinazioni_sito = {}
                    for r in sito_records:
                        area = r.get('area', '')
                        saggio = r.get('saggio', '')
                        us = r.get('us', '')
                        if area and saggio and us:
                            key = (area, saggio, us)
                            if key not in combinazioni_sito:
                                combinazioni_sito[key] = []
                            combinazioni_sito[key].append(r)

                    if combinazioni_sito:
                        # Ordina per numero di record
                        sorted_comb = sorted(combinazioni_sito.items(), key=lambda x: len(x[1]), reverse=True)

                        for (area, saggio, us), comb_records in sorted_comb:
                            comb_pct_sito = (len(comb_records) / len(sito_records)) * 100
                            comb_pct_totale = (len(comb_records) / len(records)) * 100

                            stats_text.append(f"\n  Area {area} - Saggio {saggio} - US {us}: {len(comb_records)} record")
                            stats_text.append(f"    {comb_pct_sito:.1f}% del sito | {comb_pct_totale:.1f}% del totale generale")

                            # Specie per combinazione
                            comb_species = {}
                            for r in comb_records:
                                species_list = self._extract_species_from_record(r)
                                for sp in species_list:
                                    if sp:
                                        comb_species[sp] = comb_species.get(sp, 0) + 1

                            if comb_species:
                                top_species = sorted(comb_species.items(), key=lambda x: x[1], reverse=True)[:3]
                                stats_text.append(f"    Specie: {', '.join([f'{sp} ({cnt})' for sp, cnt in top_species])}")

                            # NMI per combinazione
                            comb_nmi = [int(r['numero_minimo_individui']) for r in comb_records
                                       if r.get('numero_minimo_individui') not in (None, '', 0)]
                            if comb_nmi:
                                stats_text.append(f"    NMI totale: {sum(comb_nmi)}, Media: {sum(comb_nmi)/len(comb_nmi):.1f}")

                            # PSI per combinazione
                            comb_psi = {}
                            for r in comb_records:
                                for psi in self._extract_psi_from_record(r):
                                    if psi:
                                        comb_psi[psi] = comb_psi.get(psi, 0) + 1
                            if comb_psi:
                                top_psi = sorted(comb_psi.items(), key=lambda x: x[1], reverse=True)[:3]
                                stats_text.append(f"    PSI: {', '.join([f'{p} ({c})' for p, c in top_psi])}")

                            # Misure per combinazione
                            comb_measures = []
                            for r in comb_records:
                                comb_measures.extend(self._extract_detailed_measurements_from_record(r))
                            if comb_measures:
                                stats_text.append(f"    Misure: {len(comb_measures)} totali")

                stats_text.append(f"\n{'=' * 100}\n")

            # === DISTRIBUZIONE PER CATEGORIE ===
            stats_text.append("📊 DISTRIBUZIONE PER CATEGORIE - RIEPILOGO GENERALE")
            stats_text.append("-" * 100)

            def count_values(field_name, label, top_n=10):
                values_count = {}
                for r in records:
                    val = r.get(field_name, '')
                    if val and val.strip():
                        values_count[val] = values_count.get(val, 0) + 1

                if values_count:
                    stats_text.append(f"\n{label}:")
                    sorted_items = sorted(values_count.items(), key=lambda x: x[1], reverse=True)
                    for val, count in sorted_items[:top_n]:
                        percentage = (count / len(records)) * 100
                        stats_text.append(f"  {val}: {count} ({percentage:.1f}%)")
                else:
                    stats_text.append(f"\n{label}: Nessun dato")

            # Specie - usa estrazione JSON-aware
            all_species = {}
            for r in records:
                species_list = self._extract_species_from_record(r)
                for sp in species_list:
                    if sp and sp.strip():
                        all_species[sp] = all_species.get(sp, 0) + 1
            if all_species:
                stats_text.append(f"\nSpecie (Top 10):")
                sorted_species = sorted(all_species.items(), key=lambda x: x[1], reverse=True)
                for val, count in sorted_species[:10]:
                    percentage = (count / len(records)) * 100
                    stats_text.append(f"  {val}: {count} ({percentage:.1f}%)")
            else:
                stats_text.append(f"\nSpecie (Top 10): Nessun dato")

            # PSI - usa estrazione JSON-aware
            all_psi_cat = {}
            for r in records:
                psi_list = self._extract_psi_from_record(r)
                for psi in psi_list:
                    if psi and psi.strip():
                        all_psi_cat[psi] = all_psi_cat.get(psi, 0) + 1
            if all_psi_cat:
                stats_text.append(f"\nParti Scheletriche - PSI (Top 10):")
                sorted_psi = sorted(all_psi_cat.items(), key=lambda x: x[1], reverse=True)
                for val, count in sorted_psi[:10]:
                    percentage = (count / sum(all_psi_cat.values())) * 100
                    stats_text.append(f"  {val}: {count} ({percentage:.1f}%)")
            else:
                stats_text.append(f"\nParti Scheletriche - PSI (Top 10): Nessun dato")

            # Elementi Anatomici misurati
            all_elementi = {}
            for r in records:
                detailed = self._extract_detailed_measurements_from_record(r)
                for m in detailed:
                    if m['elemento']:
                        all_elementi[m['elemento']] = all_elementi.get(m['elemento'], 0) + 1
            if all_elementi:
                stats_text.append(f"\nElementi Anatomici Misurati:")
                sorted_elem = sorted(all_elementi.items(), key=lambda x: x[1], reverse=True)
                for val, count in sorted_elem:
                    percentage = (count / sum(all_elementi.values())) * 100
                    stats_text.append(f"  {val}: {count} ({percentage:.1f}%)")
            else:
                stats_text.append(f"\nElementi Anatomici Misurati: Nessun dato")

            count_values('contesto', 'Contesto')
            count_values('metodologia_recupero', 'Metodologia di Recupero')
            count_values('stato_conservazione', 'Stato di Conservazione')
            count_values('resti_connessione_anatomica', 'Resti in Connessione Anatomica')
            count_values('tipologia_accumulo', 'Tipologia di Accumulo')
            count_values('tracce_combustione', 'Tracce di Combustione')
            count_values('stato_frammentazione', 'Stato di Frammentazione')

            stats_text.append("")

            # === SOMMARIO DESCRITTIVO ===
            stats_text.append("=" * 100)
            stats_text.append("📝 SOMMARIO DESCRITTIVO")
            stats_text.append("=" * 100)
            stats_text.append("")

            summary = self._generate_descriptive_summary(records, nmi_values, misure_values,
                                                        siti, aree, saggi, us_list)
            stats_text.extend(summary)

            stats_text.append("")
            stats_text.append("=" * 100)
            stats_text.append(f"Report generato il: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            stats_text.append("=" * 100)

            # Salva per esportazione
            self.current_stats_text = stats_text
            self.current_stats_data = {
                'records': records,
                'total': len(records),
                'siti': siti,
                'aree': aree,
                'saggi': saggi,
                'us': us_list,
                'nmi_values': nmi_values,
                'misure_values': misure_values
            }

            # Visualizza
            self.txt_statistiche.setText("\n".join(stats_text))

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nel calcolo delle statistiche:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def _extract_species_from_record(self, record: Dict) -> list:
        """Estrae tutte le specie da un record (supporta sia JSON che campo singolo)"""
        import json
        species = []

        # Prova prima con il nuovo formato JSON
        specie_psi_json = record.get('specie_psi', '')
        if specie_psi_json and specie_psi_json.strip():
            try:
                specie_psi_data = json.loads(specie_psi_json)
                for row in specie_psi_data:
                    if len(row) > 0 and row[0]:
                        species.append(row[0])
            except:
                pass

        # Fallback: usa il campo specie vecchio
        if not species:
            sp = record.get('specie', '')
            if sp:
                species.append(sp)

        return species

    def _extract_measurements_from_record(self, record: Dict) -> list:
        """Estrae tutte le misure da un record (supporta sia JSON che campo singolo)"""
        import json
        measurements = []

        # Prova prima con il nuovo formato JSON
        misure_json = record.get('misure_ossa', '')
        if misure_json and misure_json.strip():
            try:
                misure_data = json.loads(misure_json)
                for row in misure_data:
                    # Row format: [Elemento Anatomico, Specie, GL, GB, Bp, Bd]
                    if len(row) >= 6:
                        # Estrai GL, GB, Bp, Bd (colonne 2-5)
                        for i in range(2, 6):
                            try:
                                val = float(row[i]) if row[i] else 0
                                if val > 0:
                                    measurements.append(val)
                            except (ValueError, TypeError):
                                pass
            except:
                pass

        # Fallback: usa il campo misure_ossa vecchio (numerico)
        if not measurements:
            try:
                val = float(record.get('misure_ossa', 0))
                if val > 0:
                    measurements.append(val)
            except (ValueError, TypeError):
                pass

        return measurements

    def _extract_psi_from_record(self, record: Dict) -> list:
        """Estrae tutte le parti scheletriche (PSI) da un record"""
        import json
        psi_list = []

        # Prova prima con il nuovo formato JSON
        specie_psi_json = record.get('specie_psi', '')
        if specie_psi_json and specie_psi_json.strip():
            try:
                specie_psi_data = json.loads(specie_psi_json)
                for row in specie_psi_data:
                    if len(row) > 1 and row[1]:
                        psi_list.append(row[1])
            except:
                pass

        # Fallback: usa il campo parti_scheletriche vecchio
        if not psi_list:
            psi = record.get('parti_scheletriche', '')
            if psi:
                psi_list.append(psi)

        return psi_list

    def _extract_specie_psi_pairs_from_record(self, record: Dict) -> list:
        """Estrae coppie (specie, psi) da un record"""
        import json
        pairs = []

        specie_psi_json = record.get('specie_psi', '')
        if specie_psi_json and specie_psi_json.strip():
            try:
                specie_psi_data = json.loads(specie_psi_json)
                for row in specie_psi_data:
                    if len(row) >= 2:
                        specie = row[0] if row[0] else ''
                        psi = row[1] if row[1] else ''
                        if specie or psi:
                            pairs.append((specie, psi))
            except:
                pass

        # Fallback
        if not pairs:
            specie = record.get('specie', '')
            psi = record.get('parti_scheletriche', '')
            if specie or psi:
                pairs.append((specie, psi))

        return pairs

    def _extract_detailed_measurements_from_record(self, record: Dict) -> list:
        """Estrae misure dettagliate da un record: [(elemento, specie, GL, GB, Bp, Bd), ...]"""
        import json
        detailed = []

        misure_json = record.get('misure_ossa', '')
        if misure_json and misure_json.strip():
            try:
                misure_data = json.loads(misure_json)
                for row in misure_data:
                    if len(row) >= 6:
                        elemento = row[0] if row[0] else ''
                        specie = row[1] if row[1] else ''
                        gl = self._safe_float(row[2])
                        gb = self._safe_float(row[3])
                        bp = self._safe_float(row[4])
                        bd = self._safe_float(row[5])
                        if elemento or specie or gl or gb or bp or bd:
                            detailed.append({
                                'elemento': elemento,
                                'specie': specie,
                                'GL': gl,
                                'GB': gb,
                                'Bp': bp,
                                'Bd': bd
                            })
            except:
                pass

        return detailed

    def _safe_float(self, value) -> float:
        """Converte un valore in float in modo sicuro"""
        try:
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _generate_descriptive_summary(self, records, nmi_values, misure_values, siti, aree, saggi, us_list):
        """Genera un sommario descrittivo discorsivo delle statistiche"""
        summary = []

        # Introduzione
        summary.append(f"L'analisi del dataset faunistico comprende {len(records)} record archeologici ")
        summary.append(f"distribuiti su {len(siti)} siti, {len(aree)} aree, {len(saggi)} saggi e {len(us_list)} unità stratigrafiche.")
        summary.append("")

        # Analisi per sito
        if len(siti) > 0:
            summary.append("DISTRIBUZIONE PER SITO:")
            site_records = {}
            for r in records:
                site = r.get('sito', '')
                if site:
                    if site not in site_records:
                        site_records[site] = []
                    site_records[site].append(r)

            # Sito dominante
            sorted_sites = sorted(site_records.items(), key=lambda x: len(x[1]), reverse=True)
            dominant_site = sorted_sites[0]
            pct = (len(dominant_site[1]) / len(records)) * 100

            summary.append(f"Il sito più rappresentato è '{dominant_site[0]}' con {len(dominant_site[1])} record ({pct:.1f}% del totale). ")

            if len(siti) > 1:
                summary.append(f"Gli altri {len(siti) - 1} siti contribuiscono con il restante {100 - pct:.1f}% dei dati, ")
                summary.append("permettendo un'analisi comparativa tra diverse località archeologiche. ")

                # Specie dominanti per il sito principale
                site_species = {}
                for r in dominant_site[1]:
                    species_list = self._extract_species_from_record(r)
                    for sp in species_list:
                        if sp:
                            site_species[sp] = site_species.get(sp, 0) + 1

                if site_species:
                    top_sp = max(site_species.items(), key=lambda x: x[1])
                    summary.append(f"Nel sito '{dominant_site[0]}', la specie predominante è {top_sp[0]} ")
                    summary.append(f"con {top_sp[1]} occorrenze.")

            summary.append("")
            summary.append("Le statistiche sono state organizzate gerarchicamente per sito, consentendo di analizzare ")
            summary.append("la distribuzione spaziale dei resti faunistici a livello di aree, saggi e unità stratigrafiche ")
            summary.append("all'interno di ciascun sito, oltre alle combinazioni specifiche Area+Saggio+US.")
            summary.append("")

        # Analisi specie
        species_count = {}
        for r in records:
            species_list = self._extract_species_from_record(r)
            for sp in species_list:
                if sp:
                    species_count[sp] = species_count.get(sp, 0) + 1

        if species_count:
            top_3_species = sorted(species_count.items(), key=lambda x: x[1], reverse=True)[:3]
            summary.append("ANALISI DELLE SPECIE:")
            summary.append(f"Sono state identificate {len(species_count)} specie diverse. Le specie predominanti sono:")

            for sp, count in top_3_species:
                pct = (count / len(records)) * 100
                summary.append(f"  - {sp}: presente in {count} record ({pct:.1f}% del totale)")

            summary.append("")

        # Analisi NMI
        if nmi_values:
            total_nmi = sum(nmi_values)
            avg_nmi = total_nmi / len(nmi_values)
            summary.append("NUMERO MINIMO DI INDIVIDUI (NMI):")
            summary.append(f"Il numero minimo totale di individui è {total_nmi}, con una media di {avg_nmi:.1f} individui ")
            summary.append(f"per record. Il valore minimo registrato è {min(nmi_values)}, mentre il massimo è {max(nmi_values)}.")
            summary.append("")

        # Analisi contesti
        context_count = {}
        for r in records:
            ctx = r.get('contesto', '')
            if ctx:
                context_count[ctx] = context_count.get(ctx, 0) + 1

        if context_count:
            dominant_context = max(context_count.items(), key=lambda x: x[1])
            pct = (dominant_context[1] / len(records)) * 100
            summary.append("CONTESTI ARCHEOLOGICI:")
            summary.append(f"Il contesto prevalente è '{dominant_context[0]}' con {dominant_context[1]} occorrenze ")
            summary.append(f"({pct:.1f}% del totale). ")

            if len(context_count) > 1:
                summary.append(f"Sono stati identificati {len(context_count)} diversi tipi di contesto, indicando ")
                summary.append("una varietà di situazioni deposizionali.")

            summary.append("")

        # Analisi stato di conservazione
        conservation_count = {}
        for r in records:
            cons = r.get('stato_conservazione', '')
            if cons:
                conservation_count[cons] = conservation_count.get(cons, 0) + 1

        if conservation_count:
            summary.append("STATO DI CONSERVAZIONE:")

            # Calcola media stato conservazione (considerando valori 0-5)
            try:
                numeric_conservation = [int(k) for k in conservation_count.keys() if k.isdigit()]
                if numeric_conservation:
                    weighted_sum = sum(int(k) * conservation_count[k] for k in conservation_count.keys() if k.isdigit())
                    total_with_conservation = sum(conservation_count[k] for k in conservation_count.keys() if k.isdigit())
                    avg_conservation = weighted_sum / total_with_conservation if total_with_conservation > 0 else 0

                    if avg_conservation < 2:
                        quality_desc = "generalmente scarso"
                    elif avg_conservation < 3.5:
                        quality_desc = "mediocre"
                    else:
                        quality_desc = "buono"

                    summary.append(f"Lo stato di conservazione dei reperti è {quality_desc}, con un valore medio di {avg_conservation:.1f} ")
                    summary.append("sulla scala 0-5 (dove 0=pessimo, 5=ottimo).")
            except:
                pass

            summary.append("")

        # Analisi tafonomica
        combustion_count = {}
        for r in records:
            comb = r.get('tracce_combustione', '')
            if comb:
                combustion_count[comb] = combustion_count.get(comb, 0) + 1

        if combustion_count:
            records_with_combustion = sum(v for k, v in combustion_count.items() if k.lower() not in ['assente', 'no'])
            pct_combustion = (records_with_combustion / len(records)) * 100

            summary.append("ANALISI TAFONOMICA:")
            summary.append(f"Tracce di combustione sono presenti in {records_with_combustion} record ({pct_combustion:.1f}% del totale), ")

            if pct_combustion > 50:
                summary.append("suggerendo una significativa esposizione al fuoco dei resti faunistici.")
            elif pct_combustion > 20:
                summary.append("indicando una presenza moderata di fenomeni di combustione.")
            else:
                summary.append("indicando un'esposizione limitata al fuoco.")

            summary.append("")

        # Connessione anatomica
        connection_count = {}
        for r in records:
            conn = r.get('resti_connessione_anatomica', '')
            if conn:
                connection_count[conn] = connection_count.get(conn, 0) + 1

        if connection_count:
            connected = connection_count.get('Si', 0) + connection_count.get('Parziale', 0)
            pct_connected = (connected / len(records)) * 100

            summary.append("CONNESSIONE ANATOMICA:")
            summary.append(f"Resti in connessione anatomica (totale o parziale) sono stati riscontrati in {connected} record ")
            summary.append(f"({pct_connected:.1f}% del totale), ")

            if pct_connected > 40:
                summary.append("suggerendo deposizioni primarie o una buona preservazione del contesto originale.")
            elif pct_connected > 15:
                summary.append("indicando una preservazione moderata del contesto deposizionale.")
            else:
                summary.append("suggerendo prevalentemente deposizioni secondarie o rimaneggiate.")

            summary.append("")

        # Conclusione
        summary.append("CONCLUSIONI:")
        summary.append("Il dataset rappresenta un campione significativo per l'analisi archeozoologica del sito. ")
        summary.append("I dati raccolti permettono di ricostruire aspetti legati all'economia, all'alimentazione e ")
        summary.append("alle pratiche cultuali delle popolazioni antiche che hanno abitato l'area.")

        return summary

    def export_statistics_excel(self):
        """Esporta le statistiche in formato Excel (CSV)"""
        if not self.current_stats_text:
            QMessageBox.warning(self, "Attenzione", "Genera prima le statistiche con 'Aggiorna Statistiche'")
            return

        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv

            # Dialog per scegliere dove salvare
            default_name = f"statistiche_fauna_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salva statistiche Excel",
                default_name,
                "File CSV (*.csv);;Tutti i file (*)"
            )

            if not file_path:
                return

            # Crea CSV con dati strutturati
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # Intestazione
                writer.writerow(['STATISTICHE FAUNA - EXPORT'])
                writer.writerow(['Data generazione', datetime.now().strftime('%d/%m/%Y %H:%M:%S')])
                writer.writerow([])

                # Statistiche generali
                writer.writerow(['STATISTICHE GENERALI'])
                writer.writerow(['Totale record', self.current_stats_data.get('total', 0)])
                writer.writerow(['Numero siti', len(self.current_stats_data.get('siti', []))])
                writer.writerow(['Numero aree', len(self.current_stats_data.get('aree', []))])
                writer.writerow(['Numero saggi', len(self.current_stats_data.get('saggi', []))])
                writer.writerow(['Numero US', len(self.current_stats_data.get('us', []))])
                writer.writerow([])

                # NMI
                nmi_vals = self.current_stats_data.get('nmi_values', [])
                if nmi_vals:
                    writer.writerow(['NUMERO MINIMO INDIVIDUI (NMI)'])
                    writer.writerow(['Totale record con NMI', len(nmi_vals)])
                    writer.writerow(['Media', f"{sum(nmi_vals)/len(nmi_vals):.1f}"])
                    writer.writerow(['Minimo', min(nmi_vals)])
                    writer.writerow(['Massimo', max(nmi_vals)])
                    writer.writerow(['Somma totale', sum(nmi_vals)])
                    writer.writerow([])

                # Misure
                mis_vals = self.current_stats_data.get('misure_values', [])
                if mis_vals:
                    writer.writerow(['MISURE OSSA (mm)'])
                    writer.writerow(['Totale misurazioni', len(mis_vals)])
                    writer.writerow(['Media', f"{sum(mis_vals)/len(mis_vals):.2f}"])
                    writer.writerow(['Minimo', f"{min(mis_vals):.2f}"])
                    writer.writerow(['Massimo', f"{max(mis_vals):.2f}"])
                    writer.writerow([])

                # Distribuzione specie
                records = self.current_stats_data.get('records', [])
                if records:
                    species_count = {}
                    for r in records:
                        species_list = self._extract_species_from_record(r)
                        for sp in species_list:
                            if sp:
                                species_count[sp] = species_count.get(sp, 0) + 1

                    if species_count:
                        writer.writerow(['DISTRIBUZIONE SPECIE'])
                        writer.writerow(['Specie', 'Conteggio', 'Percentuale'])
                        sorted_species = sorted(species_count.items(), key=lambda x: x[1], reverse=True)
                        for sp, count in sorted_species:
                            pct = (count / len(records)) * 100
                            writer.writerow([sp, count, f"{pct:.1f}%"])
                        writer.writerow([])

                    # Distribuzione PSI
                    psi_count = {}
                    for r in records:
                        psi_list = self._extract_psi_from_record(r)
                        for psi in psi_list:
                            if psi:
                                psi_count[psi] = psi_count.get(psi, 0) + 1

                    if psi_count:
                        writer.writerow(['DISTRIBUZIONE PARTI SCHELETRICHE (PSI)'])
                        writer.writerow(['Parte Scheletrica', 'Conteggio', 'Percentuale'])
                        sorted_psi = sorted(psi_count.items(), key=lambda x: x[1], reverse=True)
                        for psi, count in sorted_psi:
                            pct = (count / sum(psi_count.values())) * 100
                            writer.writerow([psi, count, f"{pct:.1f}%"])
                        writer.writerow([])

                    # Distribuzione Elementi Anatomici misurati
                    elem_count = {}
                    all_measures = []
                    for r in records:
                        detailed = self._extract_detailed_measurements_from_record(r)
                        all_measures.extend(detailed)
                        for m in detailed:
                            if m['elemento']:
                                elem_count[m['elemento']] = elem_count.get(m['elemento'], 0) + 1

                    if elem_count:
                        writer.writerow(['ELEMENTI ANATOMICI MISURATI'])
                        writer.writerow(['Elemento', 'Conteggio', 'Percentuale'])
                        sorted_elem = sorted(elem_count.items(), key=lambda x: x[1], reverse=True)
                        for el, count in sorted_elem:
                            pct = (count / sum(elem_count.values())) * 100
                            writer.writerow([el, count, f"{pct:.1f}%"])
                        writer.writerow([])

                    # Misure dettagliate
                    if all_measures:
                        writer.writerow(['MISURE DETTAGLIATE'])
                        writer.writerow(['Elemento', 'Specie', 'GL (mm)', 'GB (mm)', 'Bp (mm)', 'Bd (mm)'])
                        for m in all_measures:
                            writer.writerow([
                                m['elemento'],
                                m['specie'],
                                f"{m['GL']:.2f}" if m['GL'] > 0 else '',
                                f"{m['GB']:.2f}" if m['GB'] > 0 else '',
                                f"{m['Bp']:.2f}" if m['Bp'] > 0 else '',
                                f"{m['Bd']:.2f}" if m['Bd'] > 0 else ''
                            ])
                        writer.writerow([])

                # Report testuale completo
                writer.writerow(['REPORT COMPLETO'])
                for line in self.current_stats_text:
                    writer.writerow([line])

            QMessageBox.information(self, "Successo", f"Statistiche esportate in:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'esportazione Excel:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def export_statistics_pdf(self):
        """Esporta le statistiche in formato PDF"""
        if not self.current_stats_text:
            QMessageBox.warning(self, "Attenzione", "Genera prima le statistiche con 'Aggiorna Statistiche'")
            return

        try:
            from PyQt5.QtWidgets import QFileDialog

            # Dialog per scegliere dove salvare
            default_name = f"statistiche_fauna_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Salva statistiche PDF",
                default_name,
                "File PDF (*.pdf);;Tutti i file (*)"
            )

            if not file_path:
                return

            # Prova ad usare ReportLab
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import cm
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont

                # Crea PDF
                doc = SimpleDocTemplate(file_path, pagesize=A4,
                                       leftMargin=1.5*cm, rightMargin=1.5*cm,
                                       topMargin=2*cm, bottomMargin=2*cm)

                styles = getSampleStyleSheet()
                story = []

                # Titolo
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=16,
                    textColor=colors.HexColor('#2c3e50'),
                    spaceAfter=30,
                    alignment=1  # Center
                )

                story.append(Paragraph("STATISTICHE RIEPILOGATIVE - SCHEDE FAUNA", title_style))
                story.append(Spacer(1, 0.5*cm))

                # Data generazione
                date_style = ParagraphStyle(
                    'DateStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.grey,
                    alignment=1
                )
                story.append(Paragraph(f"Report generato il: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", date_style))
                story.append(Spacer(1, 1*cm))

                # Contenuto
                mono_style = ParagraphStyle(
                    'MonoStyle',
                    parent=styles['Normal'],
                    fontSize=8,
                    fontName='Courier',
                    leading=10
                )

                for line in self.current_stats_text:
                    if line.strip():
                        # Converti caratteri speciali
                        line_clean = line.replace('📋', '[*]').replace('🔢', '[#]').replace('📊', '[%]')
                        line_clean = line_clean.replace('📍', '[A]').replace('🔬', '[S]').replace('🏛', '[U]')
                        line_clean = line_clean.replace('📝', '[T]')

                        story.append(Paragraph(line_clean, mono_style))
                    else:
                        story.append(Spacer(1, 0.2*cm))

                doc.build(story)

                QMessageBox.information(self, "Successo", f"Statistiche esportate in:\n{file_path}")

            except ImportError:
                # Fallback: salva come file di testo con estensione PDF
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.current_stats_text))

                QMessageBox.information(
                    self,
                    "Esportazione completata",
                    f"Statistiche salvate in formato testo:\n{file_path}\n\n"
                    "Nota: Installa 'reportlab' per esportare in formato PDF vero:\n"
                    "pip install reportlab"
                )

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nell'esportazione PDF:\n{str(e)}")
            import traceback
            traceback.print_exc()

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

        # Note: Specie e Parti Scheletriche ora sono nelle table widgets
        # e vengono popolate dinamicamente quando si aggiungono righe

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
                self.txt_us.setText(us_data.get('us', ''))
                self.txt_sito.setText(us_data.get('sito', ''))
                self.txt_area.setText(us_data.get('area', ''))
                self.txt_saggio.setText(us_data.get('saggio', ''))
                self.txt_datazione_us.setText(us_data.get('datazione', ''))
        else:
            self.txt_us.clear()
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

    # ========== GESTIONE TABELLE SPECIE/PSI E MISURE ==========

    def add_specie_psi_row(self):
        """Aggiunge una riga alla tabella Specie/PSI"""
        row_position = self.table_specie_psi.rowCount()
        self.table_specie_psi.insertRow(row_position)

        # Combo Specie
        combo_specie = QComboBox()
        combo_specie.setEditable(True)
        combo_specie.addItem("")
        combo_specie.addItems(self.db.get_voc_values('specie'))
        self.table_specie_psi.setCellWidget(row_position, 0, combo_specie)

        # Combo PSI
        combo_psi = QComboBox()
        combo_psi.setEditable(True)
        combo_psi.addItem("")
        combo_psi.addItems(self.db.get_voc_values('parti_scheletriche'))
        self.table_specie_psi.setCellWidget(row_position, 1, combo_psi)

    def remove_specie_psi_row(self):
        """Rimuove la riga selezionata dalla tabella Specie/PSI"""
        current_row = self.table_specie_psi.currentRow()
        if current_row >= 0:
            self.table_specie_psi.removeRow(current_row)

    def get_specie_psi_data(self) -> list:
        """Estrae i dati dalla tabella Specie/PSI come lista di liste"""
        data = []
        for row in range(self.table_specie_psi.rowCount()):
            specie_widget = self.table_specie_psi.cellWidget(row, 0)
            psi_widget = self.table_specie_psi.cellWidget(row, 1)

            if specie_widget and psi_widget:
                specie = specie_widget.currentText()
                psi = psi_widget.currentText()
                if specie or psi:  # Include solo righe non vuote
                    data.append([specie, psi])
        return data

    def set_specie_psi_data(self, data: list):
        """Popola la tabella Specie/PSI da una lista di liste"""
        # Svuota la tabella
        self.table_specie_psi.setRowCount(0)

        # Aggiungi righe con i dati
        for row_data in data:
            if len(row_data) >= 2:
                row_position = self.table_specie_psi.rowCount()
                self.table_specie_psi.insertRow(row_position)

                # Combo Specie
                combo_specie = QComboBox()
                combo_specie.setEditable(True)
                combo_specie.addItem("")
                combo_specie.addItems(self.db.get_voc_values('specie'))
                combo_specie.setCurrentText(row_data[0])
                self.table_specie_psi.setCellWidget(row_position, 0, combo_specie)

                # Combo PSI
                combo_psi = QComboBox()
                combo_psi.setEditable(True)
                combo_psi.addItem("")
                combo_psi.addItems(self.db.get_voc_values('parti_scheletriche'))
                combo_psi.setCurrentText(row_data[1])
                self.table_specie_psi.setCellWidget(row_position, 1, combo_psi)

    def add_misura_row(self):
        """Aggiunge una riga alla tabella Misure"""
        row_position = self.table_misure.rowCount()
        self.table_misure.insertRow(row_position)

        # Combo Elemento Anatomico
        combo_elemento = QComboBox()
        combo_elemento.setEditable(True)
        combo_elemento.addItem("")
        combo_elemento.addItems(self.db.get_voc_values('elemento_anatomico'))
        self.table_misure.setCellWidget(row_position, 0, combo_elemento)

        # Combo Specie
        combo_specie = QComboBox()
        combo_specie.setEditable(True)
        combo_specie.addItem("")
        combo_specie.addItems(self.db.get_voc_values('specie'))
        self.table_misure.setCellWidget(row_position, 1, combo_specie)

        # Line edit per misure (GL, GB, Bp, Bd)
        for col in range(2, 6):
            line_edit = QLineEdit()
            line_edit.setPlaceholderText("0.00")
            self.table_misure.setCellWidget(row_position, col, line_edit)

    def remove_misura_row(self):
        """Rimuove la riga selezionata dalla tabella Misure"""
        current_row = self.table_misure.currentRow()
        if current_row >= 0:
            self.table_misure.removeRow(current_row)

    def get_misure_data(self) -> list:
        """Estrae i dati dalla tabella Misure come lista di liste"""
        data = []
        for row in range(self.table_misure.rowCount()):
            elemento_widget = self.table_misure.cellWidget(row, 0)
            specie_widget = self.table_misure.cellWidget(row, 1)

            if elemento_widget and specie_widget:
                elemento = elemento_widget.currentText()
                specie = specie_widget.currentText()

                # Leggi misure (GL, GB, Bp, Bd)
                misure = []
                for col in range(2, 6):
                    widget = self.table_misure.cellWidget(row, col)
                    if widget:
                        text = widget.text().strip()
                        misure.append(text if text else "")

                # Include solo righe con almeno elemento o specie
                if elemento or specie or any(misure):
                    data.append([elemento, specie] + misure)
        return data

    def set_misure_data(self, data: list):
        """Popola la tabella Misure da una lista di liste"""
        # Svuota la tabella
        self.table_misure.setRowCount(0)

        # Aggiungi righe con i dati
        for row_data in data:
            if len(row_data) >= 6:
                row_position = self.table_misure.rowCount()
                self.table_misure.insertRow(row_position)

                # Combo Elemento Anatomico
                combo_elemento = QComboBox()
                combo_elemento.setEditable(True)
                combo_elemento.addItem("")
                combo_elemento.addItems(self.db.get_voc_values('elemento_anatomico'))
                combo_elemento.setCurrentText(row_data[0])
                self.table_misure.setCellWidget(row_position, 0, combo_elemento)

                # Combo Specie
                combo_specie = QComboBox()
                combo_specie.setEditable(True)
                combo_specie.addItem("")
                combo_specie.addItems(self.db.get_voc_values('specie'))
                combo_specie.setCurrentText(row_data[1])
                self.table_misure.setCellWidget(row_position, 1, combo_specie)

                # Line edit per misure (GL, GB, Bp, Bd)
                for col in range(2, 6):
                    line_edit = QLineEdit()
                    line_edit.setPlaceholderText("0.00")
                    line_edit.setText(str(row_data[col]) if row_data[col] else "")
                    self.table_misure.setCellWidget(row_position, col, line_edit)

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

        # Popola anche il campo Nome US direttamente dal record (backup)
        self.txt_us.setText(record.get('us', ''))

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
        self.spin_nmi.setValue(int(nmi) if nmi else 0)

        # Specie e PSI (JSON)
        import json
        specie_psi_json = record.get('specie_psi', '')
        try:
            if specie_psi_json and specie_psi_json.strip():
                specie_psi_data = json.loads(specie_psi_json)
                self.set_specie_psi_data(specie_psi_data)
            else:
                # Fallback: usa campi vecchi se JSON vuoto
                specie = record.get('specie', '')
                psi = record.get('parti_scheletriche', '')
                if specie or psi:
                    self.set_specie_psi_data([[specie, psi]])
                else:
                    self.set_specie_psi_data([])
        except:
            self.set_specie_psi_data([])

        # Misure Ossa (JSON)
        misure_json = record.get('misure_ossa', '')
        try:
            if misure_json and misure_json.strip():
                misure_data = json.loads(misure_json)
                self.set_misure_data(misure_data)
            else:
                self.set_misure_data([])
        except:
            self.set_misure_data([])

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

        # Specie e PSI (JSON)
        import json
        specie_psi_data = self.get_specie_psi_data()
        data['specie_psi'] = json.dumps(specie_psi_data, ensure_ascii=False) if specie_psi_data else ''

        # Mantieni compatibilità con campi vecchi (prendi prima riga se presente)
        if specie_psi_data:
            data['specie'] = specie_psi_data[0][0] if len(specie_psi_data[0]) > 0 else ''
            data['parti_scheletriche'] = specie_psi_data[0][1] if len(specie_psi_data[0]) > 1 else ''
        else:
            data['specie'] = ''
            data['parti_scheletriche'] = ''

        # Misure Ossa (JSON)
        misure_data = self.get_misure_data()
        data['misure_ossa'] = json.dumps(misure_data, ensure_ascii=False) if misure_data else ''

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
        self.txt_alterazioni.clear()
        self.txt_note_terreno.clear()
        self.txt_campionature.clear()
        self.txt_affidabilita.clear()
        self.txt_classi_reperti.clear()
        self.txt_osservazioni.clear()
        self.txt_interpretazione.clear()
        self.check_combustione_altri.setChecked(False)

        # Clear tables
        self.table_specie_psi.setRowCount(0)
        self.table_misure.setRowCount(0)

        # Reset combo boxes
        for combo in [self.combo_metodologia, self.combo_contesto, self.combo_connessione,
                      self.combo_tipologia_accumulo, self.combo_deposizione, self.combo_num_stimato,
                      self.combo_frammentazione, self.combo_tracce_combustione, self.combo_tipo_combustione,
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