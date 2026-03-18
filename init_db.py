#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, r'C:\Users\teamp\Documents\WORKS UNI I\QUALITY')

os.chdir(r'C:\Users\teamp\Documents\WORKS UNI I\QUALITY')

from dotenv import load_dotenv
load_dotenv()

from db import init_database

print("[TEST] Inicializando base de datos PostgreSQL...")
try:
    init_database()
    print("[OK] Base de datos inicializada correctamente")
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
