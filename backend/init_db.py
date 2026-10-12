# backend/init_db.py
"""
Script para inicializar la base de datos con tablas y datos de prueba
"""
import sys
import os

# Evita UnicodeEncodeError con los emojis de este script en consolas Windows
# cuya codepage por defecto no es UTF-8 (cp1252).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.db.database import engine, SessionLocal
    from app.db.migrations import run_migrations
    from app.models.models import MedicalStaff
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("\nVerifica que:")
    print("1. Estés en el directorio 'backend'")
    print("2. El entorno virtual esté activado")
    print("3. Hayas instalado todas las dependencias: pip install -r requirements.txt")
    sys.exit(1)

def init_database():
    """Crear/actualizar las tablas aplicando las migraciones de Alembic"""
    try:
        print("\n📋 Aplicando migraciones (alembic upgrade head)...")
        run_migrations()
        print("✓ Esquema de base de datos al dia")
        return True
    except Exception as e:
        print(f"✗ Error aplicando migraciones: {e}")
        print("\nPosibles causas:")
        print("- PostgreSQL no está ejecutándose")
        print("- Credenciales incorrectas en .env")
        print("- Base de datos 'triage_db' no existe")
        return False

def create_sample_staff():
    """Crear personal médico de ejemplo"""
    print("\n👥 Creando personal médico de ejemplo...")
    db = SessionLocal()
    
    try:
        # Verificar si ya existen datos
        existing = db.query(MedicalStaff).first()
        if existing:
            print("⚠️  Personal médico ya existe en la base de datos")
            print(f"   Encontrados {db.query(MedicalStaff).count()} registros")
            return True
        
        staff_data = [
            {
                'employee_id': 'DOC001',
                'full_name': 'Dr. Carlos García',
                'role': 'cardiologist',
                'specialization': 'Cardiología',
                'license_number': 'MED-12345',
                'max_patient_capacity': 70,
                'is_available': True
            },
            {
                'employee_id': 'DOC002',
                'full_name': 'Dra. María Martínez',
                'role': 'emergency_physician',
                'specialization': 'Medicina de Urgencias',
                'license_number': 'MED-12346',
                'max_patient_capacity': 60,
                'is_available': True
            },
            {
                'employee_id': 'DOC003',
                'full_name': 'Dr. Juan López',
                'role': 'emergency_physician',
                'specialization': 'Medicina de Urgencias',
                'license_number': 'MED-12347',
                'max_patient_capacity': 50,
                'is_available': True
            },
            {
                'employee_id': 'DOC004',
                'full_name': 'Dra. Ana Fernández',
                'role': 'general_physician',
                'specialization': 'Cirugía General',
                'license_number': 'MED-12348',
                'max_patient_capacity': 50,
                'is_available': True
            }
        ]
        
        for staff in staff_data:
            db_staff = MedicalStaff(**staff)
            db.add(db_staff)
        
        db.commit()
        print(f"✓ {len(staff_data)} miembros del personal médico creados")
        return True
        
    except Exception as e:
        print(f"✗ Error creando personal: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("INICIALIZANDO BASE DE DATOS DEL SISTEMA DE TRIAGE")
    print("="*60)
    
    # Verificar conexion a la base de datos
    is_postgres = engine.url.get_backend_name() == "postgresql"
    print(f"\n🔌 Verificando conexión a la base de datos ({engine.url.get_backend_name()})...")
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            if is_postgres:
                version = conn.execute(text("SELECT version()")).fetchone()[0]
                print("✓ Conectado a PostgreSQL")
                print(f"  Versión: {version.split(',')[0]}")
            else:
                conn.execute(text("SELECT 1"))
                print("✓ Conectado (SQLite, cero configuración)")
    except Exception as e:
        print(f"✗ Error de conexión: {e}")
        if is_postgres:
            print("\n💡 Soluciones:")
            print("1. Verifica que PostgreSQL esté ejecutándose:")
            print("   - Windows: Servicios → PostgreSQL")
            print("   - Docker: docker ps")
            print("\n2. Verifica las credenciales en el archivo .env")
            print("   DATABASE_URL=postgresql://usuario:password@localhost:5432/triage_db")
            print("\n3. Crea la base de datos si no existe:")
            print("   psql -U postgres")
            print("   CREATE DATABASE triage_db;")
            print("   CREATE USER triage_user WITH PASSWORD 'triage_password';")
            print("   GRANT ALL PRIVILEGES ON DATABASE triage_db TO triage_user;")
        sys.exit(1)
    
    # Inicializar tablas
    success = init_database()
    if not success:
        sys.exit(1)
    
    # Crear datos de ejemplo
    success = create_sample_staff()
    if not success:
        print("\n⚠️  Las tablas se crearon pero hubo errores con los datos de ejemplo")
    
    print("\n" + "="*60)
    print("✓ BASE DE DATOS INICIALIZADA CORRECTAMENTE")
    print("="*60)
    print("\n🚀 Siguiente paso:")
    print("   uvicorn app.main:app --reload")
    print("\n📚 Documentación API:")
    print("   http://localhost:8000/docs")
    print("="*60)