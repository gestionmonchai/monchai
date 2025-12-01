"""
Validateurs avancés pour les clients - Roadmap 37
Email, téléphone E.164, numéros de TVA par pays
"""

import re
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _


class AdvancedEmailValidator(EmailValidator):
    """Validateur email amélioré avec normalisation"""
    
    def deconstruct(self):
        """Permet la sérialisation dans les migrations"""
        return ('apps.clients.validators.AdvancedEmailValidator', [], {})
    
    def __call__(self, value):
        if not value:
            return
        
        # Normalisation : lowercase et trim
        normalized = value.lower().strip()
        
        # Validation de base
        super().__call__(normalized)
        
        # Validations supplémentaires
        if len(normalized) > 254:
            raise ValidationError(_('L\'adresse email ne peut pas dépasser 254 caractères.'))
        
        local, domain = normalized.split('@', 1)
        
        if len(local) > 64:
            raise ValidationError(_('La partie locale de l\'email ne peut pas dépasser 64 caractères.'))
        
        # Domaines interdits (exemple)
        forbidden_domains = ['tempmail.org', '10minutemail.com', 'guerrillamail.com']
        if domain in forbidden_domains:
            raise ValidationError(_('Ce domaine email n\'est pas autorisé.'))


class PhoneE164Validator:
    """
    Validateur pour numéros de téléphone au format E.164
    Utilise des regex simples en attendant libphonenumber
    """
    
    # Patterns E.164 simplifiés par pays
    COUNTRY_PATTERNS = {
        'FR': r'^\+33[1-9](?:[0-9]{8})$',  # France
        'US': r'^\+1[2-9][0-9]{9}$',       # USA
        'CH': r'^\+41[1-9][0-9]{8}$',      # Suisse
        'IT': r'^\+39[0-9]{6,11}$',        # Italie
        'ES': r'^\+34[6-9][0-9]{8}$',      # Espagne
        'DE': r'^\+49[1-9][0-9]{10,11}$',  # Allemagne
        'BE': r'^\+32[1-9][0-9]{7,8}$',    # Belgique
    }
    
    def __init__(self, country_code=None):
        self.country_code = country_code
    
    def deconstruct(self):
        """Permet la sérialisation dans les migrations"""
        return ('apps.clients.validators.PhoneE164Validator', [], {'country_code': self.country_code})
    
    def __call__(self, value):
        if not value:
            return
        
        # Normalisation : suppression des espaces et tirets
        normalized = re.sub(r'[\s\-\(\)]', '', value.strip())
        
        # Vérification format E.164 de base
        if not normalized.startswith('+'):
            raise ValidationError(_('Le numéro de téléphone doit commencer par + (format E.164).'))
        
        if not re.match(r'^\+[1-9]\d{1,14}$', normalized):
            raise ValidationError(_('Format de téléphone invalide. Utilisez le format E.164 (+33123456789).'))
        
        # Validation spécifique par pays si fourni
        if self.country_code and self.country_code in self.COUNTRY_PATTERNS:
            pattern = self.COUNTRY_PATTERNS[self.country_code]
            if not re.match(pattern, normalized):
                raise ValidationError(
                    _('Le numéro de téléphone n\'est pas valide pour le pays {}.').format(self.country_code)
                )
    
    @staticmethod
    def normalize_phone(phone, country_code=None):
        """Normalise un numéro de téléphone"""
        if not phone:
            return phone
        
        # Suppression des espaces et caractères spéciaux
        normalized = re.sub(r'[\s\-\(\)]', '', phone.strip())
        
        # Si pas de +, essayer d'ajouter le préfixe pays
        if not normalized.startswith('+') and country_code:
            country_prefixes = {
                'FR': '+33',
                'US': '+1',
                'CH': '+41',
                'IT': '+39',
                'ES': '+34',
                'DE': '+49',
                'BE': '+32',
            }
            
            if country_code in country_prefixes:
                prefix = country_prefixes[country_code]
                # Supprimer le 0 initial pour la France
                if country_code == 'FR' and normalized.startswith('0'):
                    normalized = normalized[1:]
                normalized = prefix + normalized
        
        return normalized


