from __future__ import annotations
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.accounts.models import Organization


class OnboardingState(models.Model):
    """
    État d'onboarding métier par organisation.
    Suit les étapes du cycle vinicole et leur statut done/pending + last_step_completed.
    """

    STEPS = [
        ('parcelles', "Parcelles"),
        ('vendanges', "Vendanges"),
        ('pressurages', "Pressurages"),
        ('encuvages', "Encuvages"),
        ('elevage', "Élevage / Analyses"),
        ('mises', "Mises"),
        ('lots', "Lots techniques"),
        ('stocks', "Stocks bouteilles"),
        ('ventes', "Ventes / Expéditions"),
    ]

    STATUS_CHOICES = [
        ('pending', 'pending'),
        ('done', 'done'),
    ]

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='onboarding_state')

    # Map {step_key: 'pending'|'done'}
    state = models.JSONField(default=dict, blank=True)

    # Map {step_key: bool} → True si l'utilisateur a cliqué "Passer" (skipped mais non réalisé)
    skipped = models.JSONField(default=dict, blank=True)

    last_step_completed = models.CharField(max_length=32, blank=True)

    dismissed = models.BooleanField(default=False, help_text="Onboarding masqué pour cette organisation")

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Onboarding – État"
        verbose_name_plural = "Onboarding – États"
        indexes = [
            models.Index(fields=['organization']),
        ]

    def __str__(self) -> str:
        return f"Onboarding {self.organization.name} ({self.get_progress()}%)"

    @classmethod
    def default_state(cls) -> dict:
        return {k: 'pending' for k, _ in cls.STEPS}

    def save(self, *args, **kwargs):
        if not self.state:
            self.state = self.default_state()
        # started_at logic
        if not self.started_at and any(v == 'done' for v in (self.state or {}).values()):
            self.started_at = timezone.now()
        # completed_at logic
        if self.is_completed():
            if not self.completed_at:
                self.completed_at = timezone.now()
        else:
            # reset completed_at if not complete anymore
            self.completed_at = None
        super().save(*args, **kwargs)

    # --- Helpers ---
    def is_completed(self) -> bool:
        st = self.state or {}
        return all(st.get(k) == 'done' for k, _ in self.STEPS)

    def get_progress(self) -> int:
        st = self.state or {}
        done = sum(1 for k, _ in self.STEPS if st.get(k) == 'done')
        total = len(self.STEPS)
        return int((done / total) * 100) if total else 0

    def set_step(self, step_key: str, status: str, *, mark_last=False):
        if step_key not in dict(self.STEPS):
            raise ValidationError(f"Étape inconnue: {step_key}")
        if status not in dict(self.STATUS_CHOICES):
            raise ValidationError(f"Statut invalide: {status}")
        if not self.state:
            self.state = self.default_state()
        self.state[step_key] = status
        if status == 'done' and mark_last:
            self.last_step_completed = step_key
        self.save()

    def mark_done(self, step_key: str):
        self.set_step(step_key, 'done', mark_last=True)

    def mark_skipped(self, step_key: str):
        sk = self.skipped or {}
        sk[step_key] = True
        self.skipped = sk
        # Reste en pending pour cette étape
        if not self.state:
            self.state = self.default_state()
        if self.state.get(step_key) != 'done':
            self.state[step_key] = 'pending'
        self.save()

    def ensure_all_keys(self):
        # S'assure que toutes les clés existent dans state/skipped
        st = self.state or {}
        for k, _ in self.STEPS:
            if k not in st:
                st[k] = 'pending'
        self.state = st
        sk = self.skipped or {}
        for k, _ in self.STEPS:
            if k not in sk:
                sk[k] = False
        self.skipped = sk
        self.save()
