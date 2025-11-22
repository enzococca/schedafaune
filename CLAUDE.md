# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a complete digital management system for archaeozoological data, implementing the standardized SCHEDA FR (Fauna Record Sheet) format. The system integrates with pyArchInit and QGIS to provide a comprehensive solution for managing fauna remains from archaeological excavations.

## Project Structure

### Core Components
- **sql/**: Database schema files
  - `create_fauna_table.sql`: Main fauna table with 34 fields from SCHEDA FR
  - `create_fauna_voc.sql`: Controlled vocabulary tables with standardized values

- **Python Modules**:
  - `fauna_db.py`: Database management layer (CRUD operations, queries)
  - `fauna_manager.py`: Main Qt interface with tab-based layout and navigation toolbar
  - `fauna_pdf.py`: PDF export functionality using ReportLab
  - `qgis_integration.py`: QGIS integration via Actions and Python console

- **Utilities**:
  - `install_db.py`: Database installation script
  - `test_fauna_system.py`: Complete test suite
  - `esempi_uso.py`: Usage examples

- **Documentation**:
  - `README.md`: Complete user documentation
  - `requirements.txt`: Python dependencies
  - `FIGG. 2-4.pdf`: Original SCHEDA FR template (reference)
  - `Scheda FR_faune.xlsx`: Field specifications (reference)

## Architecture

### Database Integration

**Multi-Database Support**:
- **SQLite**: File-based, simple setup, good for single-user
- **PostgreSQL**: Server-based, multi-user, better for team collaboration

**Schema**:
- **fauna_table**: Main table with 34 fields following SCHEDA FR standard
  - Fields 1-6: Foreign key relationship with pyArchInit's `us_table` (sito, area, saggio, us, datazione_us)
  - Fields 7-34: Fauna-specific data (species, NMI, taphonomy, etc.)
- **fauna_voc**: Controlled vocabulary for dropdowns and data validation
- **Join strategy**: id_us → us_table.id_us for automatic retrieval of stratigraphic context

**Auto-creation**: Tables are created automatically on first connection if missing, with proper syntax adaptation for PostgreSQL (BOOLEAN TRUE/FALSE, GENERATED ALWAYS AS IDENTITY, etc.)

### Interface Organization
Four-tab layout following SCHEDA FR sections:
1. **Dati Identificativi**: US data (read-only from us_table) + depositional data
2. **Dati Archeozoologici**: Species, NMI, skeletal parts, anatomical connection
3. **Dati Tafonomici**: Fragmentation, combustion, preservation state
4. **Dati Contestuali**: Notes, observations, interpretation

### Toolbar Functions
- **Navigation**: First/Previous/Next/Last record
- **CRUD**: New/Save/Delete (with multi-delete support)
- **Search**: Advanced search dialog with filters
- **Export**: PDF generation (ReportLab-based)

## Common Development Tasks

### Quick Start Installation

```bash
# 1. Crea e attiva virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Su macOS/Linux
# .venv\Scripts\activate   # Su Windows

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Avvia l'applicazione
./start_fauna_manager.sh  # macOS/Linux
# python start_fauna.py   # Alternativa cross-platform
```

Al primo avvio:
1. Si apre un dialog per selezionare il database (SQLite o PostgreSQL)
2. Le tabelle `fauna_table` e `fauna_voc` vengono create automaticamente se mancanti
3. La configurazione viene salvata in `~/.pyarchinit/fauna_db_config.json`

### Database Support

**SQLite** (predefinito):
- Database file: `~/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite`
- Nessuna configurazione aggiuntiva richiesta

**PostgreSQL**:
- Host: localhost (o server remoto)
- Porta: 5432 (predefinita) o personalizzata
- Database: pyarchinit (o altro)
- Credenziali: username/password
- Password può essere salvata (opzionale, vedi `SAVE_PASSWORD` in `db_config_manager.py`)

### Cambiare Database Durante l'Uso

Click sul pulsante `🔄 Cambia Database` nella toolbar per:
- Passare da SQLite a PostgreSQL (o viceversa)
- Connettersi a un database diverso
- Le tabelle vengono verificate/create automaticamente

### Running the Application

```bash
# Metodo 1: Script di avvio (consigliato)
./start_fauna_manager.sh

# Metodo 2: Python diretto
python start_fauna.py

# Metodo 3: Standalone (senza virtual environment)
python fauna_manager.py

# Metodo 4: Da QGIS Python console
import sys
sys.path.insert(0, '/Users/enzo/Desktop/schedafaune')
from qgis_integration import FaunaQGISIntegration
integration = FaunaQGISIntegration(iface)
integration.open_fauna_manager()
```

### Adding New Vocabulary Values

**SQLite**:
```sql
INSERT INTO fauna_voc (campo, valore, ordinamento)
VALUES ('specie', 'New Species Name', 100);
```

**PostgreSQL**:
```sql
INSERT INTO fauna_voc (campo, valore, ordinamento)
VALUES ('specie', 'New Species Name', 100)
ON CONFLICT (campo, valore) DO NOTHING;
```

### Configuration Files

- **Database config**: `~/.pyarchinit/fauna_db_config.json`
  - Tipo database (sqlite/postgres)
  - Parametri connessione
  - Password (opzionale, configurabile)

- **Virtual environment**: `.venv/`
  - Dipendenze Python isolate
  - Creato automaticamente da `start_fauna_manager.sh`

## Key Design Patterns

### Database Access
All database operations go through database wrapper classes:
- **fauna_db_wrapper.py**: Factory function `create_fauna_db()` selects SQLite or PostgreSQL adapter
- **fauna_db.py**: SQLite implementation (`FaunaDB` class)
- **fauna_db_postgres.py**: PostgreSQL implementation (`FaunaDBPostgres` class)
- **db_config_manager.py**: Manages config persistence in `~/.pyarchinit/fauna_db_config.json`
- **database_selector.py**: Qt dialog for database selection with connection testing

Features:
- Automatic connection management with autocommit for DDL operations
- Table auto-creation on first connection with SQL syntax adaptation
- SQL comment removal and BOOLEAN conversion (1/0 → TRUE/FALSE) for PostgreSQL
- Foreign key enforcement for us_table relationship
- Parameterized queries to prevent SQL injection

### Form-Record Binding
- `display_record(dict)`: Populates form from database record
- `get_form_data()`: Extracts form data to dictionary
- ComboBox auto-population from fauna_voc table
- Read-only fields for US data (populated via us_table join)

### PDF Generation
Template-based generation using ReportLab:
- Matches original SCHEDA FR layout
- Section headers and field tables
- Supports both single and batch export

## Integration Points

### With pyArchInit
- Shares same SQLite database
- Foreign key: fauna_table.id_us → us_table.id_us
- Reads sito, area, us, saggio, datazione from us_table
- Can be launched as Action from us_table layer in QGIS

### With QGIS
- Action-based launch from layer properties
- Compatible with QGIS 3.x PyQt5 API
- Can be embedded as dock widget or standalone window

## Language and Terminology

All UI and data in Italian. Key terms:
- **SCHEDA FR**: Fauna Record (standard form)
- **US**: Unità Stratigrafica (Stratigraphic Unit)
- **NMI**: Numero Minimo di Individui (Minimum Number of Individuals)
- **Contesto**: Context (funerary, habitation, production, hypogeum, cult, other)
- **Resti in connessione anatomica**: Remains in anatomical connection
- **Stato di conservazione**: Preservation state (0-5 scale)
- **Segni tafonomici**: Taphonomic marks/traces

## Testing

Run complete test suite:
```bash
python test_fauna_system.py
```

Tests cover:
1. Database connection
2. Vocabulary tables
3. us_table integration
4. CRUD operations
5. Search functionality
6. PDF export

## Known Dependencies
- PyQt5: GUI framework
- ReportLab: PDF generation (optional, graceful degradation)
- SQLite3: Database (included in Python)
- pyArchInit: Must be installed with populated us_table