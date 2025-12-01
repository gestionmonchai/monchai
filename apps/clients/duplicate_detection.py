"""
Service de détection de doublons pour les clients - Roadmap 37
"""

from django.db.models import Q
from django.core.cache import cache
from .models import Customer
import hashlib


class DuplicateDetectionService:
    """Service de détection de doublons clients en temps réel"""
    
    CACHE_TTL = 300  # 5 minutes
    
    @staticmethod
    def check_duplicates(organization, name=None, email=None, phone=None, vat_number=None, exclude_id=None):
        """
        Détecte les doublons potentiels pour un client
        
        Args:
            organization: Organisation courante
            name: Nom du client
            email: Email du client
            phone: Téléphone du client
            vat_number: Numéro de TVA
            exclude_id: ID du client à exclure (pour édition)
            
        Returns:
            dict: {
                'duplicates': [...],
                'score': float,
                'suggestions': [...]
            }
        """
        # Cache key basé sur les paramètres
        cache_params = f"{organization.id}_{name}_{email}_{phone}_{vat_number}_{exclude_id}"
        cache_key = f"duplicate_check_{hashlib.md5(cache_params.encode()).hexdigest()}"
        
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        duplicates = []
        suggestions = []
        max_score = 0.0
        
        # Requête de base
        queryset = Customer.objects.filter(organization=organization, is_active=True)
        
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        # 1. Vérification exacte du numéro de TVA (score max)
        if vat_number:
            vat_exact = queryset.filter(vat_number__iexact=vat_number.strip())
            if vat_exact.exists():
                for customer in vat_exact:
                    duplicates.append({
                        'customer': customer,
                        'score': 1.0,
                        'reason': 'Numéro de TVA identique',
                        'field': 'vat_number'
                    })
                max_score = 1.0
        
        # 2. Vérification exacte de l'email (score élevé)
        if email and max_score < 0.9:
            email_exact = queryset.filter(email__iexact=email.strip())
            if email_exact.exists():
                for customer in email_exact:
                    duplicates.append({
                        'customer': customer,
                        'score': 0.9,
                        'reason': 'Email identique',
                        'field': 'email'
                    })
                max_score = max(max_score, 0.9)
        
        # 3. Vérification exacte du téléphone (score élevé)
        if phone and max_score < 0.8:
            # Normalisation simple du téléphone pour comparaison
            normalized_phone = DuplicateDetectionService._normalize_phone_for_search(phone)
            if normalized_phone:
                phone_exact = queryset.filter(phone__icontains=normalized_phone[-8:])  # 8 derniers chiffres
                if phone_exact.exists():
                    for customer in phone_exact:
                        duplicates.append({
                            'customer': customer,
                            'score': 0.8,
                            'reason': 'Téléphone similaire',
                            'field': 'phone'
                        })
                    max_score = max(max_score, 0.8)
        
        # 4. Vérification similarité du nom (score moyen)
        if name and max_score < 0.7:
            # Normalisation du nom pour recherche
            normalized_name = DuplicateDetectionService._normalize_name_for_search(name)
            if len(normalized_name) >= 3:
                # Recherche par similarité trigram (simulation)
                name_similar = queryset.filter(
                    Q(name_norm__icontains=normalized_name) |
                    Q(name__icontains=name.strip())
                )
                
                for customer in name_similar:
                    # Calcul de similarité simple
                    similarity = DuplicateDetectionService._calculate_name_similarity(
                        normalized_name, customer.name_norm
                    )
                    
                    if similarity > 0.6:
                        duplicates.append({
                            'customer': customer,
                            'score': similarity * 0.7,  # Score pondéré
                            'reason': f'Nom similaire ({similarity:.0%})',
                            'field': 'name'
                        })
                        max_score = max(max_score, similarity * 0.7)
        
        # 5. Suggestions pour améliorer la recherche
        if not duplicates and name:
            # Recherche élargie pour suggestions
            suggestions = DuplicateDetectionService._get_suggestions(organization, name, exclude_id)
        
        # Tri des doublons par score décroissant
        duplicates.sort(key=lambda x: x['score'], reverse=True)
        
        # Limitation à 5 doublons max
        duplicates = duplicates[:5]
        
        result = {
            'duplicates': [
                {
                    'id': str(d['customer'].id),
                    'name': d['customer'].name,
                    'segment': d['customer'].segment,
                    'segment_display': d['customer'].get_segment_display(),
                    'email': d['customer'].email,
                    'phone': d['customer'].phone,
                    'vat_number': d['customer'].vat_number,
                    'score': d['score'],
                    'reason': d['reason'],
                    'field': d['field']
                }
                for d in duplicates
            ],
            'max_score': max_score,
            'suggestions': suggestions,
            'has_high_risk': max_score >= 0.8,
            'has_medium_risk': 0.5 <= max_score < 0.8,
        }
        
        # Cache pendant 5 minutes
        cache.set(cache_key, result, DuplicateDetectionService.CACHE_TTL)
        
        return result
    
    @staticmethod
    def _normalize_phone_for_search(phone):
        """Normalise un téléphone pour la recherche de doublons"""
        if not phone:
            return ''
        
        import re
        # Suppression de tous les caractères non numériques
        normalized = re.sub(r'[^\d]', '', phone)
        
        # Suppression du préfixe pays commun
        if normalized.startswith('33') and len(normalized) == 11:  # France
            normalized = normalized[2:]
        elif normalized.startswith('1') and len(normalized) == 11:  # USA
            normalized = normalized[1:]
        
        return normalized
    
    @staticmethod
    def _normalize_name_for_search(name):
        """Normalise un nom pour la recherche de doublons"""
        if not name:
            return ''
        
        import unicodedata
        import re
        
        # Normalisation Unicode et suppression des accents
        normalized = unicodedata.normalize('NFD', name.lower().strip())
        normalized = normalized.encode('ascii', 'ignore').decode('ascii')
        
        # Suppression des mots courants
        stop_words = ['sarl', 'sas', 'sa', 'eurl', 'sasu', 'sci', 'snc', 'scp', 'cie', 'et', 'fils', 'freres']
        words = normalized.split()
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        return ' '.join(filtered_words)
    
    @staticmethod
    def _calculate_name_similarity(name1, name2):
        """Calcule la similarité entre deux noms (0-1)"""
        if not name1 or not name2:
            return 0.0
        
        # Similarité simple basée sur les mots communs
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def _get_suggestions(organization, name, exclude_id=None):
        """Obtient des suggestions pour améliorer la recherche"""
        suggestions = []
        
        if not name or len(name) < 3:
            return suggestions
        
        # Recherche de noms proches
        queryset = Customer.objects.filter(organization=organization, is_active=True)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        # Recherche par début de nom
        name_starts = queryset.filter(name__istartswith=name[:3]).values_list('name', flat=True)[:3]
        
        for suggestion_name in name_starts:
            if suggestion_name.lower() != name.lower():
                suggestions.append({
                    'type': 'name_similar',
                    'text': f'Vouliez-vous dire "{suggestion_name}" ?',
                    'value': suggestion_name
                })
        
        return suggestions
