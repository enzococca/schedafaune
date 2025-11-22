#!/bin/bash
#
# Script di avvio Fauna Manager per Mac/Linux
# Verifica dipendenze, installa se necessario e avvia l'interfaccia
#

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzione per stampare messaggi colorati
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Banner
echo "========================================"
echo "  Fauna Manager - pyArchInit"
echo "  Gestione Schede Faunistiche"
echo "========================================"
echo ""

# Ottieni la directory dello script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. Verifica Python
print_info "Verifica installazione Python..."

# Controlla se c'è un virtual environment attivo o nella directory
if [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_CMD="$VIRTUAL_ENV/bin/python"
    print_success "Usando Python del virtual environment: $VIRTUAL_ENV"
elif [ -d ".venv/bin" ]; then
    PYTHON_CMD=".venv/bin/python"
    print_info "Attivazione virtual environment .venv..."
    source .venv/bin/activate
    print_success "Virtual environment .venv attivato"
elif [ -d "venv/bin" ]; then
    PYTHON_CMD="venv/bin/python"
    print_info "Attivazione virtual environment venv..."
    source venv/bin/activate
    print_success "Virtual environment venv attivato"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    print_warning "Nessun virtual environment trovato, usando python3 di sistema"
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    print_warning "Nessun virtual environment trovato, usando python di sistema"
else
    print_error "Python non trovato!"
    print_info "Installa Python 3.7+ da https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
print_success "Python $PYTHON_VERSION trovato"

# 2. Verifica pip
print_info "Verifica pip..."

# Usa il pip del virtual environment se disponibile
if [ -n "$VIRTUAL_ENV" ]; then
    PIP_CMD="$VIRTUAL_ENV/bin/pip"
elif [ -d ".venv/bin" ]; then
    PIP_CMD=".venv/bin/pip"
elif [ -d "venv/bin" ]; then
    PIP_CMD="venv/bin/pip"
elif command -v pip3 &> /dev/null; then
    PIP_CMD=pip3
elif command -v pip &> /dev/null; then
    PIP_CMD=pip
else
    print_error "pip non trovato!"
    exit 1
fi

print_success "pip trovato"

# 3. Verifica e installa dipendenze
print_info "Verifica dipendenze Python..."

MISSING_DEPS=()

# Controlla PyQt5
$PYTHON_CMD -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    print_warning "PyQt5 non installato"
    MISSING_DEPS+=("PyQt5")
fi

# Controlla reportlab
$PYTHON_CMD -c "import reportlab" 2>/dev/null
if [ $? -ne 0 ]; then
    print_warning "reportlab non installato"
    MISSING_DEPS+=("reportlab")
fi

# Se ci sono dipendenze mancanti, chiedi all'utente
if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo ""
    print_warning "Dipendenze mancanti: ${MISSING_DEPS[*]}"
    echo -n "Vuoi installarle ora? (s/n): "
    read -r INSTALL_DEPS

    if [ "$INSTALL_DEPS" = "s" ] || [ "$INSTALL_DEPS" = "S" ]; then
        print_info "Installazione dipendenze..."

        if [ -f "requirements.txt" ]; then
            $PIP_CMD install -r requirements.txt
        else
            for dep in "${MISSING_DEPS[@]}"; do
                print_info "Installazione $dep..."
                $PIP_CMD install "$dep"
            done
        fi

        if [ $? -eq 0 ]; then
            print_success "Dipendenze installate con successo"
        else
            print_error "Errore nell'installazione delle dipendenze"
            exit 1
        fi
    else
        print_warning "Alcune funzionalità potrebbero non funzionare senza le dipendenze"
    fi
fi

echo ""

# 4. Verifica database pyArchInit
print_info "Verifica database pyArchInit..."

DB_PATH="$HOME/pyarchinit/pyarchinit_DB_folder/pyarchinit_db.sqlite"

if [ ! -f "$DB_PATH" ]; then
    print_warning "Database pyArchInit non trovato in: $DB_PATH"
    print_info "Il database verrà selezionato all'avvio dell'interfaccia"
else
    print_success "Database pyArchInit trovato"

    # Verifica se le tabelle fauna esistono
    TABLES_EXIST=$($PYTHON_CMD -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('$DB_PATH')
    cursor = conn.cursor()
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='fauna_table'\")
    if cursor.fetchone():
        print('1')
    else:
        print('0')
    conn.close()
except:
    print('0')
" 2>/dev/null)

    if [ "$TABLES_EXIST" = "1" ]; then
        print_success "Tabelle fauna già installate"
    else
        print_warning "Tabelle fauna non installate"
        echo -n "Vuoi installarle ora? (s/n): "
        read -r INSTALL_TABLES

        if [ "$INSTALL_TABLES" = "s" ] || [ "$INSTALL_TABLES" = "S" ]; then
            print_info "Installazione tabelle..."
            $PYTHON_CMD install_db.py

            if [ $? -eq 0 ]; then
                print_success "Tabelle installate con successo"
            else
                print_error "Errore nell'installazione delle tabelle"
                exit 1
            fi
        fi
    fi
fi

echo ""

# 5. Avvio interfaccia
print_success "Avvio Fauna Manager..."
echo ""

# Aggiungi directory corrente al PYTHONPATH
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Fix per Qt plugin su macOS
# Trova il percorso dei plugin Qt
QT_PLUGIN_PATH=$($PYTHON_CMD -c "import os, sys; from PyQt5.QtCore import QLibraryInfo; print(QLibraryInfo.location(QLibraryInfo.PluginsPath))" 2>/dev/null)

if [ -n "$QT_PLUGIN_PATH" ] && [ -d "$QT_PLUGIN_PATH" ]; then
    export QT_PLUGIN_PATH
    print_info "Qt plugin path: $QT_PLUGIN_PATH"
fi

# Disabilita High DPI scaling se causa problemi
export QT_AUTO_SCREEN_SCALE_FACTOR=0

# Avvia l'interfaccia
$PYTHON_CMD qgis_integration.py

# Codice di uscita
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    print_success "Fauna Manager chiuso correttamente"
else
    print_error "Fauna Manager chiuso con errori (codice: $EXIT_CODE)"
fi

exit $EXIT_CODE
