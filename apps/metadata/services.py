"""
Services pour la gestion des métadonnées
Roadmap Meta Base de Données - Phase P1
"""

from typing import Dict, List, Optional
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.db import models
from .models import MetaEntity, MetaAttribute, MetaRelation


class MetadataService:
    """Service pour gérer les métadonnées des entités"""
    
    def __init__(self):
        self.registered_entities = {}
    
    def register_entity(
        self, 
        model_class, 
        name: str, 
        code: str, 
        domain: str,
        is_searchable: bool = True,
        is_listable: bool = True,
        description: str = ""
    ):
        """
        Enregistre une entité dans le métamodèle
        
        Args:
            model_class: Classe du modèle Django
            name: Nom humain
            code: Code technique
            domain: Domaine métier
            is_searchable: Inclure dans recherche globale
            is_listable: Affichable dans listes
            description: Description
        """
        content_type = ContentType.objects.get_for_model(model_class)
        
        entity, created = MetaEntity.objects.get_or_create(
            content_type=content_type,
            defaults={
                'name': name,
                'code': code,
                'domain': domain,
                'is_searchable': is_searchable,
                'is_listable': is_listable,
                'description': description,
            }
        )
        
        if not created:
            # Mettre à jour si nécessaire
            entity.name = name
            entity.code = code
            entity.domain = domain
            entity.is_searchable = is_searchable
            entity.is_listable = is_listable
            entity.description = description
            entity.save()
        
        self.registered_entities[code] = entity
        return entity
    
    def register_attribute(
        self,
        entity_code: str,
        field_name: str,
        name: str,
        data_type: str,
        is_facet: bool = False,
        is_sortable: bool = False,
        is_fulltext: bool = False,
        is_required: bool = False,
        unit: str = "",
        help_text: str = "",
        display_order: int = 0
    ):
        """
        Enregistre un attribut d'entité
        
        Args:
            entity_code: Code de l'entité
            field_name: Nom du champ en base
            name: Nom humain
            data_type: Type de données
            is_facet: Utilisable comme facette
            is_sortable: Utilisable pour tri
            is_fulltext: Inclure dans recherche textuelle
            is_required: Champ obligatoire
            unit: Unité
            help_text: Aide contextuelle
            display_order: Ordre d'affichage
        """
        if entity_code not in self.registered_entities:
            raise ValueError(f"Entité non enregistrée: {entity_code}")
        
        entity = self.registered_entities[entity_code]
        
        attribute, created = MetaAttribute.objects.get_or_create(
            entity=entity,
            code=field_name,
            defaults={
                'name': name,
                'data_type': data_type,
                'is_facet': is_facet,
                'is_sortable': is_sortable,
                'is_fulltext': is_fulltext,
                'is_required': is_required,
                'unit': unit,
                'help_text': help_text,
                'display_order': display_order,
            }
        )
        
        if not created:
            # Mettre à jour
            attribute.name = name
            attribute.data_type = data_type
            attribute.is_facet = is_facet
            attribute.is_sortable = is_sortable
            attribute.is_fulltext = is_fulltext
            attribute.is_required = is_required
            attribute.unit = unit
            attribute.help_text = help_text
            attribute.display_order = display_order
            attribute.save()
        
        return attribute
    
    def auto_discover_entities(self):
        """
        Découvre automatiquement les entités existantes
        """
        # Modèles à enregistrer automatiquement
        entities_config = {
            'accounts.Organization': {
                'name': 'Organisation',
                'code': 'organization',
                'domain': 'system',
                'description': 'Exploitation viticole ou organisation',
                'attributes': {
                    'name': {'name': 'Nom', 'data_type': 'text', 'is_fulltext': True, 'is_sortable': True},
                    'siret': {'name': 'SIRET', 'data_type': 'text', 'is_facet': True},
                    'email': {'name': 'Email', 'data_type': 'text', 'is_fulltext': True},
                    'phone': {'name': 'Téléphone', 'data_type': 'text'},
                    'address': {'name': 'Adresse', 'data_type': 'text', 'is_fulltext': True},
                    'city': {'name': 'Ville', 'data_type': 'text', 'is_facet': True, 'is_sortable': True},
                    'postal_code': {'name': 'Code postal', 'data_type': 'text', 'is_facet': True},
                    'country': {'name': 'Pays', 'data_type': 'text', 'is_facet': True},
                }
            },
            'referentiels.Cuvee': {
                'name': 'Cuvée',
                'code': 'cuvee',
                'domain': 'viticulture',
                'description': 'Cuvée de vin avec ses caractéristiques',
                'attributes': {
                    'nom': {'name': 'Nom', 'data_type': 'text', 'is_fulltext': True, 'is_sortable': True, 'is_required': True},
                    'couleur': {'name': 'Couleur', 'data_type': 'choice', 'is_facet': True, 'is_sortable': True},
                    'classification': {'name': 'Classification', 'data_type': 'choice', 'is_facet': True, 'is_sortable': True},
                    'appellation': {'name': 'Appellation', 'data_type': 'text', 'is_facet': True, 'is_sortable': True, 'is_fulltext': True},
                    'degre_alcool': {'name': 'Degré d\'alcool', 'data_type': 'decimal', 'unit': '% vol.', 'is_sortable': True, 'is_facet': True},
                    'description': {'name': 'Description', 'data_type': 'text', 'is_fulltext': True},
                    'notes_degustation': {'name': 'Notes de dégustation', 'data_type': 'text', 'is_fulltext': True},
                }
            },
            'catalogue.Lot': {
                'name': 'Lot de production',
                'code': 'lot',
                'domain': 'production',
                'description': 'Lot de production avec volumes et statut',
                'attributes': {
                    'numero_lot': {'name': 'Numéro de lot', 'data_type': 'text', 'is_fulltext': True, 'is_sortable': True, 'is_required': True},
                    'millesime': {'name': 'Millésime', 'data_type': 'number', 'is_facet': True, 'is_sortable': True},
                    'volume_initial': {'name': 'Volume initial', 'data_type': 'decimal', 'unit': 'L', 'is_sortable': True, 'is_facet': True},
                    'volume_actuel': {'name': 'Volume actuel', 'data_type': 'decimal', 'unit': 'L', 'is_sortable': True, 'is_facet': True},
                    'statut': {'name': 'Statut', 'data_type': 'choice', 'is_facet': True, 'is_sortable': True},
                    'degre_alcool': {'name': 'Degré d\'alcool', 'data_type': 'decimal', 'unit': '% vol.', 'is_sortable': True, 'is_facet': True},
                    'densite': {'name': 'Densité', 'data_type': 'decimal', 'is_sortable': True},
                    'date_creation': {'name': 'Date de création', 'data_type': 'date', 'is_sortable': True, 'is_facet': True},
                    'notes': {'name': 'Notes', 'data_type': 'text', 'is_fulltext': True},
                }
            },
            'referentiels.Cepage': {
                'name': 'Cépage',
                'code': 'cepage',
                'domain': 'referentiel',
                'description': 'Variété de raisin',
                'attributes': {
                    'nom': {'name': 'Nom', 'data_type': 'text', 'is_fulltext': True, 'is_sortable': True, 'is_required': True},
                    'code': {'name': 'Code', 'data_type': 'text', 'is_sortable': True},
                    'couleur': {'name': 'Couleur', 'data_type': 'choice', 'is_facet': True, 'is_sortable': True},
                    'notes': {'name': 'Notes', 'data_type': 'text', 'is_fulltext': True},
                }
            },
            'referentiels.Parcelle': {
                'name': 'Parcelle',
                'code': 'parcelle',
                'domain': 'viticulture',
                'description': 'Parcelle de vignes',
                'attributes': {
                    'nom': {'name': 'Nom', 'data_type': 'text', 'is_fulltext': True, 'is_sortable': True, 'is_required': True},
                    'surface': {'name': 'Surface', 'data_type': 'decimal', 'unit': 'ha', 'is_sortable': True, 'is_facet': True},
                    'lieu_dit': {'name': 'Lieu-dit', 'data_type': 'text', 'is_fulltext': True, 'is_sortable': True},
                    'commune': {'name': 'Commune', 'data_type': 'text', 'is_facet': True, 'is_sortable': True, 'is_fulltext': True},
                    'appellation': {'name': 'Appellation', 'data_type': 'text', 'is_facet': True, 'is_sortable': True, 'is_fulltext': True},
                }
            },
            'referentiels.Unite': {
                'name': 'Unité',
                'code': 'unite',
                'domain': 'referentiel',
                'description': 'Unité de mesure',
                'attributes': {
                    'nom': {'name': 'Nom', 'data_type': 'text', 'is_fulltext': True, 'is_sortable': True, 'is_required': True},
                    'symbole': {'name': 'Symbole', 'data_type': 'text', 'is_sortable': True},
                    'type_unite': {'name': 'Type d\'unité', 'data_type': 'choice', 'is_facet': True, 'is_sortable': True},
                    'facteur_conversion': {'name': 'Facteur de conversion', 'data_type': 'decimal', 'is_sortable': True},
                }
            },
            'referentiels.Entrepot': {
                'name': 'Entrepôt',
                'code': 'entrepot',
                'domain': 'production',
                'description': 'Lieu de stockage',
                'attributes': {
                    'nom': {'name': 'Nom', 'data_type': 'text', 'is_fulltext': True, 'is_sortable': True, 'is_required': True},
                    'type_entrepot': {'name': 'Type d\'entrepôt', 'data_type': 'choice', 'is_facet': True, 'is_sortable': True},
                    'capacite': {'name': 'Capacité', 'data_type': 'decimal', 'unit': 'L', 'is_sortable': True, 'is_facet': True},
                    'adresse': {'name': 'Adresse', 'data_type': 'text', 'is_fulltext': True},
                    'notes': {'name': 'Notes', 'data_type': 'text', 'is_fulltext': True},
                }
            },
        }
        
        for model_path, config in entities_config.items():
            try:
                app_label, model_name = model_path.split('.')
                model_class = apps.get_model(app_label, model_name)
                
                # Enregistrer l'entité
                entity = self.register_entity(
                    model_class=model_class,
                    name=config['name'],
                    code=config['code'],
                    domain=config['domain'],
                    description=config.get('description', ''),
                )
                
                # Enregistrer les attributs
                for field_name, attr_config in config.get('attributes', {}).items():
                    self.register_attribute(
                        entity_code=config['code'],
                        field_name=field_name,
                        **attr_config
                    )
                
                print(f"Entité enregistrée: {config['name']} ({config['code']})")
                
            except Exception as e:
                print(f"Erreur lors de l'enregistrement de {model_path}: {e}")
    
    def get_searchable_entities(self, organization=None) -> List[MetaEntity]:
        """
        Retourne les entités recherchables
        
        Args:
            organization: Organisation (optionnel)
            
        Returns:
            Liste des entités recherchables
        """
        queryset = MetaEntity.objects.filter(
            is_searchable=True,
            is_active=True
        )
        
        if organization:
            queryset = queryset.filter(
                models.Q(organization=organization) | models.Q(organization__isnull=True)
            )
        
        return list(queryset.select_related('content_type'))
    
    def get_facet_attributes(self, entity_code: str) -> List[MetaAttribute]:
        """
        Retourne les attributs utilisables comme facettes
        
        Args:
            entity_code: Code de l'entité
            
        Returns:
            Liste des attributs facettes
        """
        try:
            entity = MetaEntity.objects.get(code=entity_code, is_active=True)
            return list(entity.attributes.filter(is_facet=True, is_active=True).order_by('display_order'))
        except MetaEntity.DoesNotExist:
            return []
    
    def get_sortable_attributes(self, entity_code: str) -> List[MetaAttribute]:
        """
        Retourne les attributs utilisables pour le tri
        
        Args:
            entity_code: Code de l'entité
            
        Returns:
            Liste des attributs triables
        """
        try:
            entity = MetaEntity.objects.get(code=entity_code, is_active=True)
            return list(entity.attributes.filter(is_sortable=True, is_active=True).order_by('display_order'))
        except MetaEntity.DoesNotExist:
            return []
    
    def get_fulltext_attributes(self, entity_code: str) -> List[MetaAttribute]:
        """
        Retourne les attributs pour la recherche textuelle
        
        Args:
            entity_code: Code de l'entité
            
        Returns:
            Liste des attributs full-text
        """
        try:
            entity = MetaEntity.objects.get(code=entity_code, is_active=True)
            return list(entity.attributes.filter(is_fulltext=True, is_active=True))
        except MetaEntity.DoesNotExist:
            return []


# Instance globale du service
metadata_service = MetadataService()
