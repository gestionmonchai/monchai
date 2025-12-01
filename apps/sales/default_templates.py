"""
Templates de documents par défaut
"""

DEFAULT_TEMPLATES = {
    'quote': {
        'name': 'Devis standard',
        'description': 'Template de devis classique avec tableau des produits',
        'header': '''
<div class="row">
    <div class="col-6">
        <h1 class="wine-gradient">DEVIS</h1>
        <p><strong>N° {{ document.number }}</strong></p>
        <p>Date : {{ document.date|date_format }}</p>
        {% if document.valid_until %}
        <p>Valable jusqu'au : {{ document.valid_until|date_format }}</p>
        {% endif %}
    </div>
    <div class="col-6" style="text-align: right;">
        <h2>{{ organization.name }}</h2>
        <p>{{ organization.address }}<br>
        {{ organization.postal_code }} {{ organization.city }}<br>
        {{ organization.country }}</p>
        {% if organization.phone %}<p>Tél : {{ organization.phone }}</p>{% endif %}
        {% if organization.email %}<p>Email : {{ organization.email }}</p>{% endif %}
        {% if organization.vat_number %}<p>TVA : {{ organization.vat_number }}</p>{% endif %}
    </div>
</div>

{% if customer %}
<div style="margin-top: 30px; padding: 15px; background: #f9f9f9; border-left: 4px solid #d4af37;">
    <strong>Client :</strong><br>
    <strong>{{ customer.legal_name }}</strong><br>
    {{ customer.billing_address }}<br>
    {{ customer.billing_postal_code }} {{ customer.billing_city }}<br>
    {% if customer.vat_number %}TVA : {{ customer.vat_number }}{% endif %}
</div>
{% endif %}
        ''',
        'body': '''
<h3 style="margin-top: 30px;">Détail du devis</h3>

<table>
    <thead>
        <tr>
            <th>Désignation</th>
            <th style="text-align: center; width: 80px;">Qté</th>
            <th style="text-align: right; width: 120px;">Prix unit. HT</th>
            <th style="text-align: right; width: 120px;">Total HT</th>
        </tr>
    </thead>
    <tbody>
        {% for line in lines %}
        <tr>
            <td>{{ line.description }}</td>
            <td style="text-align: center;">{{ line.qty }}</td>
            <td style="text-align: right;">{{ line.unit_price|currency }}</td>
            <td style="text-align: right;">{{ line.total_ht|currency }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="totals">
    <table>
        <tr class="total-ht">
            <td>Total HT</td>
            <td style="text-align: right;">{{ totals.total_ht|currency }}</td>
        </tr>
        <tr>
            <td>TVA</td>
            <td style="text-align: right;">{{ totals.total_tax|currency }}</td>
        </tr>
        <tr class="total-ttc">
            <td>Total TTC</td>
            <td style="text-align: right;">{{ totals.total_ttc|currency }}</td>
        </tr>
    </table>
</div>

<div style="clear: both; margin-top: 30px; padding: 15px; background: #f7e7ce; border: 1px solid #d4af37;">
    <strong>Conditions :</strong><br>
    Devis valable {{ document.valid_until|date_format }}.<br>
    Acompte de 30% à la commande.<br>
    Solde à la livraison.
</div>
        ''',
        'footer': '''
<p style="text-align: center; font-size: 8pt; color: #666;">
    {{ organization.name }} - {{ organization.address }}, {{ organization.postal_code }} {{ organization.city }}<br>
    {% if organization.siret %}SIRET : {{ organization.siret }} - {% endif %}
    {% if organization.vat_number %}TVA : {{ organization.vat_number }}{% endif %}<br>
    {% if organization.website %}{{ organization.website }}{% endif %}
</p>
        ''',
    },
    
    'invoice': {
        'name': 'Facture standard',
        'description': 'Template de facture avec mentions légales',
        'header': '''
<div class="row">
    <div class="col-6">
        <h1 class="wine-gradient">FACTURE</h1>
        <p><strong>N° {{ document.number }}</strong></p>
        <p>Date d'émission : {{ document.date_issue|date_format }}</p>
        {% if document.due_date %}
        <p>Date d'échéance : {{ document.due_date|date_format }}</p>
        {% endif %}
    </div>
    <div class="col-6" style="text-align: right;">
        <h2>{{ organization.name }}</h2>
        <p>{{ organization.address }}<br>
        {{ organization.postal_code }} {{ organization.city }}<br>
        {{ organization.country }}</p>
        {% if organization.phone %}<p>Tél : {{ organization.phone }}</p>{% endif %}
        {% if organization.email %}<p>Email : {{ organization.email }}</p>{% endif %}
    </div>
</div>

{% if customer %}
<div style="margin-top: 30px; padding: 15px; background: #f9f9f9; border-left: 4px solid #8B1538;">
    <strong>Facturé à :</strong><br>
    <strong>{{ customer.legal_name }}</strong><br>
    {{ customer.billing_address }}<br>
    {{ customer.billing_postal_code }} {{ customer.billing_city }}<br>
    {% if customer.vat_number %}N° TVA : {{ customer.vat_number }}{% endif %}
</div>
{% endif %}
        ''',
        'body': '''
<h3 style="margin-top: 30px;">Détail de la facture</h3>

<table>
    <thead>
        <tr>
            <th>Désignation</th>
            <th style="text-align: center; width: 80px;">Qté</th>
            <th style="text-align: right; width: 120px;">Prix unit. HT</th>
            <th style="text-align: right; width: 120px;">Total HT</th>
        </tr>
    </thead>
    <tbody>
        {% for line in lines %}
        <tr>
            <td>{{ line.description }}</td>
            <td style="text-align: center;">{{ line.qty }}</td>
            <td style="text-align: right;">{{ line.unit_price|currency }}</td>
            <td style="text-align: right;">{{ line.total_ht|currency }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="totals">
    <table>
        <tr class="total-ht">
            <td>Total HT</td>
            <td style="text-align: right;">{{ totals.total_ht|currency }}</td>
        </tr>
        <tr>
            <td>TVA (20%)</td>
            <td style="text-align: right;">{{ totals.total_tax|currency }}</td>
        </tr>
        <tr class="total-ttc">
            <td><strong>TOTAL TTC</strong></td>
            <td style="text-align: right;"><strong>{{ totals.total_ttc|currency }}</strong></td>
        </tr>
    </table>
</div>

<div style="clear: both; margin-top: 30px; padding: 15px; background: #fff3cd; border: 1px solid #856404;">
    <strong>Conditions de paiement :</strong><br>
    Paiement à {{ document.due_date|date_format }}<br>
    En cas de retard de paiement, une pénalité de 3 fois le taux d'intérêt légal sera appliquée.<br>
    Indemnité forfaitaire pour frais de recouvrement : 40 €.
</div>
        ''',
        'footer': '''
<p style="text-align: center; font-size: 7pt; color: #666;">
    <strong>{{ organization.name }}</strong> - {{ organization.address }}, {{ organization.postal_code }} {{ organization.city }}<br>
    {% if organization.siret %}SIRET : {{ organization.siret }} - {% endif %}
    {% if organization.vat_number %}N° TVA intracommunautaire : {{ organization.vat_number }}{% endif %}<br>
    {% if organization.website %}{{ organization.website }} - {% endif %}
    {% if organization.email %}{{ organization.email }}{% endif %}<br>
    <em>TVA non applicable - Article 293 B du CGI</em> (si applicable)
</p>
        ''',
    },
    
    'order': {
        'name': 'Commande standard',
        'description': 'Template de bon de commande',
        'header': '''
<div class="row">
    <div class="col-6">
        <h1 class="wine-gradient">BON DE COMMANDE</h1>
        <p><strong>N° {{ document.number }}</strong></p>
        <p>Date : {{ document.date|date_format }}</p>
    </div>
    <div class="col-6" style="text-align: right;">
        <h2>{{ organization.name }}</h2>
        <p>{{ organization.address }}<br>
        {{ organization.postal_code }} {{ organization.city }}</p>
    </div>
</div>

{% if customer %}
<div style="margin-top: 30px; padding: 15px; background: #e7f3ff; border-left: 4px solid #004085;">
    <strong>Client :</strong><br>
    <strong>{{ customer.legal_name }}</strong><br>
    {{ customer.billing_address }}<br>
    {{ customer.billing_postal_code }} {{ customer.billing_city }}
</div>
{% endif %}
        ''',
        'body': '''
<h3 style="margin-top: 30px;">Détail de la commande</h3>

<table>
    <thead>
        <tr>
            <th>Produit</th>
            <th style="text-align: center; width: 100px;">Quantité</th>
            <th style="text-align: right; width: 120px;">Prix unit.</th>
            <th style="text-align: right; width: 120px;">Total</th>
        </tr>
    </thead>
    <tbody>
        {% for line in lines %}
        <tr>
            <td>{{ line.description }}</td>
            <td style="text-align: center;">{{ line.qty }}</td>
            <td style="text-align: right;">{{ line.unit_price|currency }}</td>
            <td style="text-align: right;">{{ line.total_ht|currency }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="totals">
    <table>
        <tr class="total-ttc">
            <td><strong>TOTAL</strong></td>
            <td style="text-align: right;"><strong>{{ totals.total_ttc|currency }}</strong></td>
        </tr>
    </table>
</div>
        ''',
        'footer': '''
<p style="text-align: center; font-size: 8pt;">
    {{ organization.name }} - {{ organization.phone }} - {{ organization.email }}
</p>
        ''',
    },
    
    'delivery': {
        'name': 'Bon de livraison standard',
        'description': 'Template de bon de livraison',
        'header': '''
<div class="row">
    <div class="col-6">
        <h1 class="wine-gradient">BON DE LIVRAISON</h1>
        <p><strong>N° {{ document.number }}</strong></p>
        <p>Date : {{ document.date|date_format }}</p>
    </div>
    <div class="col-6" style="text-align: right;">
        <h2>{{ organization.name }}</h2>
        <p>{{ organization.address }}<br>
        {{ organization.postal_code }} {{ organization.city }}</p>
    </div>
</div>

{% if customer %}
<div class="row" style="margin-top: 30px;">
    <div class="col-6" style="padding: 15px; background: #f9f9f9; border: 1px solid #ddd;">
        <strong>Livré à :</strong><br>
        <strong>{{ customer.legal_name }}</strong><br>
        {{ customer.billing_address }}<br>
        {{ customer.billing_postal_code }} {{ customer.billing_city }}
    </div>
</div>
{% endif %}
        ''',
        'body': '''
<h3 style="margin-top: 30px;">Articles livrés</h3>

<table>
    <thead>
        <tr>
            <th>Désignation</th>
            <th style="text-align: center; width: 150px;">Quantité livrée</th>
        </tr>
    </thead>
    <tbody>
        {% for line in lines %}
        <tr>
            <td>{{ line.description }}</td>
            <td style="text-align: center; font-weight: bold;">{{ line.qty }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div style="margin-top: 50px; border: 1px solid #333; padding: 20px;">
    <p><strong>Signature du destinataire :</strong></p>
    <p style="margin-top: 10px;">Date et signature (précédée de "Bon pour accord") :</p>
    <div style="height: 80px;"></div>
</div>
        ''',
        'footer': '''
<p style="text-align: center; font-size: 8pt; color: #666;">
    Document non contractuel - Ne constitue pas une facture
</p>
        ''',
    },
}
