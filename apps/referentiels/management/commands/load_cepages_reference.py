"""
Commande pour charger le référentiel officiel des cépages français
"""
from django.core.management.base import BaseCommand
from apps.referentiels.models import CepageReference


# Base de données complète des cépages français avec leurs régions
# Source: Côté Vins - Liste exhaustive par région viticole
CEPAGES_FRANCAIS = [
    # ============================================================
    # CÉPAGES LES PLUS COURANTS EN FRANCE
    # ============================================================
    {'nom': 'Ugni Blanc', 'couleur': 'blanc', 'regions': ['bordeaux', 'sud_ouest', 'languedoc', 'provence'], 'synonymes': ['Trebbiano', 'Saint-Émilion']},
    {'nom': 'Merlot', 'couleur': 'rouge', 'regions': ['bordeaux', 'sud_ouest', 'languedoc'], 'synonymes': []},
    {'nom': 'Grenache Noir', 'couleur': 'rouge', 'regions': ['rhone', 'languedoc', 'provence'], 'synonymes': ['Grenache', 'Garnacha']},
    {'nom': 'Syrah', 'couleur': 'rouge', 'regions': ['rhone', 'languedoc', 'provence', 'loire'], 'synonymes': ['Shiraz', 'Sérine']},
    {'nom': 'Chardonnay', 'couleur': 'blanc', 'regions': ['bourgogne', 'champagne', 'jura', 'languedoc', 'beaujolais', 'savoie'], 'synonymes': ['Beaunois', 'Morillon', 'Gamay Blanc']},
    {'nom': 'Sauvignon Blanc', 'couleur': 'blanc', 'regions': ['loire', 'bordeaux', 'languedoc', 'bourgogne'], 'synonymes': ['Blanc Fumé', 'Sauvignon']},
    {'nom': 'Cabernet Sauvignon', 'couleur': 'rouge', 'regions': ['bordeaux', 'languedoc', 'provence'], 'synonymes': ['Petit Cabernet', 'Vidure']},
    {'nom': 'Carignan', 'couleur': 'rouge', 'regions': ['languedoc', 'rhone', 'provence'], 'synonymes': ['Mazuelo', 'Carignane']},
    {'nom': 'Pinot Noir', 'couleur': 'rouge', 'regions': ['bourgogne', 'champagne', 'alsace', 'loire', 'jura', 'savoie'], 'synonymes': ['Pinot Fin', 'Morillon Noir']},
    {'nom': 'Gamay', 'couleur': 'rouge', 'regions': ['beaujolais', 'bourgogne', 'loire', 'savoie'], 'synonymes': ['Gamay Noir']},
    
    # ============================================================
    # VALLÉE DE LA LOIRE
    # ============================================================
    # Blancs
    {'nom': 'Chenin Blanc', 'couleur': 'blanc', 'regions': ['loire'], 'synonymes': ['Pineau de la Loire']},
    {'nom': 'Melon de Bourgogne', 'couleur': 'blanc', 'regions': ['loire'], 'synonymes': ['Muscadet']},
    {'nom': 'Menu Pineau', 'couleur': 'blanc', 'regions': ['loire'], 'synonymes': ['Arbois']},
    # Rouges
    {'nom': 'Cabernet Franc', 'couleur': 'rouge', 'regions': ['bordeaux', 'loire', 'sud_ouest'], 'synonymes': ['Bouchet', 'Breton']},
    {'nom': 'Groslot', 'couleur': 'rouge', 'regions': ['loire'], 'synonymes': ['Grolleau']},
    {'nom': 'Gamay Teinturier', 'couleur': 'rouge', 'regions': ['loire'], 'synonymes': []},
    
    # ============================================================
    # BORDEAUX
    # ============================================================
    # Blancs
    {'nom': 'Sémillon', 'couleur': 'blanc', 'regions': ['bordeaux', 'sud_ouest'], 'synonymes': []},
    {'nom': 'Muscadelle', 'couleur': 'blanc', 'regions': ['bordeaux', 'sud_ouest'], 'synonymes': []},
    {'nom': 'Sauvignon Gris', 'couleur': 'gris', 'regions': ['bordeaux'], 'synonymes': []},
    # Rouges
    {'nom': 'Malbec', 'couleur': 'rouge', 'regions': ['bordeaux', 'sud_ouest', 'loire'], 'synonymes': ['Côt', 'Auxerrois']},
    {'nom': 'Petit Verdot', 'couleur': 'rouge', 'regions': ['bordeaux', 'languedoc'], 'synonymes': []},
    {'nom': 'Carménère', 'couleur': 'rouge', 'regions': ['bordeaux'], 'synonymes': []},
    
    # ============================================================
    # SUD-OUEST
    # ============================================================
    # Blancs
    {'nom': 'Petit Manseng', 'couleur': 'blanc', 'regions': ['sud_ouest'], 'synonymes': []},
    {'nom': 'Gros Manseng', 'couleur': 'blanc', 'regions': ['sud_ouest'], 'synonymes': []},
    {'nom': 'Colombard', 'couleur': 'blanc', 'regions': ['bordeaux', 'sud_ouest'], 'synonymes': []},
    {'nom': 'Len de l\'El', 'couleur': 'blanc', 'regions': ['sud_ouest'], 'synonymes': ['Loin de l\'Œil']},
    {'nom': 'Mauzac', 'couleur': 'blanc', 'regions': ['languedoc', 'sud_ouest'], 'synonymes': []},
    {'nom': 'Courbu Blanc', 'couleur': 'blanc', 'regions': ['sud_ouest'], 'synonymes': ['Courbu']},
    {'nom': 'Petit Courbu', 'couleur': 'blanc', 'regions': ['sud_ouest'], 'synonymes': []},
    {'nom': 'Ondenc', 'couleur': 'blanc', 'regions': ['sud_ouest'], 'synonymes': []},
    {'nom': 'Arrufiac', 'couleur': 'blanc', 'regions': ['sud_ouest'], 'synonymes': []},
    {'nom': 'Baroque', 'couleur': 'blanc', 'regions': ['sud_ouest'], 'synonymes': []},
    # Rouges
    {'nom': 'Tannat', 'couleur': 'rouge', 'regions': ['sud_ouest'], 'synonymes': []},
    {'nom': 'Négrette', 'couleur': 'rouge', 'regions': ['sud_ouest'], 'synonymes': []},
    {'nom': 'Fer Servadou', 'couleur': 'rouge', 'regions': ['sud_ouest'], 'synonymes': ['Mansois', 'Braucol', 'Pinenc']},
    {'nom': 'Duras', 'couleur': 'rouge', 'regions': ['sud_ouest'], 'synonymes': []},
    {'nom': 'Abouriou', 'couleur': 'rouge', 'regions': ['sud_ouest'], 'synonymes': []},
    
    # ============================================================
    # LANGUEDOC-ROUSSILLON
    # ============================================================
    # Blancs
    {'nom': 'Grenache Blanc', 'couleur': 'blanc', 'regions': ['rhone', 'languedoc'], 'synonymes': []},
    {'nom': 'Muscat', 'couleur': 'blanc', 'regions': ['languedoc', 'alsace', 'rhone'], 'synonymes': ['Muscat Blanc']},
    {'nom': 'Bourboulenc', 'couleur': 'blanc', 'regions': ['rhone', 'languedoc', 'provence'], 'synonymes': []},
    {'nom': 'Clairette', 'couleur': 'blanc', 'regions': ['rhone', 'languedoc', 'provence'], 'synonymes': []},
    {'nom': 'Picpoul', 'couleur': 'blanc', 'regions': ['languedoc', 'rhone'], 'synonymes': ['Piquepoul']},
    {'nom': 'Carignan Blanc', 'couleur': 'blanc', 'regions': ['languedoc'], 'synonymes': []},
    {'nom': 'Grenache Gris', 'couleur': 'gris', 'regions': ['rhone', 'languedoc'], 'synonymes': []},
    {'nom': 'Marsanne', 'couleur': 'blanc', 'regions': ['rhone', 'languedoc'], 'synonymes': []},
    {'nom': 'Roussanne', 'couleur': 'blanc', 'regions': ['rhone', 'savoie', 'languedoc'], 'synonymes': ['Bergeron']},
    {'nom': 'Vermentino', 'couleur': 'blanc', 'regions': ['corse', 'provence', 'languedoc'], 'synonymes': ['Rolle', 'Malvoisie de Corse']},
    {'nom': 'Maccabeu', 'couleur': 'blanc', 'regions': ['languedoc', 'rhone'], 'synonymes': ['Macabeo', 'Viura']},
    {'nom': 'Viognier', 'couleur': 'blanc', 'regions': ['rhone', 'languedoc'], 'synonymes': []},
    {'nom': 'Souvignier Gris', 'couleur': 'gris', 'regions': ['languedoc'], 'synonymes': []},
    {'nom': 'Malvoisie', 'couleur': 'blanc', 'regions': ['languedoc'], 'synonymes': []},
    # Rouges
    {'nom': 'Cinsault', 'couleur': 'rouge', 'regions': ['rhone', 'provence', 'languedoc'], 'synonymes': ['Cinsaut']},
    {'nom': 'Mourvèdre', 'couleur': 'rouge', 'regions': ['rhone', 'provence', 'languedoc'], 'synonymes': ['Monastrell']},
    {'nom': 'Lledoner Pelut', 'couleur': 'rouge', 'regions': ['languedoc'], 'synonymes': []},
    
    # ============================================================
    # PROVENCE
    # ============================================================
    # Blancs
    {'nom': 'Rolle', 'couleur': 'blanc', 'regions': ['provence', 'languedoc', 'rhone'], 'synonymes': ['Vermentino']},
    # Rouges
    {'nom': 'Tibouren', 'couleur': 'rouge', 'regions': ['provence'], 'synonymes': []},
    
    # ============================================================
    # CORSE
    # ============================================================
    # Blancs
    {'nom': 'Muscat à Petits Grains', 'couleur': 'blanc', 'regions': ['alsace', 'corse', 'rhone', 'languedoc'], 'synonymes': ['Muscat Blanc', 'Muscat de Frontignan']},
    {'nom': 'Barbarossa', 'couleur': 'blanc', 'regions': ['corse'], 'synonymes': []},
    # Rouges
    {'nom': 'Sciaccarello', 'couleur': 'rouge', 'regions': ['corse'], 'synonymes': []},
    {'nom': 'Nielluccio', 'couleur': 'rouge', 'regions': ['corse'], 'synonymes': []},
    
    # ============================================================
    # VALLÉE DU RHÔNE
    # ============================================================
    # Blancs
    {'nom': 'Gros Vert', 'couleur': 'blanc', 'regions': ['rhone'], 'synonymes': []},
    {'nom': 'Picardan', 'couleur': 'blanc', 'regions': ['rhone'], 'synonymes': []},
    # Rouges
    {'nom': 'Clairette Rose', 'couleur': 'rose', 'regions': ['rhone'], 'synonymes': []},
    {'nom': 'Counoise', 'couleur': 'rouge', 'regions': ['rhone'], 'synonymes': []},
    {'nom': 'Marselan', 'couleur': 'rouge', 'regions': ['languedoc', 'rhone'], 'synonymes': []},
    {'nom': 'Muscardin', 'couleur': 'rouge', 'regions': ['rhone'], 'synonymes': []},
    {'nom': 'Vaccarèse', 'couleur': 'rouge', 'regions': ['rhone'], 'synonymes': []},
    {'nom': 'Terret Noir', 'couleur': 'rouge', 'regions': ['rhone', 'languedoc'], 'synonymes': []},
    
    # ============================================================
    # BOURGOGNE
    # ============================================================
    # Blancs
    {'nom': 'Aligoté', 'couleur': 'blanc', 'regions': ['bourgogne', 'savoie'], 'synonymes': []},
    # Rouges
    {'nom': 'César', 'couleur': 'rouge', 'regions': ['bourgogne'], 'synonymes': []},
    
    # ============================================================
    # CHAMPAGNE
    # ============================================================
    # Blancs
    {'nom': 'Arbane', 'couleur': 'blanc', 'regions': ['champagne'], 'synonymes': []},
    {'nom': 'Petit Meslier', 'couleur': 'blanc', 'regions': ['champagne'], 'synonymes': []},
    {'nom': 'Fromenteau', 'couleur': 'blanc', 'regions': ['champagne'], 'synonymes': []},
    {'nom': 'Pinot Blanc', 'couleur': 'blanc', 'regions': ['alsace', 'bourgogne', 'champagne'], 'synonymes': ['Clevner', 'Klevner']},
    {'nom': 'Pinot Gris', 'couleur': 'gris', 'regions': ['alsace', 'bourgogne', 'champagne', 'savoie'], 'synonymes': ['Tokay Pinot Gris', 'Pinot Beurot']},
    # Rouges
    {'nom': 'Pinot Meunier', 'couleur': 'rouge', 'regions': ['champagne'], 'synonymes': ['Meunier', 'Schwarzriesling']},
    
    # ============================================================
    # ALSACE
    # ============================================================
    # Blancs
    {'nom': 'Riesling', 'couleur': 'blanc', 'regions': ['alsace'], 'synonymes': []},
    {'nom': 'Gewurztraminer', 'couleur': 'blanc', 'regions': ['alsace', 'jura'], 'synonymes': ['Gewürztraminer', 'Traminer']},
    {'nom': 'Sylvaner', 'couleur': 'blanc', 'regions': ['alsace'], 'synonymes': []},
    {'nom': 'Chasselas', 'couleur': 'blanc', 'regions': ['savoie', 'alsace'], 'synonymes': ['Fendant', 'Gutedel']},
    {'nom': 'Klevener de Heiligenstein', 'couleur': 'blanc', 'regions': ['alsace'], 'synonymes': ['Savagnin Rose']},
    {'nom': 'Auxerrois', 'couleur': 'blanc', 'regions': ['alsace', 'lorraine'], 'synonymes': []},
    
    # ============================================================
    # JURA
    # ============================================================
    # Blancs
    {'nom': 'Savagnin', 'couleur': 'blanc', 'regions': ['jura'], 'synonymes': ['Traminer', 'Naturé']},
    {'nom': 'Savagnin Muscaté', 'couleur': 'blanc', 'regions': ['jura'], 'synonymes': []},
    # Rouges
    {'nom': 'Poulsard', 'couleur': 'rouge', 'regions': ['jura', 'savoie'], 'synonymes': ['Ploussard']},
    {'nom': 'Trousseau', 'couleur': 'rouge', 'regions': ['jura'], 'synonymes': []},
    
    # ============================================================
    # BEAUJOLAIS ET LYONNAIS
    # ============================================================
    # Blancs
    {'nom': 'Tressallier', 'couleur': 'blanc', 'regions': ['beaujolais'], 'synonymes': []},
    
    # ============================================================
    # SAVOIE ET BUGEY
    # ============================================================
    # Blancs
    {'nom': 'Jacquère', 'couleur': 'blanc', 'regions': ['savoie'], 'synonymes': []},
    {'nom': 'Altesse', 'couleur': 'blanc', 'regions': ['savoie'], 'synonymes': ['Roussette']},
    {'nom': 'Molette', 'couleur': 'blanc', 'regions': ['savoie'], 'synonymes': []},
    {'nom': 'Gringet', 'couleur': 'blanc', 'regions': ['savoie'], 'synonymes': []},
    {'nom': 'Mondeuse Blanche', 'couleur': 'blanc', 'regions': ['savoie'], 'synonymes': []},
    {'nom': 'Verdesse', 'couleur': 'blanc', 'regions': ['savoie'], 'synonymes': []},
    # Rouges
    {'nom': 'Mondeuse', 'couleur': 'rouge', 'regions': ['savoie', 'jura'], 'synonymes': []},
    {'nom': 'Persan', 'couleur': 'rouge', 'regions': ['savoie'], 'synonymes': []},
    {'nom': 'Étraire de l\'Aduï', 'couleur': 'rouge', 'regions': ['savoie'], 'synonymes': []},
    {'nom': 'Douce Noire', 'couleur': 'rouge', 'regions': ['savoie'], 'synonymes': []},
    
    # ============================================================
    # CÉPAGES COMPLÉMENTAIRES / ANCIENS / RARES
    # ============================================================
    {'nom': 'Grolleau', 'couleur': 'rouge', 'regions': ['loire'], 'synonymes': ['Groslot']},
    {'nom': 'Pineau d\'Aunis', 'couleur': 'rouge', 'regions': ['loire'], 'synonymes': ['Chenin Noir']},
    {'nom': 'Romorantin', 'couleur': 'blanc', 'regions': ['loire'], 'synonymes': []},
    {'nom': 'Gros Plant', 'couleur': 'blanc', 'regions': ['loire'], 'synonymes': ['Folle Blanche']},
    {'nom': 'Terret Blanc', 'couleur': 'blanc', 'regions': ['languedoc'], 'synonymes': []},
    {'nom': 'Biancu Gentile', 'couleur': 'blanc', 'regions': ['corse'], 'synonymes': []},
    {'nom': 'Prunelard', 'couleur': 'rouge', 'regions': ['sud_ouest'], 'synonymes': []},
    {'nom': 'Braquet', 'couleur': 'rouge', 'regions': ['provence'], 'synonymes': []},
    {'nom': 'Calitor', 'couleur': 'rouge', 'regions': ['provence'], 'synonymes': []},
    
    # === CÉPAGES INTERNATIONAUX CULTIVÉS EN FRANCE ===
    {'nom': 'Tempranillo', 'couleur': 'rouge', 'regions': ['languedoc'], 'synonymes': []},
    {'nom': 'Alicante Bouschet', 'couleur': 'rouge', 'regions': ['languedoc'], 'synonymes': ['Alicante Henri Bouschet']},
]


class Command(BaseCommand):
    help = 'Charge le référentiel officiel des cépages français'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recharge tous les cépages même s\'ils existent déjà',
        )

    def handle(self, *args, **options):
        created = 0
        updated = 0
        skipped = 0

        for data in CEPAGES_FRANCAIS:
            nom = data['nom']
            
            try:
                cepage, is_created = CepageReference.objects.update_or_create(
                    nom=nom,
                    defaults={
                        'couleur': data['couleur'],
                        'regions': data.get('regions', []),
                        'synonymes': data.get('synonymes', []),
                        'pays': 'France',
                    }
                )
                
                if is_created:
                    created += 1
                    self.stdout.write(self.style.SUCCESS(f'  + {nom}'))
                else:
                    if options['force']:
                        updated += 1
                        self.stdout.write(f'  ~ {nom} (mis à jour)')
                    else:
                        skipped += 1
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ {nom}: {e}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Terminé: {created} créés, {updated} mis à jour, {skipped} ignorés'
        ))
        self.stdout.write(f'Total cépages en base: {CepageReference.objects.count()}')
