"""
Migration pour créer les extensions PostgreSQL
Roadmap Meta Base de Données - Phase P0/P2
"""

from django.db import migrations, connection


def create_postgres_extensions(apps, schema_editor):
    """Crée les extensions PostgreSQL si la base est PostgreSQL"""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
                print("Extensions PostgreSQL créées: unaccent, pg_trgm")
                
                # Extension pgvector optionnelle
                try:
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    print("Extension pgvector créée")
                except Exception:
                    print("Extension pgvector non disponible (optionnelle)")
                    
            except Exception as e:
                print(f"Erreur création extensions PostgreSQL: {e}")
    else:
        print(f"Base de données {connection.vendor} - Extensions PostgreSQL ignorées")


def drop_postgres_extensions(apps, schema_editor):
    """Supprime les extensions PostgreSQL si la base est PostgreSQL"""
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            try:
                cursor.execute("DROP EXTENSION IF EXISTS vector;")
                cursor.execute("DROP EXTENSION IF EXISTS pg_trgm;")
                cursor.execute("DROP EXTENSION IF EXISTS unaccent;")
                print("Extensions PostgreSQL supprimées")
            except Exception as e:
                print(f"Erreur suppression extensions: {e}")


class Migration(migrations.Migration):
    
    initial = True
    
    dependencies = []
    
    operations = [
        migrations.RunPython(
            create_postgres_extensions,
            reverse_code=drop_postgres_extensions
        ),
    ]
