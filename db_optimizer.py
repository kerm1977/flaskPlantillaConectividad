from db import db


def optimize_sqlite():
    """Activa WAL, caché y otras optimizaciones de SQLite para alto rendimiento."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")
        cursor.execute("PRAGMA foreign_keys=ON")
        conn.commit()
        conn.close()
        print("[DB] SQLite optimizado: WAL, cache, mmap activados.")
    except Exception as e:
        print(f"[DB] Error optimizando SQLite: {e}")


def create_indexes():
    """Crea índices útiles sobre tablas frecuentes."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        indexes = [
            ("idx_user_email", "user", "email"),
            ("idx_user_role", "user", "role"),
            ("idx_event_slug", "event", "slug"),
            ("idx_event_fecha", "event", "fecha"),
            ("idx_form_slug", "form", "slug"),
            ("idx_form_response_form_id", "form_response", "form_id"),
            ("idx_raffle_slug", "raffle", "slug"),
            ("idx_hiker_cedula", "hiker", "cedula"),
        ]
        for name, table, column in indexes:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column})")
        conn.commit()
        conn.close()
        print("[DB] Índices creados/verificados.")
    except Exception as e:
        print(f"[DB] Error creando índices: {e}")
