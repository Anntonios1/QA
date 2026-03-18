# ControlCash - Sistema Profesional de Control Financiero

## Arquitectura de 3 Capas (Separacion de Responsabilidades)

```
├── db/          → Capa de Datos (PostgreSQL + Esquemas)
├── api/         → Capa de Negocio (Flask REST API)
├── app/         → Capa de Presentacion (HTML/CSS/JS - Glass UI Profesional)
├── docs/        → Documentacion bajo normas internacionales
└── tests/       → Pruebas unitarias e integracion
```

## Normas Internacionales Aplicadas

| Norma | Aplicacion |
|-------|-----------|
| CMMI | Niveles de madurez del proceso de desarrollo |
| ISO 9001 | Sistema de gestion de calidad |
| IEEE 730 | Plan de aseguramiento de calidad del software |
| ISO 9001:2000 | Enfoque basado en procesos |
| ISO 9126 | Modelo de calidad del software |
| ISO 14598 | Evaluacion del producto software |
| ISO/IEC 25000 (SQuaRE) | Calidad del producto software |
| ISO/IEC 12207 | Procesos del ciclo de vida del software |
| ISO/IEC 15504 (SPICE) | Evaluacion y mejora de procesos |
| ISO/IEC 20000 | Gestion de servicios de TI |
| ISO/IEC 27001 | Seguridad de la informacion |
| OWASP Mobile Top 10 | Seguridad en aplicaciones moviles |

## Actores del Sistema

### Usuario
- **Quien es:** Persona que utiliza el sistema para registrar y consultar su informacion financiera.
- **Que hace:** Ingresa datos, registra movimientos y consulta su balance.

### Sistema
- **Quien es:** Aplicacion que procesa, almacena y organiza la informacion financiera.
- **Que hace:** Recibe datos, valida, guarda y genera notificaciones/resumenes.

## Funciones Principales
1. Registrarse
2. Iniciar sesion (con autenticacion biometrica opcional)
3. Gestionar movimientos (ingresos/gastos)
4. Solicitar balance
5. Validar datos
6. Notificaciones
7. Resumen financiero
8. Escaneo de recibos (OCR con IA)
9. Asistente financiero (Chat IA)

## Seguridad
- Autenticacion biometrica (Capacitor - huella/Face ID)
- Session timeout por inactividad (ISO 27001)
- Cifrado de contrasenas con bcrypt
- Indicador de fortaleza de contrasena (OWASP)
- Content Security Policy headers

## Requisitos
- Python 3.8+
- Flask
- PostgreSQL
- pg8000 (driver PostgreSQL puro Python)
- Navegador moderno (Chrome, Firefox, Edge)

## Instalacion

```bash
# 1. Instalar dependencias de la API
cd api
pip install -r requirements.txt

# 2. Configurar PostgreSQL
# Crear base de datos 'gastos_db' en PostgreSQL
# Copiar .env.example a .env y configurar credenciales

# 3. Ejecutar la API (inicializa la BD automaticamente)
python app.py

# 4. Abrir la aplicacion en http://localhost:5000
```
