"""
Services pour l'export DRM (Déclaration Récapitulative Mensuelle)
"""
import os
import csv
import hashlib
from io import StringIO, BytesIO
from datetime import datetime, date
from decimal import Decimal
from calendar import monthrange

from django.db import transaction
from django.conf import settings
from django.core.files.storage import default_storage
from django.db.models import Sum, Q

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from .models import DRMExport, DRMLigneProduit
from monchai.apps.core.models import Mouvement, Lot, Vendange
from monchai.apps.sales.models import Produit


class DRMCalculService:
    """Service pour calculer les données DRM à partir des mouvements"""
    
    @staticmethod
    def calculer_donnees_periode(domaine, periode):
        """
        Calcule les données DRM pour une période donnée
        
        Args:
            domaine: Instance du domaine
            periode: String au format YYYY-MM
            
        Returns:
            Dict avec les totaux et détails par appellation
        """
        annee, mois = map(int, periode.split('-'))
        
        # Dates de début et fin de période
        debut_periode = date(annee, mois, 1)
        _, dernier_jour = monthrange(annee, mois)
        fin_periode = date(annee, mois, dernier_jour)
        
        # Période précédente pour le stock de début
        if mois == 1:
            periode_precedente = f"{annee-1}-12"
        else:
            periode_precedente = f"{annee}-{mois-1:02d}"
        
        # Calculer stock de début (= stock de fin de la période précédente)
        stock_debut = DRMCalculService._calculer_stock_fin_periode(domaine, periode_precedente)
        
        # Mouvements de la période
        mouvements_periode = Mouvement.objects.filter(
            domaine=domaine,
            date__gte=debut_periode,
            date__lte=fin_periode,
            status='valide'
        )
        
        # Calculer les totaux
        entrees_hl = Decimal('0')
        sorties_hl = Decimal('0')
        pertes_hl = Decimal('0')
        
        # Détail par appellation (pour Loire, on utilise Muscadet par défaut)
        lignes_produits = {}
        
        for mouvement in mouvements_periode:
            volume = mouvement.volume_hl
            
            # Déterminer l'appellation et couleur
            appellation = "Muscadet Sèvre-et-Maine"  # Par défaut pour Loire
            couleur = "blanc"  # Par défaut
            
            # Créer la clé pour regrouper
            cle_produit = (appellation, couleur)
            
            if cle_produit not in lignes_produits:
                lignes_produits[cle_produit] = {
                    'appellation': appellation,
                    'couleur': couleur,
                    'stock_debut_hl': Decimal('0'),
                    'entrees_vendange_hl': Decimal('0'),
                    'entrees_autres_hl': Decimal('0'),
                    'sorties_vente_hl': Decimal('0'),
                    'sorties_autres_hl': Decimal('0'),
                    'pertes_hl': Decimal('0'),
                    'references_lots': []
                }
            
            ligne = lignes_produits[cle_produit]
            
            # Classer le mouvement selon son type
            if mouvement.type == 'vendange_vers_cuve':
                ligne['entrees_vendange_hl'] += volume
                entrees_hl += volume
            elif mouvement.type == 'vente_sortie_stock':
                ligne['sorties_vente_hl'] += volume
                sorties_hl += volume
            elif mouvement.type == 'perte':
                ligne['pertes_hl'] += volume
                pertes_hl += volume
            elif mouvement.type == 'inter_cuves':
                # Les mouvements inter-cuves sont neutres pour le DRM
                pass
            elif mouvement.type == 'mise_en_bouteille':
                # La mise en bouteille est considérée comme une transformation, pas une sortie
                pass
            else:
                ligne['entrees_autres_hl'] += volume
                entrees_hl += volume
            
            # Ajouter la référence du lot si disponible
            if mouvement.source_lot and mouvement.source_lot.ref_interne:
                if mouvement.source_lot.ref_interne not in ligne['references_lots']:
                    ligne['references_lots'].append(mouvement.source_lot.ref_interne)
        
        # Calculer le stock de fin
        stock_fin = stock_debut + entrees_hl - sorties_hl - pertes_hl
        
        # Répartir le stock de début sur les lignes produits
        if lignes_produits and stock_debut > 0:
            # Répartition proportionnelle basée sur les entrées
            total_entrees = sum(
                ligne['entrees_vendange_hl'] + ligne['entrees_autres_hl'] 
                for ligne in lignes_produits.values()
            )
            
            if total_entrees > 0:
                for ligne in lignes_produits.values():
                    entrees_ligne = ligne['entrees_vendange_hl'] + ligne['entrees_autres_hl']
                    proportion = entrees_ligne / total_entrees
                    ligne['stock_debut_hl'] = stock_debut * proportion
            else:
                # Si pas d'entrées, répartir équitablement
                stock_par_ligne = stock_debut / len(lignes_produits)
                for ligne in lignes_produits.values():
                    ligne['stock_debut_hl'] = stock_par_ligne
        
        # Calculer le stock de fin pour chaque ligne
        for ligne in lignes_produits.values():
            ligne['stock_fin_hl'] = (
                ligne['stock_debut_hl'] +
                ligne['entrees_vendange_hl'] +
                ligne['entrees_autres_hl'] -
                ligne['sorties_vente_hl'] -
                ligne['sorties_autres_hl'] -
                ligne['pertes_hl']
            )
        
        return {
            'stock_debut_hl': stock_debut,
            'entrees_hl': entrees_hl,
            'sorties_hl': sorties_hl,
            'pertes_hl': pertes_hl,
            'stock_fin_hl': stock_fin,
            'lignes_produits': list(lignes_produits.values())
        }
    
    @staticmethod
    def _calculer_stock_fin_periode(domaine, periode):
        """Calcule le stock de fin pour une période donnée"""
        try:
            drm_export = DRMExport.objects.get(domaine=domaine, periode=periode)
            return drm_export.stock_fin_hl
        except DRMExport.DoesNotExist:
            # Si pas d'export précédent, calculer depuis le début
            return Decimal('0')