class VATNumberValidator:
    """
    Validateur pour numéros de TVA par pays
    Patterns simplifiés - peut être étendu avec une API VIES
    """
    
    def deconstruct(self):
        """Permet la sérialisation dans les migrations"""
        return ('apps.clients.validators.VATNumberValidator', [], {'country_code': getattr(self, 'country_code', None)})
    
    # Patterns de numéros de TVA par pays
    VAT_PATTERNS = {
        'FR': r'^FR[0-9A-Z]{2}[0-9]{9}$',           # France: FR + 2 caractères + 9 chiffres
        'DE': r'^DE[0-9]{9}$',                      # Allemagne: DE + 9 chiffres
        'IT': r'^IT[0-9]{11}$',                     # Italie: IT + 11 chiffres
        'ES': r'^ES[A-Z][0-9]{7}[A-Z]$',           # Espagne: ES + lettre + 7 chiffres + lettre
        'BE': r'^BE[0-9]{10}$',                     # Belgique: BE + 10 chiffres
        'NL': r'^NL[0-9]{9}B[0-9]{2}$',            # Pays-Bas: NL + 9 chiffres + B + 2 chiffres
        'CH': r'^CHE[0-9]{9}(MWST|TVA|IVA)$',      # Suisse: CHE + 9 chiffres + suffixe
        'US': r'^US[0-9]{2}-[0-9]{7}$',            # USA: format simplifié
    }
    
    def __init__(self, country_code=None):
        self.country_code = country_code
    
    def __call__(self, value):
        if not value:
            return
        
        # Normalisation : uppercase et suppression des espaces/tirets
        normalized = re.sub(r'[\s\-\.]', '', value.upper().strip())
        
        # Validation de base
        if len(normalized) < 4:
            raise ValidationError(_('Le numéro de TVA est trop court.'))
        
        if len(normalized) > 15:
            raise ValidationError(_('Le numéro de TVA est trop long.'))
        
        # Extraction du code pays du numéro de TVA
        vat_country = normalized[:2]
        
        # Si un pays est spécifié, vérifier la cohérence
        if self.country_code and vat_country != self.country_code:
            raise ValidationError(
                _('Le numéro de TVA doit correspondre au pays sélectionné ({}).').format(self.country_code)
            )
        
        # Validation par pattern si disponible
        if vat_country in self.VAT_PATTERNS:
            pattern = self.VAT_PATTERNS[vat_country]
            if not re.match(pattern, normalized):
                raise ValidationError(
                    _('Format de numéro de TVA invalide pour le pays {}.').format(vat_country)
                )
        else:
            # Pattern générique pour pays non supportés
            if not re.match(r'^[A-Z]{2}[A-Z0-9]{4,13}$', normalized):
                raise ValidationError(_('Format de numéro de TVA invalide.'))
    
    @staticmethod
    def normalize_vat(vat_number):
        """Normalise un numéro de TVA"""
        if not vat_number:
            return vat_number
        
        return re.sub(r'[\s\-\.]', '', vat_number.upper().strip())


class CountryCodeValidator:
    """Validateur pour codes pays ISO 3166-1 alpha-2"""
    
    def deconstruct(self):
        """Permet la sérialisation dans les migrations"""
        return ('apps.clients.validators.CountryCodeValidator', [], {})
    
    # Liste des codes pays supportés (peut être étendue)
    VALID_COUNTRIES = {
        'FR', 'DE', 'IT', 'ES', 'BE', 'NL', 'CH', 'AT', 'PT', 'LU',
        'US', 'CA', 'GB', 'IE', 'DK', 'SE', 'NO', 'FI', 'PL', 'CZ'
    }
    
    def __call__(self, value):
        if not value:
            return
        
        normalized = value.upper().strip()
        
        if len(normalized) != 2:
            raise ValidationError(_('Le code pays doit faire exactement 2 caractères.'))
        
        if not re.match(r'^[A-Z]{2}$', normalized):
            raise ValidationError(_('Le code pays doit contenir uniquement des lettres.'))
        
        if normalized not in self.VALID_COUNTRIES:
            raise ValidationError(
                _('Code pays non supporté. Codes valides: {}').format(', '.join(sorted(self.VALID_COUNTRIES)))
            )


class CustomerNameValidator:
    """Validateur pour nom de client avec normalisation"""
    
    def deconstruct(self):
        """Permet la sérialisation dans les migrations"""
        return ('apps.clients.validators.CustomerNameValidator', [], {})
    
    def __call__(self, value):
        if not value:
            raise ValidationError(_('Le nom est obligatoire.'))
        
        normalized = value.strip()
        
        if len(normalized) < 2:
            raise ValidationError(_('Le nom doit faire au moins 2 caractères.'))
        
        if len(normalized) > 120:
            raise ValidationError(_('Le nom ne peut pas dépasser 120 caractères.'))
        
        # Caractères interdits
        forbidden_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        for char in forbidden_chars:
            if char in normalized:
                raise ValidationError(_('Le nom contient des caractères interdits.'))
    
    @staticmethod
    def normalize_name(name):
        """Normalise un nom pour la recherche"""
        if not name:
            return name
        
        import unicodedata
        
        # Normalisation Unicode et suppression des accents
        normalized = unicodedata.normalize('NFD', name.lower().strip())
        normalized = normalized.encode('ascii', 'ignore').decode('ascii')
        
        # Collapse des espaces multiples
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
