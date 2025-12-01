"""
Migration S1 - Schéma V2 add-only
GIGA ROADMAP: colonnes search_tsv_v2 + triggers + index CONCURRENT
"""

from django.db import migrations, connection


def create_search_v2_schema(apps, schema_editor):
    """Crée le schéma V2 sans casser V1"""
    if connection.vendor != 'postgresql':
        print("PostgreSQL requis pour FTS V2 - ignoré")
        return
    
    with connection.cursor() as cursor:
        try:
            # 1. Colonnes search_tsv_v2 pour chaque table
            tables = ['referentiels_cepage', 'referentiels_parcelle', 'referentiels_unite']
            
            for table in tables:
                print(f"Ajout colonne search_tsv_v2 sur {table}")
                cursor.execute(f"""
                    ALTER TABLE {table} 
                    ADD COLUMN IF NOT EXISTS search_tsv_v2 tsvector;
                """)
            
            # 2. Fonction trigger générique V2
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_search_tsv_v2() RETURNS trigger AS $$
                BEGIN
                    -- Normalisation avancée : unaccent + champs multiples
                    NEW.search_tsv_v2 := to_tsvector('simple', 
                        unaccent(
                            coalesce(NEW.nom, '') || ' ' || 
                            coalesce(NEW.code, '') || ' ' ||
                            coalesce(NEW.couleur, '') || ' ' ||
                            coalesce(NEW.symbole, '') || ' ' ||
                            coalesce(NEW.type, '') || ' ' ||
                            coalesce(NEW.lieu_dit, '') || ' ' ||
                            coalesce(NEW.commune, '')
                        )
                    );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # 3. Triggers V2 sur chaque table
            for table in tables:
                trigger_name = f"trg_{table}_search_tsv_v2"
                print(f"Création trigger {trigger_name}")
                
                cursor.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON {table};")
                cursor.execute(f"""
                    CREATE TRIGGER {trigger_name}
                    BEFORE INSERT OR UPDATE ON {table}
                    FOR EACH ROW EXECUTE FUNCTION update_search_tsv_v2();
                """)
            
            # 4. Index GIN CONCURRENT (non bloquant)
            for table in tables:
                index_name = f"idx_{table}_search_tsv_v2"
                print(f"Création index CONCURRENT {index_name}")
                
                try:
                    cursor.execute(f"""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} 
                        ON {table} USING GIN (search_tsv_v2);
                    """)
                except Exception as e:
                    print(f"Avertissement index {index_name}: {e}")
            
            # 5. Index trigram pour fallback
            text_columns = [
                ('referentiels_cepage', 'nom'),
                ('referentiels_parcelle', 'nom'),
                ('referentiels_unite', 'nom'),
            ]
            
            for table, column in text_columns:
                index_name = f"idx_{table}_{column}_trgm_v2"
                print(f"Création index trigram {index_name}")
                
                try:
                    cursor.execute(f"""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name}
                        ON {table} USING GIN ({column} gin_trgm_ops);
                    """)
                except Exception as e:
                    print(f"Avertissement trigram {index_name}: {e}")
            
            # 6. Peupler les colonnes existantes
            for table in tables:
                print(f"Population initiale search_tsv_v2 sur {table}")
                cursor.execute(f"UPDATE {table} SET search_tsv_v2 = NULL;")  # Force trigger
            
            print("Schéma V2 créé avec succès - CONCURRENT")
            
        except Exception as e:
            print(f"Erreur création schéma V2: {e}")
            raise


def drop_search_v2_schema(apps, schema_editor):
    """Supprime le schéma V2 (rollback)"""
    if connection.vendor != 'postgresql':
        return
    
    with connection.cursor() as cursor:
        tables = ['referentiels_cepage', 'referentiels_parcelle', 'referentiels_unite']
        
        # Supprimer triggers
        for table in tables:
            cursor.execute(f"DROP TRIGGER IF EXISTS trg_{table}_search_tsv_v2 ON {table};")
        
        # Supprimer fonction
        cursor.execute("DROP FUNCTION IF EXISTS update_search_tsv_v2();")
        
        # Supprimer index (pas CONCURRENT pour le drop)
        for table in tables:
            cursor.execute(f"DROP INDEX IF EXISTS idx_{table}_search_tsv_v2;")
            cursor.execute(f"DROP INDEX IF EXISTS idx_{table}_nom_trgm_v2;")
        
        # Supprimer colonnes
        for table in tables:
            cursor.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS search_tsv_v2;")
        
        print("Schéma V2 supprimé")


class Migration(migrations.Migration):
    
    # Required so that CREATE INDEX CONCURRENTLY can run outside a transaction
    atomic = False
    
    dependencies = [
        ('referentiels', '0001_initial'),
        ('metadata', '0001_initial_extensions'),  # Besoin unaccent + pg_trgm
    ]
    
    operations = [
        migrations.RunPython(
            create_search_v2_schema,
            reverse_code=drop_search_v2_schema
        ),
    ]