class DRMExportService:
    """Service pour générer les exports DRM"""
    
    @staticmethod
    @transaction.atomic
    def creer_export_drm(domaine, periode, region="Loire"):
        """
        Crée un export DRM pour une période donnée
        
        Args:
            domaine: Instance du domaine
            periode: String au format YYYY-MM
            region: Région viticole
            
        Returns:
            Instance DRMExport créée
        """
        # Vérifier si un export existe déjà
        drm_export, created = DRMExport.objects.get_or_create(
            domaine=domaine,
            periode=periode,
            defaults={
                'region': region,
                'status': 'brouillon'
            }
        )
        
        if not created and drm_export.status in ['genere', 'transmis', 'valide']:
            raise ValueError(f"Un export DRM existe déjà pour {periode} avec le statut {drm_export.get_status_display()}")
        
        # Calculer les données
        donnees = DRMCalculService.calculer_donnees_periode(domaine, periode)
        
        # Mettre à jour l'export principal
        drm_export.stock_debut_hl = donnees['stock_debut_hl']
        drm_export.entrees_hl = donnees['entrees_hl']
        drm_export.sorties_hl = donnees['sorties_hl']
        drm_export.pertes_hl = donnees['pertes_hl']
        drm_export.stock_fin_hl = donnees['stock_fin_hl']
        
        # Convertir les Decimal en float pour la sérialisation JSON
        data_serializable = {
            'stock_debut_hl': float(donnees['stock_debut_hl']),
            'entrees_hl': float(donnees['entrees_hl']),
            'sorties_hl': float(donnees['sorties_hl']),
            'pertes_hl': float(donnees['pertes_hl']),
            'stock_fin_hl': float(donnees['stock_fin_hl']),
            'lignes_produits': []
        }
        
        # Convertir les lignes produits
        for ligne_data in donnees['lignes_produits']:
            ligne_serializable = {}
            for key, value in ligne_data.items():
                if isinstance(value, Decimal):
                    ligne_serializable[key] = float(value)
                else:
                    ligne_serializable[key] = value
            data_serializable['lignes_produits'].append(ligne_serializable)
        
        drm_export.data = data_serializable
        drm_export.save()
        
        # Supprimer les anciennes lignes produits
        drm_export.lignes_produits.all().delete()
        
        # Créer les nouvelles lignes produits
        for ligne_data in donnees['lignes_produits']:
            DRMLigneProduit.objects.create(
                drm_export=drm_export,
                **ligne_data
            )
        
        return drm_export
    
    @staticmethod
    def generer_csv(drm_export):
        """
        Génère le fichier CSV pour l'export DRM
        
        Args:
            drm_export: Instance DRMExport
            
        Returns:
            Chemin du fichier CSV généré
        """
        # Créer le contenu CSV
        output = StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # En-têtes
        writer.writerow([
            'Période',
            'Domaine',
            'Région',
            'Appellation',
            'Couleur',
            'Stock début (HL)',
            'Entrées vendange (HL)',
            'Autres entrées (HL)',
            'Sorties vente (HL)',
            'Autres sorties (HL)',
            'Pertes (HL)',
            'Stock fin (HL)',
            'Références lots'
        ])
        
        # Lignes de données
        for ligne in drm_export.lignes_produits.all():
            writer.writerow([
                drm_export.periode,
                drm_export.domaine.nom,
                drm_export.region,
                ligne.appellation,
                ligne.couleur,
                str(ligne.stock_debut_hl),
                str(ligne.entrees_vendange_hl),
                str(ligne.entrees_autres_hl),
                str(ligne.sorties_vente_hl),
                str(ligne.sorties_autres_hl),
                str(ligne.pertes_hl),
                str(ligne.stock_fin_hl),
                ', '.join(ligne.references_lots)
            ])
        
        # Ligne de totaux
        writer.writerow([
            drm_export.periode,
            drm_export.domaine.nom,
            drm_export.region,
            'TOTAL',
            '',
            str(drm_export.stock_debut_hl),
            str(drm_export.entrees_hl),
            '0',  # Autres entrées (calculé dans entrees_hl)
            str(drm_export.sorties_hl),
            '0',  # Autres sorties (calculé dans sorties_hl)
            str(drm_export.pertes_hl),
            str(drm_export.stock_fin_hl),
            ''
        ])
        
        # Sauvegarder le fichier
        filename = f"drm/{drm_export.domaine.id}/DRM_{drm_export.periode}_{drm_export.domaine.nom.replace(' ', '_')}.csv"
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(os.path.join(settings.MEDIA_ROOT, filename)), exist_ok=True)
        
        # Sauvegarder
        csv_content = output.getvalue()
        file_path = default_storage.save(filename, StringIO(csv_content))
        
        # Calculer le checksum
        checksum = hashlib.md5(csv_content.encode('utf-8')).hexdigest()
        
        # Mettre à jour l'export
        drm_export.chemin_csv = file_path
        if not drm_export.checksums:
            drm_export.checksums = {}
        drm_export.checksums['csv'] = checksum
        drm_export.save()
        
        return file_path
    
    @staticmethod
    def generer_pdf(drm_export):
        """
        Génère le fichier PDF pour l'export DRM
        
        Args:
            drm_export: Instance DRMExport
            
        Returns:
            Chemin du fichier PDF généré
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Construire le contenu
        story = []
        
        # Titre
        story.append(Paragraph(f"DÉCLARATION RÉCAPITULATIVE MENSUELLE", title_style))
        story.append(Paragraph(f"Période: {drm_export.periode} - Région: {drm_export.region}", styles['Normal']))
        story.append(Paragraph(f"Domaine: {drm_export.domaine.nom}", styles['Normal']))
        story.append(Spacer(1, 30))
        
        # Résumé général
        resume_data = [
            ["Résumé général", "Volume (HL)"],
            ["Stock début de période", f"{drm_export.stock_debut_hl:.2f}"],
            ["Entrées totales", f"{drm_export.entrees_hl:.2f}"],
            ["Sorties totales", f"{drm_export.sorties_hl:.2f}"],
            ["Pertes totales", f"{drm_export.pertes_hl:.2f}"],
            ["Stock fin de période", f"{drm_export.stock_fin_hl:.2f}"],
        ]
        
        resume_table = Table(resume_data, colWidths=[8*cm, 4*cm])
        resume_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        
        story.append(resume_table)
        story.append(Spacer(1, 30))
        
        # Détail par appellation
        if drm_export.lignes_produits.exists():
            story.append(Paragraph("Détail par appellation", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            detail_data = [
                ["Appellation", "Couleur", "Stock début", "Entrées", "Sorties", "Pertes", "Stock fin"]
            ]
            
            for ligne in drm_export.lignes_produits.all():
                detail_data.append([
                    ligne.appellation,
                    ligne.couleur.title(),
                    f"{ligne.stock_debut_hl:.2f}",
                    f"{ligne.entrees_vendange_hl + ligne.entrees_autres_hl:.2f}",
                    f"{ligne.sorties_vente_hl + ligne.sorties_autres_hl:.2f}",
                    f"{ligne.pertes_hl:.2f}",
                    f"{ligne.stock_fin_hl:.2f}"
                ])
            
            detail_table = Table(detail_data, colWidths=[4*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
            detail_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ]))
            
            story.append(detail_table)
        
        # Pied de page
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", styles['Normal']))
        story.append(Paragraph("MonChai - Gestion viticole", styles['Normal']))
        
        # Générer le PDF
        doc.build(story)
        
        # Sauvegarder le fichier
        filename = f"drm/{drm_export.domaine.id}/DRM_{drm_export.periode}_{drm_export.domaine.nom.replace(' ', '_')}.pdf"
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(os.path.join(settings.MEDIA_ROOT, filename)), exist_ok=True)
        
        # Sauvegarder
        buffer.seek(0)
        file_path = default_storage.save(filename, buffer)
        
        # Calculer le checksum
        buffer.seek(0)
        checksum = hashlib.md5(buffer.read()).hexdigest()
        
        # Mettre à jour l'export
        drm_export.chemin_pdf = file_path
        if not drm_export.checksums:
            drm_export.checksums = {}
        drm_export.checksums['pdf'] = checksum
        drm_export.status = 'genere'
        drm_export.save()
        
        return file_path
    
    @staticmethod
    @transaction.atomic
    def generer_export_complet(domaine, periode, region="Loire"):
        """
        Génère un export DRM complet (calcul + CSV + PDF)
        
        Args:
            domaine: Instance du domaine
            periode: String au format YYYY-MM
            region: Région viticole
            
        Returns:
            Instance DRMExport avec fichiers générés
        """
        # Créer l'export
        drm_export = DRMExportService.creer_export_drm(domaine, periode, region)
        
        # Générer les fichiers
        DRMExportService.generer_csv(drm_export)
        DRMExportService.generer_pdf(drm_export)
        
        return drm_export
