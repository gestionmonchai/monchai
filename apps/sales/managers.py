"""
Gestionnaires métier pour les ventes et pricing
DB Roadmap 03 - Ventes, Clients & Pricing
"""

from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Optional, List, Tuple

from apps.stock.models import StockManager


class PricingManager:
    """
    Gestionnaire pour la résolution des prix
    Règles de pricing selon la roadmap
    """
    
    @staticmethod
    def resolve_price(customer, sku, qty=1, date=None):
        """
        Résout le prix d'un SKU pour un client donné
        
        Ordre de priorité:
        1. Grilles tarifaires du client (par priorité)
        2. Grille tarifaire par défaut de l'organisation
        3. Erreur si politique stricte
        
        Args:
            customer: Instance Customer
            sku: Instance SKU
            qty: Quantité demandée
            date: Date de référence (défaut: aujourd'hui)
        
        Returns:
            dict: {
                'unit_price': Decimal,
                'discount_pct': Decimal,
                'effective_price': Decimal,
                'source': str  # 'customer_list', 'default_list', 'not_found'
            }
        """
        from .models import CustomerPriceList, PriceItem, PriceList
        
        if date is None:
            date = timezone.now().date()
        
        # 1. Chercher dans les grilles du client
        customer_price_lists = CustomerPriceList.objects.filter(
            customer=customer,
            price_list__is_active=True
        ).select_related('price_list').order_by('priority')
        
        for cpl in customer_price_lists:
            price_list = cpl.price_list
            if not price_list.is_valid_at(date):
                continue
            
            price_info = PricingManager._find_price_in_list(price_list, sku, qty)
            if price_info:
                price_info['source'] = 'customer_list'
                price_info['price_list'] = price_list.name
                return price_info
        
        # 2. Chercher dans la grille par défaut de l'organisation
        default_price_list = PriceList.objects.filter(
            organization=customer.organization,
            name__icontains='défaut',
            is_active=True
        ).first()
        
        if not default_price_list:
            # Prendre la première grille active
            default_price_list = PriceList.objects.filter(
                organization=customer.organization,
                is_active=True
            ).order_by('-valid_from').first()
        
        if default_price_list and default_price_list.is_valid_at(date):
            price_info = PricingManager._find_price_in_list(default_price_list, sku, qty)
            if price_info:
                price_info['source'] = 'default_list'
                price_info['price_list'] = default_price_list.name
                return price_info
        
        # 3. Prix non trouvé
        return {
            'unit_price': None,
            'discount_pct': Decimal('0'),
            'effective_price': None,
            'source': 'not_found',
            'price_list': None
        }
    
    @staticmethod
    def _find_price_in_list(price_list, sku, qty):
        """
        Trouve le prix dans une grille tarifaire donnée
        Gère les seuils de quantité (min_qty)
        """
        from .models import PriceItem
        
        # Chercher tous les prix pour ce SKU dans cette grille
        price_items = PriceItem.objects.filter(
            price_list=price_list,
            sku=sku
        ).order_by('-min_qty')  # Du plus grand seuil au plus petit
        
        if not price_items.exists():
            return None
        
        # Trouver le prix applicable selon la quantité
        for item in price_items:
            if item.min_qty is None or qty >= item.min_qty:
                return {
                    'unit_price': item.unit_price,
                    'discount_pct': item.discount_pct,
                    'effective_price': item.effective_price,
                }
        
        # Aucun seuil atteint, prendre le prix sans seuil s'il existe
        no_threshold_item = price_items.filter(min_qty__isnull=True).first()
        if no_threshold_item:
            return {
                'unit_price': no_threshold_item.unit_price,
                'discount_pct': no_threshold_item.discount_pct,
                'effective_price': no_threshold_item.effective_price,
            }
        
        return None
    
    @staticmethod
    def get_tax_code(customer, sku):
        """
        Détermine le code taxe applicable selon le client et le produit
        
        Règles TVA:
        - Particulier FR: TVA 20%
        - Pro FR: TVA 20% 
        - Pro UE avec TVA: TVA 0% (autoliquidation)
        - Pro UE sans TVA: TVA 20%
        - Hors UE: TVA 0%
        """
        from .models import TaxCode
        
        organization = customer.organization
        
        # Codes taxes par défaut
        try:
            if customer.billing_country == 'FR':
                # France: TVA 20%
                return TaxCode.objects.get(
                    organization=organization,
                    code='TVA20',
                    is_active=True
                )
            elif customer.billing_country in ['DE', 'ES', 'IT', 'BE', 'NL', 'PT']:
                # UE: dépend du type de client
                if customer.type == 'pro' and customer.vat_number:
                    # Pro avec TVA: autoliquidation (0%)
                    return TaxCode.objects.get(
                        organization=organization,
                        code='TVA0',
                        is_active=True
                    )
                else:
                    # Particulier ou pro sans TVA: TVA française
                    return TaxCode.objects.get(
                        organization=organization,
                        code='TVA20',
                        is_active=True
                    )
            else:
                # Hors UE: pas de TVA
                return TaxCode.objects.get(
                    organization=organization,
                    code='TVA0',
                    is_active=True
                )
        except TaxCode.DoesNotExist:
            # Fallback: TVA 20%
            return TaxCode.objects.filter(
                organization=organization,
                is_active=True
            ).first()


