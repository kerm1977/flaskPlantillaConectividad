# app.py
import os
from flask import Flask
from config import Config
from db import db, configure_db_uri, configure_db_engine_options
from routes import bp, inject_site_content
from users import inject_superusers

import models_core, models_forms, models_rifas, models_publicaciones  # Cargar todos los modelos


from db_optimizer import optimize_sqlite, create_indexes
from db_migrations import run_all as run_migrations


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Configuración inteligente de Base de Datos
    app.config['SQLALCHEMY_DATABASE_URI'] = configure_db_uri()
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = configure_db_engine_options()

    # Inicializar la base de datos con la app
    db.init_app(app)
    
    # Registrar las rutas
    app.register_blueprint(bp)


    # Crear tablas e inyectar usuarios dentro del contexto de la aplicación
    with app.app_context():
        # Crea el archivo base_app.db y todas sus tablas si no existen
        db.create_all()

        # Optimizar SQLite, crear índices y aplicar migraciones
        optimize_sqlite()
        create_indexes()
        run_migrations()
        
        # Inyecta automáticamente los superusuarios
        inject_superusers()
        # Inyecta el contenido por defecto del sitio si no existe
        inject_site_content()

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5050))
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=port)