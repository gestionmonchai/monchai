"""
Générateur de PDF pour les factures avec mentions légales
"""
import os
from io import BytesIO
from datetime import date
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

from django.conf import settings
from django.core.files.storage import default_storage

from .models import Facture


class FacturePDFGenerator:
    """Générateur de PDF pour les factures"""
    
    def __init__(self, facture):
        self.facture = facture
        self.commande = facture.commande
        self.client = self.commande.client
        self.domaine = facture.domaine
        
        # Styles
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=10
        )
        self.normal_style = self.styles['Normal']
        self.right_align_style = ParagraphStyle(
            'RightAlign',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT
        )
    
    def generate_pdf(self, save_to_file=True):
        """
        Génère le PDF de la facture
        
        Args:
            save_to_file: Si True, sauvegarde le fichier et met à jour le modèle
            
        Returns:
            BytesIO buffer du PDF
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
        
        # Construire le contenu
        story = []
        
        # En-tête avec informations du domaine et client
        story.extend(self._build_header())
        
        # Titre de la facture
        story.append(Paragraph(f"FACTURE N° {self.facture.numero}", self.title_style))
        story.append(Spacer(1, 20))
        
        # Informations de la facture
        story.extend(self._build_facture_info())
        
        # Tableau des lignes
        story.extend(self._build_lines_table())
        
        # Totaux
        story.extend(self._build_totals())
        
        # Mentions légales
        story.extend(self._build_mentions_legales())
        
        # Générer le PDF
        doc.build(story)
        
        if save_to_file:
            self._save_pdf_file(buffer)
        
        buffer.seek(0)
        return buffer
    
    def _build_header(self):
        """Construit l'en-tête avec les informations du domaine et du client"""
        story = []
        
        # Informations du domaine (expéditeur)
        domaine_info = [
            [Paragraph(f"<b>{self.domaine.nom}</b>", self.header_style), ""],
            [Paragraph(f"SIRET: {self.domaine.siret or 'N/A'}", self.normal_style), ""],
            [Paragraph(f"Adresse: {self.domaine.adresse or 'N/A'}", self.normal_style), ""],
            [Paragraph(f"{self.domaine.code_postal or ''} {self.domaine.ville or ''}", self.normal_style), ""]
        ]
        
        # Informations du client (destinataire)
        client_info = [
            ["", Paragraph(f"<b>Facturé à:</b>", self.header_style)],
            ["", Paragraph(f"<b>{self.client.nom}</b>", self.normal_style)],
            ["", Paragraph(f"{self.client.adresse}", self.normal_style)],
            ["", Paragraph(f"{self.client.code_postal} {self.client.ville}", self.normal_style)]
        ]
        
        if self.client.siret:
            client_info.append(["", Paragraph(f"SIRET: {self.client.siret}", self.normal_style)])
        
        # Combiner les deux colonnes
        header_data = []
        max_rows = max(len(domaine_info), len(client_info))
        
        for i in range(max_rows):
            left = domaine_info[i][0] if i < len(domaine_info) else ""
            right = client_info[i][1] if i < len(client_info) else ""
            header_data.append([left, right])
        
        header_table = Table(header_data, colWidths=[8*cm, 8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def _build_facture_info(self):
        """Construit les informations de la facture"""
        story = []
        
        info_data = [
            ["Date d'émission:", self.facture.date_emission.strftime("%d/%m/%Y")],
            ["Date d'échéance:", self.facture.date_echeance.strftime("%d/%m/%Y") if self.facture.date_echeance else "N/A"],
            ["Commande N°:", str(self.commande.id)],
        ]
        
        info_table = Table(info_data, colWidths=[4*cm, 6*cm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def _build_lines_table(self):
        """Construit le tableau des lignes de la facture"""
        story = []
        
        # En-têtes
        headers = ["Désignation", "Qté", "Prix unit. HT", "TVA", "Total HT", "Total TTC"]
        
        # Données
        data = [headers]
        
        for ligne in self.commande.lignes.all():
            data.append([
                ligne.produit.nom,
                str(ligne.quantite),
                f"{ligne.prix_unitaire_ht_eur:.2f} €",
                f"{ligne.tva_pct:.1f}%",
                f"{ligne.total_ht_eur:.2f} €",
                f"{ligne.total_ttc_eur:.2f} €"
            ])
        
        # Créer le tableau
        table = Table(data, colWidths=[6*cm, 1.5*cm, 2.5*cm, 1.5*cm, 2.5*cm, 2.5*cm])
        
        # Style du tableau
        table.setStyle(TableStyle([
            # En-têtes
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Corps du tableau
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),  # Aligner les nombres à droite
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),    # Désignation à gauche
            
            # Bordures
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_totals(self):
        """Construit la section des totaux avec détail TVA"""
        story = []
        
        # Calculs
        total_ht = sum(ligne.total_ht_eur for ligne in self.commande.lignes.all())
        total_ttc = self.facture.total_ttc
        
        # Détail TVA
        tva_details = []
        for taux, details in self.facture.tva.items():
            tva_details.append([
                f"TVA {taux}%",
                f"Base HT: {details['base_ht']:.2f} €",
                f"Montant TVA: {details['montant_tva']:.2f} €"
            ])
        
        # Tableau des totaux
        totals_data = []
        
        # Détail TVA
        for detail in tva_details:
            totals_data.append(["", detail[0], detail[1], detail[2]])
        
        # Ligne de séparation
        totals_data.append(["", "", "", ""])
        
        # Totaux finaux
        totals_data.extend([
            ["", "", "Total HT:", f"{total_ht:.2f} €"],
            ["", "", "Total TVA:", f"{total_ttc - total_ht:.2f} €"],
            ["", "", "TOTAL TTC:", f"{total_ttc:.2f} €"]
        ])
        
        totals_table = Table(totals_data, colWidths=[6*cm, 3*cm, 3*cm, 4*cm])
        totals_table.setStyle(TableStyle([
            # Totaux finaux en gras
            ('FONTNAME', (2, -3), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, -3), (-1, -1), 11),
            
            # Total TTC encore plus visible
            ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, -1), (-1, -1), 12),
            ('BACKGROUND', (2, -1), (-1, -1), colors.lightgrey),
            
            # Alignement
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Bordures pour les totaux
            ('LINEABOVE', (2, -3), (-1, -3), 1, colors.black),
            ('LINEABOVE', (2, -1), (-1, -1), 2, colors.black),
        ]))
        
        story.append(totals_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def _build_mentions_legales(self):
        """Construit les mentions légales obligatoires"""
        story = []
        
        story.append(HRFlowable(width="100%"))
        story.append(Spacer(1, 10))
        
        mentions = [
            "Mentions légales:",
            f"• TVA non applicable, art. 293 B du CGI (si applicable)",
            f"• Paiement à réception de facture",
            f"• Aucun escompte pour paiement anticipé",
            f"• Pénalités de retard : 3 fois le taux d'intérêt légal",
            f"• Indemnité forfaitaire pour frais de recouvrement : 40 €",
            f"• Facture émise le {date.today().strftime('%d/%m/%Y')}"
        ]
        
        for mention in mentions:
            if mention.startswith("Mentions"):
                story.append(Paragraph(f"<b>{mention}</b>", self.normal_style))
            else:
                story.append(Paragraph(mention, self.normal_style))
        
        return story
    
    def _save_pdf_file(self, buffer):
        """Sauvegarde le fichier PDF et met à jour le modèle"""
        # Créer le nom de fichier
        filename = f"factures/{self.facture.numero}.pdf"
        
        # Créer le répertoire si nécessaire
        os.makedirs(os.path.dirname(os.path.join(settings.MEDIA_ROOT, filename)), exist_ok=True)
        
        # Sauvegarder le fichier
        buffer.seek(0)
        file_path = default_storage.save(filename, buffer)
        
        # Mettre à jour le modèle
        self.facture.pdf_path = file_path
        self.facture.save()
        
        return file_path


def generer_pdf_facture(facture_id):
    """
    Fonction utilitaire pour générer le PDF d'une facture
    
    Args:
        facture_id: ID de la facture
        
    Returns:
        Chemin du fichier PDF généré
    """
    try:
        facture = Facture.objects.get(id=facture_id)
        generator = FacturePDFGenerator(facture)
        buffer = generator.generate_pdf(save_to_file=True)
        return facture.pdf_path
    except Facture.DoesNotExist:
        raise ValueError(f"Facture {facture_id} non trouvée")