class SalesManager:
    """
    Gestionnaire pour les opérations de vente
    Gestion des devis, commandes et réservations stock
    """
    
    @staticmethod
    @transaction.atomic
    def create_quote_from_cart(customer, cart_items, valid_days=30):
        """
        Crée un devis à partir d'un panier
        
        Args:
            customer: Instance Customer
            cart_items: List[dict] avec 'sku', 'qty'
            valid_days: Nombre de jours de validité
        
        Returns:
            Quote: Instance du devis créé
        """
        from .models import Quote, QuoteLine
        
        # Créer le devis
        valid_until = timezone.now().date() + timezone.timedelta(days=valid_days)
        quote = Quote.objects.create(
            organization=customer.organization,
            customer=customer,
            currency=customer.currency,
            valid_until=valid_until
        )
        
        # Créer les lignes
        for item in cart_items:
            sku = item['sku']
            qty = item['qty']
            
            # Résoudre le prix
            price_info = PricingManager.resolve_price(customer, sku, qty)
            if price_info['unit_price'] is None:
                raise ValidationError(f"Prix non trouvé pour {sku.label}")
            
            # Déterminer le code taxe
            tax_code = PricingManager.get_tax_code(customer, sku)
            
            # Créer la ligne
            QuoteLine.objects.create(
                organization=customer.organization,
                quote=quote,
                sku=sku,
                description=sku.label,
                qty=qty,
                unit_price=price_info['unit_price'],
                discount_pct=price_info['discount_pct'],
                tax_code=tax_code
            )
        
        # Recalculer les totaux
        quote.calculate_totals()
        quote.save()
        
        return quote
    
    @staticmethod
    @transaction.atomic
    def convert_quote_to_order(quote):
        """
        Convertit un devis en commande
        
        Args:
            quote: Instance Quote à convertir
        
        Returns:
            Order: Instance de la commande créée
        """
        from .models import Order, OrderLine
        
        if quote.status != 'accepted':
            raise ValidationError("Seuls les devis acceptés peuvent être convertis en commande")
        
        # Créer la commande
        order = Order.objects.create(
            organization=quote.organization,
            customer=quote.customer,
            quote=quote,
            currency=quote.currency,
            total_ht=quote.total_ht,
            total_tax=quote.total_tax,
            total_ttc=quote.total_ttc
        )
        
        # Copier les lignes
        for quote_line in quote.lines.all():
            OrderLine.objects.create(
                organization=quote.organization,
                order=order,
                sku=quote_line.sku,
                description=quote_line.description,
                qty=quote_line.qty,
                unit_price=quote_line.unit_price,
                discount_pct=quote_line.discount_pct,
                tax_code=quote_line.tax_code,
                total_ht=quote_line.total_ht,
                total_tax=quote_line.total_tax,
                total_ttc=quote_line.total_ttc
            )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def confirm_order(order, warehouse=None):
        """
        Confirme une commande et crée les réservations de stock
        
        Args:
            order: Instance Order à confirmer
            warehouse: Entrepôt par défaut (optionnel)
        
        Returns:
            List[StockReservation]: Réservations créées
        """
        from .models import StockReservation
        from apps.stock.models import StockSKUBalance, Warehouse
        
        if order.status != 'draft':
            raise ValidationError("Seules les commandes en brouillon peuvent être confirmées")
        
        # Entrepôt par défaut si non spécifié
        if warehouse is None:
            warehouse = Warehouse.objects.filter(
                organization=order.organization
            ).first()
            
            if not warehouse:
                raise ValidationError("Aucun entrepôt disponible pour cette organisation")
        
        reservations = []
        
        # Vérifier et réserver le stock pour chaque ligne
        for line in order.lines.all():
            # Vérifier le stock disponible
            try:
                balance = StockSKUBalance.objects.get(
                    organization=order.organization,
                    sku=line.sku,
                    warehouse=warehouse
                )
                
                if balance.qty_units < line.qty:
                    raise ValidationError(
                        f"Stock insuffisant pour {line.sku.label}: "
                        f"demandé {line.qty}, disponible {balance.qty_units}"
                    )
            except StockSKUBalance.DoesNotExist:
                raise ValidationError(f"Aucun stock disponible pour {line.sku.label}")
            
            # Créer ou mettre à jour la réservation
            reservation, created = StockReservation.objects.get_or_create(
                organization=order.organization,
                order=order,
                sku=line.sku,
                warehouse=warehouse,
                defaults={'qty_units': line.qty}
            )
            
            if not created:
                # Consolider les réservations existantes
                reservation.qty_units += line.qty
                reservation.save()
            
            reservations.append(reservation)
        
        # Confirmer la commande
        order.status = 'confirmed'
        order.save()
        
        return reservations
    
    @staticmethod
    @transaction.atomic
    def fulfill_order(order, user):
        """
        Expédie une commande et effectue les mouvements de stock
        
        Args:
            order: Instance Order à expédier
            user: Utilisateur effectuant l'opération
        
        Returns:
            List: Mouvements de stock créés
        """
        if order.status != 'confirmed':
            raise ValidationError("Seules les commandes confirmées peuvent être expédiées")
        
        stock_moves = []
        
        # Effectuer les sorties de stock
        for reservation in order.reservations.all():
            # Mouvement de sortie
            move = StockManager.move_sku(
                sku=reservation.sku,
                src_warehouse=reservation.warehouse,
                dst_warehouse=None,  # Sortie
                qty_units=reservation.qty_units,
                move_type='sortie',
                ref_type='order',
                ref_id=str(order.id),
                user=user,
                notes=f"Expédition commande {order.id.hex[:8]}"
            )
            stock_moves.append(move)
        
        # Marquer la commande comme expédiée
        order.status = 'fulfilled'
        order.save()
        
        return stock_moves
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order):
        """
        Annule une commande et libère les réservations
        
        Args:
            order: Instance Order à annuler
        """
        if order.status == 'fulfilled':
            raise ValidationError("Une commande expédiée ne peut pas être annulée")
        
        # Supprimer les réservations
        order.reservations.all().delete()
        
        # Marquer comme annulée
        order.status = 'cancelled'
        order.save()
