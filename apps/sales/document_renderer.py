"""
Moteur de rendu pour les documents
Gestion du remplacement des variables et génération PDF
"""

from jinja2 import Template, Environment, select_autoescape
from decimal import Decimal
from datetime import date, datetime
from django.utils.formats import date_format, number_format
from django.utils.html import escape
import logging

logger = logging.getLogger(__name__)


class DocumentRenderer:
    """
    Moteur de rendu pour les templates de documents
    Remplace les variables et génère le HTML final
    """
    
    def __init__(self, template_obj):
        """
        :param template_obj: Instance de DocumentTemplate
        """
        self.template = template_obj
        self.env = Environment(
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Filtres personnalisés
        self.env.filters['currency'] = self.filter_currency
        self.env.filters['date_format'] = self.filter_date
        self.env.filters['percentage'] = self.filter_percentage
    
    @staticmethod
    def filter_currency(value, currency='€'):
        """Formatte un montant en devise"""
        if value is None:
            return f"0,00 {currency}"
        
        if isinstance(value, (int, float, Decimal)):
            # Format français : espace pour milliers, virgule pour décimales
            return f"{value:,.2f}".replace(',', ' ').replace('.', ',') + f" {currency}"
        return str(value)
    
    @staticmethod
    def filter_date(value, format_string='SHORT_DATE_FORMAT'):
        """Formatte une date"""
        if value is None:
            return ''
        
        if isinstance(value, (date, datetime)):
            return date_format(value, format_string)
        return str(value)
    
    @staticmethod
    def filter_percentage(value):
        """Formatte un pourcentage"""
        if value is None:
            return '0%'
        
        if isinstance(value, (int, float, Decimal)):
            return f"{value}%"
        return str(value)
    
    def prepare_context(self, document_obj, organization_obj, customer_obj=None):
        """
        Prépare le contexte de variables pour le rendu
        
        :param document_obj: Quote, Order, Invoice, etc.
        :param organization_obj: Organization
        :param customer_obj: Customer (optionnel, peut être dans document_obj)
        :return: dict avec toutes les variables
        """
        # Customer
        if customer_obj is None and hasattr(document_obj, 'customer'):
            customer_obj = document_obj.customer
        
        context = {
            'organization': {
                'name': organization_obj.name,
                'address': getattr(organization_obj, 'address', ''),
                'postal_code': getattr(organization_obj, 'postal_code', ''),
                'city': getattr(organization_obj, 'city', ''),
                'country': getattr(organization_obj, 'country', 'France'),
                'phone': getattr(organization_obj, 'phone', ''),
                'email': getattr(organization_obj, 'email', ''),
                'website': getattr(organization_obj, 'website', ''),
                'vat_number': getattr(organization_obj, 'vat_number', ''),
                'siret': getattr(organization_obj, 'siret', ''),
            },
            'document': {
                'number': getattr(document_obj, 'number', '') or str(document_obj.id.hex[:8]),
                'date': date.today(),
                'currency': getattr(document_obj, 'currency', 'EUR'),
                'status': document_obj.get_status_display() if hasattr(document_obj, 'get_status_display') else '',
            },
            'totals': {
                'total_ht': getattr(document_obj, 'total_ht', Decimal('0')),
                'total_tax': getattr(document_obj, 'total_tax', Decimal('0')),
                'total_ttc': getattr(document_obj, 'total_ttc', Decimal('0')),
            },
        }
        
        # Customer
        if customer_obj:
            context['customer'] = {
                'legal_name': customer_obj.legal_name,
                'billing_address': getattr(customer_obj, 'billing_address', ''),
                'billing_postal_code': getattr(customer_obj, 'billing_postal_code', ''),
                'billing_city': getattr(customer_obj, 'billing_city', ''),
                'billing_country': getattr(customer_obj, 'billing_country', ''),
                'vat_number': getattr(customer_obj, 'vat_number', ''),
            }
        else:
            context['customer'] = None
        
        # Dates spécifiques selon le type de document
        if hasattr(document_obj, 'date_issue'):
            context['document']['date_issue'] = document_obj.date_issue
        
        if hasattr(document_obj, 'valid_until'):
            context['document']['valid_until'] = document_obj.valid_until
        
        if hasattr(document_obj, 'due_date'):
            context['document']['due_date'] = document_obj.due_date
        
        # Lignes du document
        lines = []
        if hasattr(document_obj, 'lines'):
            for line in document_obj.lines.all():
                line_data = {
                    'description': line.description,
                    'qty': line.qty,
                    'unit_price': line.unit_price,
                    'total_ht': getattr(line, 'total_ht', line.qty * line.unit_price),
                }
                
                # Remise si présente
                if hasattr(line, 'discount_pct') and line.discount_pct:
                    line_data['discount_pct'] = line.discount_pct
                
                # Taxe si présente
                if hasattr(line, 'tax_rate'):
                    line_data['tax_rate'] = line.tax_rate
                
                # SKU si présent
                if hasattr(line, 'sku') and line.sku:
                    line_data['sku_code'] = line.sku.code
                
                lines.append(line_data)
        
        context['lines'] = lines
        
        return context
    
    def render_html(self, document_obj, organization_obj, customer_obj=None):
        """
        Rend le HTML complet du document
        
        :return: str HTML complet
        """
        context = self.prepare_context(document_obj, organization_obj, customer_obj)
        
        # Rendre chaque partie
        header_html = self._render_part(self.template.html_header, context)
        body_html = self._render_part(self.template.html_body, context)
        footer_html = self._render_part(self.template.html_footer, context)
        
        # Assembler le document complet avec CSS
        full_html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.template.get_document_type_display()} - {context['document']['number']}</title>
    <style>
        /* Reset et styles de base */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 10pt;
            line-height: 1.5;
            color: #333;
        }}
        
        .page {{
            width: 210mm;
            min-height: 297mm;
            padding: {self.template.margin_top}mm {self.template.margin_right}mm {self.template.margin_bottom}mm {self.template.margin_left}mm;
            margin: 0 auto;
            background: white;
        }}
        
        /* En-tête */
        .header {{
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #8B1538;
        }}
        
        .logo {{
            max-width: 200px;
            margin-bottom: 10px;
        }}
        
        /* Corps */
        .body {{
            margin-bottom: 30px;
        }}
        
        /* Tableaux */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        table th {{
            background: #8B1538;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
        }}
        
        table td {{
            padding: 10px 8px;
            border-bottom: 1px solid #ddd;
        }}
        
        table tr:hover {{
            background: #f9f9f9;
        }}
        
        /* Totaux */
        .totals {{
            margin-top: 30px;
            float: right;
            width: 300px;
        }}
        
        .totals table {{
            margin: 0;
        }}
        
        .totals .total-ht td {{
            font-weight: bold;
        }}
        
        .totals .total-ttc td {{
            background: #8B153820;
            font-weight: bold;
            font-size: 12pt;
            border-top: 2px solid #8B1538;
        }}
        
        /* Pied de page */
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 8pt;
            color: #666;
            clear: both;
        }}
        
        /* Grille deux colonnes */
        .row {{
            display: flex;
            margin-bottom: 20px;
        }}
        
        .col-6 {{
            flex: 0 0 50%;
            padding: 0 10px;
        }}
        
        /* Styles viticoles */
        .wine-gradient {{
            background: linear-gradient(135deg, #8B1538 0%, #722f37 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .gold-text {{
            color: #d4af37;
        }}
        
        /* Print styles */
        @media print {{
            .page {{
                margin: 0;
                border: none;
                box-shadow: none;
            }}
        }}
        
        /* Styles personnalisés */
        {self.template.custom_css}
    </style>
</head>
<body>
    <div class="page">
        <div class="header">
            {header_html}
        </div>
        
        <div class="body">
            {body_html}
        </div>
        
        <div class="footer">
            {footer_html}
        </div>
    </div>
</body>
</html>
        """
        
        return full_html
    
    def _render_part(self, template_string, context):
        """
        Rend une partie du template (header, body ou footer)
        """
        if not template_string:
            return ''
        
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Erreur de rendu template: {e}")
            return f'<div style="color: red;">Erreur de rendu: {escape(str(e))}</div>'
    
    def generate_pdf(self, document_obj, organization_obj, customer_obj=None):
        """
        Génère un PDF à partir du document
        
        :return: bytes du PDF
        """
        try:
            from weasyprint import HTML, CSS
            
            html_content = self.render_html(document_obj, organization_obj, customer_obj)
            
            # Configuration PDF
            pdf_bytes = HTML(string=html_content).write_pdf()
            
            return pdf_bytes
        
        except ImportError:
            logger.error("WeasyPrint n'est pas installé. Installez-le avec: pip install weasyprint")
            raise
        except Exception as e:
            logger.error(f"Erreur génération PDF: {e}")
            raise


class DocumentHelper:
    """
    Helpers pour la gestion des documents
    """
    
    @staticmethod
    def get_default_template(organization, document_type):
        """
        Récupère le template par défaut pour un type de document
        """
        from apps.sales.models_documents import DocumentTemplate
        
        try:
            return DocumentTemplate.objects.get(
                organization=organization,
                document_type=document_type,
                is_default=True,
                is_active=True
            )
        except DocumentTemplate.DoesNotExist:
            # Créer un template par défaut si aucun n'existe
            return DocumentHelper.create_default_template(organization, document_type)
    
    @staticmethod
    def create_default_template(organization, document_type):
        """
        Crée un template par défaut pour un type de document
        """
        from apps.sales.models_documents import DocumentTemplate
        from apps.sales.default_templates import DEFAULT_TEMPLATES
        
        template_config = DEFAULT_TEMPLATES.get(document_type, DEFAULT_TEMPLATES['quote'])
        
        template = DocumentTemplate.objects.create(
            organization=organization,
            name=f"{template_config['name']} (défaut)",
            document_type=document_type,
            description=template_config['description'],
            is_default=True,
            is_active=True,
            html_header=template_config['header'],
            html_body=template_config['body'],
            html_footer=template_config['footer'],
            custom_css=template_config.get('css', ''),
        )
        
        return template
