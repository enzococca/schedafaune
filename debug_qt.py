#!/usr/bin/env python3
"""
Script per diagnosticare problemi Qt
"""

import sys
import os

print("="*60)
print("DIAGNOSI Qt - Fauna Manager")
print("="*60)
print()

# 1. Informazioni Python
print("1. Python:")
print(f"   Versione: {sys.version}")
print(f"   Eseguibile: {sys.executable}")
print(f"   Prefix: {sys.prefix}")
print()

# 2. Virtual Environment
print("2. Virtual Environment:")
venv = os.environ.get('VIRTUAL_ENV', 'Nessuno')
print(f"   VIRTUAL_ENV: {venv}")
print()

# 3. PyQt5
print("3. PyQt5:")
try:
    import PyQt5
    print(f"   ✓ PyQt5 importato")
    print(f"   Path: {PyQt5.__file__}")

    from PyQt5.QtCore import QLibraryInfo, PYQT_VERSION_STR, QT_VERSION_STR
    print(f"   Versione PyQt5: {PYQT_VERSION_STR}")
    print(f"   Versione Qt: {QT_VERSION_STR}")

    # Percorsi Qt
    print()
    print("4. Percorsi Qt:")

    # Vecchio metodo (PyQt5 < 5.15)
    try:
        plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
        print(f"   Plugins Path: {plugins_path}")
        print(f"   Exists: {os.path.exists(plugins_path)}")

        if os.path.exists(plugins_path):
            print(f"   Contents:")
            for item in os.listdir(plugins_path):
                print(f"      - {item}")
                if item == "platforms":
                    platforms_path = os.path.join(plugins_path, "platforms")
                    print(f"        Platforms:")
                    for platform in os.listdir(platforms_path):
                        print(f"          - {platform}")
    except:
        # Nuovo metodo (PyQt5 >= 5.15.4)
        try:
            from PyQt5.QtCore import QLibraryInfo
            if hasattr(QLibraryInfo, 'path'):
                plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
                print(f"   Plugins Path (new API): {plugins_path}")
                print(f"   Exists: {os.path.exists(plugins_path)}")
        except:
            print("   ✗ Impossibile determinare plugin path")

    print()
    print("5. Variabili d'Ambiente Qt:")
    qt_vars = ['QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH', 'DYLD_LIBRARY_PATH']
    for var in qt_vars:
        value = os.environ.get(var, 'Non impostata')
        print(f"   {var}: {value}")

    print()
    print("6. Test Creazione QApplication:")
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        print("   ✓ QApplication creata con successo!")
        app.quit()
    except Exception as e:
        print(f"   ✗ Errore: {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"   ✗ PyQt5 non installato: {e}")

print()
print("="*60)
print("Fine diagnosi")
print("="*60)
