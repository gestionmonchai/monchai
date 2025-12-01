"""
Factories pour les tests - Sprint 08
Utilise factory_boy pour créer des objets de test cohérents
"""

import factory
from django.contrib.auth import get_user_model
from apps.accounts.models import Organization, Membership

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des utilisateurs de test"""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f'user{n}@test.com')
    email = factory.SelfAttribute('username')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if create:
            obj.set_password(extracted or 'testpass123')
            obj.save()


class OrganizationFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des organisations de test"""
    
    class Meta:
        model = Organization
    
    name = factory.Faker('company')
    siret = factory.Sequence(lambda n: f'{12345678901234 + n}')
    tva_number = factory.Sequence(lambda n: f'FR{12345678901 + n}')
    currency = 'EUR'
    is_initialized = True


class MembershipFactory(factory.django.DjangoModelFactory):
    """Factory pour créer des memberships de test"""
    
    class Meta:
        model = Membership
    
    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    role = Membership.Role.EDITOR
    is_active = True


class OwnerMembershipFactory(MembershipFactory):
    """Factory pour créer un membership owner"""
    role = Membership.Role.OWNER


class AdminMembershipFactory(MembershipFactory):
    """Factory pour créer un membership admin"""
    role = Membership.Role.ADMIN


class ReadOnlyMembershipFactory(MembershipFactory):
    """Factory pour créer un membership read-only"""
    role = Membership.Role.READ_ONLY
