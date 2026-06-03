import sys
import os
import random
from datetime import datetime, timedelta

# Agregar el directorio actual al path para importar db
_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, _DIR)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_DIR, ".env"))
except ImportError:
    pass

from db import (
    UsuarioRepository,
    CategoriaRepository,
    MovimientoRepository,
    PresupuestoRepository,
    NotificacionRepository,
    init_database
)

def create_demo_data():
    print("=== Iniciando Generación de Datos para Demostración (Smoke Demo) ===")
    
    # 1. Asegurar que la DB esté inicializada
    try:
        init_database()
        print("[OK] Base de datos inicializada.")
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar la DB: {e}")
        return

    # 2. Registrar Usuario de Prueba
    email_demo = "demo_smoke@controlcash.com"
    password_demo = "Demo123!"
    nombre_demo = "Usuario de Demostración"
    
    # Limpiar si ya existe (opcional, pero mejor para repetibilidad)
    # No hay método eliminar usuario fácil en repo, así que solo intentamos crear
    usuario = UsuarioRepository.crear(
        nombre=nombre_demo,
        email=email_demo,
        password=password_demo,
        moneda="COP"
    )
    
    if usuario is None:
        print(f"[INFO] El usuario {email_demo} ya existe. Usando el existente.")
        usuario = UsuarioRepository.autenticar(email_demo, password_demo)
    else:
        print(f"[OK] Usuario demo creado: {usuario['id']}")

    usuario_id = usuario['id']

    # 3. Asegurar Categorías para el usuario
    # Usamos SQL directo para asegurar que existan categorías para este usuario
    import pymysql
    from db.config import MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD
    
    conn = pymysql.connect(
        host=MYSQL_HOST, port=int(MYSQL_PORT), user=MYSQL_USER, 
        password=MYSQL_PASSWORD, database=MYSQL_DATABASE
    )
    try:
        with conn.cursor() as cur:
            # Categorías básicas de ejemplo
            seed_cats = [
                ('Salario', 'ingreso', '💼'),
                ('Alimentación', 'gasto', '🍔'),
                ('Transporte', 'gasto', '🚗'),
                ('Vivienda', 'gasto', '🏠'),
                ('Salud', 'gasto', '🏥'),
                ('Entretenimiento', 'gasto', '🎮'),
                ('Otros gastos', 'gasto', '📦')
            ]
            for nom, tip, ico in seed_cats:
                cur.execute(
                    "INSERT INTO categorias (usuario_id, nombre, tipo_id, icono, activo) "
                    "VALUES (%s, %s, (SELECT id FROM tipos_movimiento WHERE codigo = %s), %s, 1) "
                    "ON DUPLICATE KEY UPDATE activo = 1",
                    (usuario_id, nom, tip, ico)
                )
        conn.commit()
        print(f"[OK] Categorías insertadas/aseguradas vía SQL directo.")
    except Exception as e:
        print(f"[WARN] Error en SQL directo de categorías: {e}")
    finally:
        conn.close()

    categorias = CategoriaRepository.listar(usuario_id)
    cat_map = {c['nombre']: c['id'] for c in categorias}
    print(f"[OK] Categorías listas ({len(categorias)} en total).")

    if not categorias:
        print("[ERROR] No se pudieron obtener categorías para el usuario. Abortando.")
        return

    # 4. Añadir dos movimientos "Relevantes"
    # Ingreso principal
    cat_ingreso_id = cat_map.get('Salario') or (categorias[0]['id'] if [c for c in categorias if c['tipo'] == 'ingreso'] else None)
    if cat_ingreso_id:
        MovimientoRepository.crear(
            usuario_id=usuario_id,
            categoria_id=cat_ingreso_id,
            tipo='ingreso',
            monto=5000000,
            descripcion="Salario Mensual - Nómina Mayo",
            fecha=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
        )
        print("[OK] Movimiento RELEVANTE 1 (Ingreso) creado.")

    # Gasto importante
    cat_gasto_id = cat_map.get('Vivienda') or (categorias[0]['id'] if [c for c in categorias if c['tipo'] == 'gasto'] else None)
    if cat_gasto_id:
        MovimientoRepository.crear(
            usuario_id=usuario_id,
            categoria_id=cat_gasto_id,
            tipo='gasto',
            monto=1200000,
            descripcion="Pago Arriendo Apartamento",
            fecha=(datetime.now() - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S")
        )
        print("[OK] Movimiento RELEVANTE 2 (Gasto) creado.")

    # 5. Añadir Datos Sintéticos para el Dashboard (30 días de historia)
    print("Generando datos sintéticos para los últimos 30 días...")
    descripciones_gastos = [
        "Cena restaurante", "Súper del mes", "Gasolina", "Netflix", 
        "Café", "Uber", "Farmacia", "Cine", "Internet", "Luz"
    ]
    
    cats_gastos = [c for c in categorias if c['tipo'] == 'gasto']
    cats_ingresos = [c for c in categorias if c['tipo'] == 'ingreso']

    if not cats_gastos:
        print("[ERROR] No hay categorías de gasto para generar datos sintéticos.")
        return

    for i in range(30):
        fecha_mov = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        
        # Unos cuantos gastos por día
        for _ in range(random.randint(1, 3)):
            cat = random.choice(cats_gastos)
            monto = random.randint(10000, 150000)
            desc = random.choice(descripciones_gastos)
            MovimientoRepository.crear(
                usuario_id=usuario_id,
                categoria_id=cat['id'],
                tipo='gasto',
                monto=monto,
                descripcion=f"{desc} (Demo)",
                fecha=f"{fecha_mov} {random.randint(8, 22):02}:00:00"
            )

        # Algún ingreso extra ocasional
        if cats_ingresos and random.random() < 0.2:
            cat = random.choice(cats_ingresos)
            monto = random.randint(500000, 1000000)
            MovimientoRepository.crear(
                usuario_id=usuario_id,
                categoria_id=cat['id'],
                tipo='ingreso',
                monto=monto,
                descripcion="Freelance / Bono (Demo)",
                fecha=f"{fecha_mov} 10:00:00"
            )

    print("[OK] Datos sintéticos generados con éxito.")

    # 6. Crear un presupuesto para que se vean alertas
    try:
        mes_actual = datetime.now().strftime("%Y-%m-01")
        PresupuestoRepository.crear(usuario_id, None, 3000000, mes_actual)
        print(f"[OK] Presupuesto global creado para {mes_actual}.")
    except:
        pass

    # 7. Añadir una notificación de bienvenida
    NotificacionRepository.crear(
        usuario_id=usuario_id,
        titulo="Demostración Lista",
        mensaje="Se han cargado datos sintéticos para que puedas ver el dashboard lleno.",
        tipo="exito"
    )

    print("\n=== DEMOSTRACIÓN CONFIGURADA CORRECTAMENTE ===")
    print(f"Email: {email_demo}")
    print(f"Password: {password_demo}")
    print("==============================================")

if __name__ == "__main__":
    create_demo_data()
