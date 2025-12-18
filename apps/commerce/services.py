from django.db import transaction, models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal

from .models import CommercialDocument, CommercialLine
from apps.produits.models_catalog import SKU, InventoryItem, StockMovement

class DocumentService:
    @staticmethod
    @transaction.atomic
    def transform_document(source_doc, target_type, user=None):
        """
        Transform a document into another type (e.g. Quote -> Order).
        """
        # Validations
        if target_type == CommercialDocument.TYPE_ORDER:
            if source_doc.type != CommercialDocument.TYPE_QUOTE:
                raise ValidationError("Seul un devis peut être transformé en commande.")
        elif target_type == CommercialDocument.TYPE_DELIVERY:
            if source_doc.type != CommercialDocument.TYPE_ORDER:
                raise ValidationError("Seule une commande peut être transformée en livraison.")
        elif target_type == CommercialDocument.TYPE_INVOICE:
            if source_doc.type not in [CommercialDocument.TYPE_ORDER, CommercialDocument.TYPE_DELIVERY]:
                raise ValidationError("Une facture doit provenir d'une commande ou d'une livraison.")

        # Create new document
        new_doc = CommercialDocument(
            organization=source_doc.organization,
            type=target_type,
            side=source_doc.side,
            status=CommercialDocument.STATUS_DRAFT,
            client=source_doc.client,
            parent=source_doc,
            sale_mode=source_doc.sale_mode,
            currency=source_doc.currency,
            notes=source_doc.notes,
            internal_notes=source_doc.internal_notes,
            delivery_date_expected=source_doc.delivery_date_expected,
            shipping_address=source_doc.shipping_address,
            created_by=user
        )
        
        # Generate temporary number
        prefix = target_type[:2].upper()
        new_doc.number = f"DRAFT-{prefix}-{timezone.now().timestamp()}"
        new_doc.save()

        # Copy lines
        for line in source_doc.lines.all():
            CommercialLine.objects.create(
                document=new_doc,
                sku=line.sku,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_pct=line.discount_pct,
                tax_rate=line.tax_rate,
                lot_number=line.lot_number,
                sort_order=line.sort_order
            )
            
        # Update source document status if needed
        if source_doc.type == CommercialDocument.TYPE_QUOTE and target_type == CommercialDocument.TYPE_ORDER:
            source_doc.status = CommercialDocument.STATUS_VALIDATED
            source_doc.save()
            
        # Recalculate totals
        new_doc.total_ht = source_doc.total_ht
        new_doc.total_tax = source_doc.total_tax
        new_doc.total_ttc = source_doc.total_ttc
        new_doc.save()
        
        return new_doc

    @staticmethod
    @transaction.atomic
    def execute_delivery(doc, user=None):
        """
        Validate a Delivery document and update stock.
        """
        if doc.type != CommercialDocument.TYPE_DELIVERY:
            raise ValidationError("Seul un Bon de Livraison/Réception peut être exécuté.")
            
        if doc.status == CommercialDocument.STATUS_EXECUTED:
            return # Already done
            
        # Determine stock movement direction
        # Sale -> Delivery -> Stock Decrease (OUT)
        # Purchase -> Delivery (Reception) -> Stock Increase (IN)
        is_outgoing = (doc.side == CommercialDocument.SIDE_SALE)
        movement_type = 'out' if is_outgoing else 'in'
        
        for line in doc.lines.all():
            if line.sku and line.sku.product.stockable: # Assuming Product has stockable field
                # Find or create inventory item (simplified for now, assumes 1 warehouse per org or default)
                inventory_item, created = InventoryItem.objects.get_or_create(
                    organization=doc.organization,
                    sku=line.sku,
                    defaults={'qty': 0}
                )
                
                qty_change = Decimal(line.quantity)
                if is_outgoing:
                    inventory_item.qty = models.F('qty') - qty_change
                else:
                    inventory_item.qty = models.F('qty') + qty_change
                
                inventory_item.save()
                
                # Log movement
                StockMovement.objects.create(
                    organization=doc.organization,
                    sku=line.sku,
                    quantity=qty_change,
                    movement_type=movement_type,
                    source_doc_type=doc.type,
                    source_doc_id=doc.id,
                    description=f"{doc.get_type_display()} {doc.number}"
                )
        
        doc.status = CommercialDocument.STATUS_EXECUTED
        doc.save()
        
        # Update parent status
        if doc.parent:
            # Check if all parent lines are fulfilled? For now simpler logic:
            if doc.parent.type == CommercialDocument.TYPE_ORDER:
                doc.parent.status = CommercialDocument.STATUS_EXECUTED # Or fulfilled
                doc.parent.save()

    @staticmethod
    @transaction.atomic
    def validate_order(doc, user=None):
        """
        Validate an order (moves from Draft/Sent to Validated).
        Could reserve stock here if needed.
        """
        if doc.type != CommercialDocument.TYPE_ORDER:
            raise ValidationError("Document n'est pas une commande.")
            
        doc.status = CommercialDocument.STATUS_VALIDATED
        doc.save()
