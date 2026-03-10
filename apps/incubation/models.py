from django.db import models
from django.utils import timezone
from datetime import timedelta


class EggStatus(models.TextChoices):
    PENDING      = 'pending',     'En attente'
    FERTILE      = 'fertile',     'Fertile'
    CLEAR        = 'clear',       'Clair (infertile)'
    DEAD_EMBRYO  = 'dead_embryo', 'Mort embryonnaire'
    CRACKED      = 'cracked',     'Fissuré'
    HATCHED      = 'hatched',     'Éclos ✓'
    FAILED       = 'failed',      'Échoué'
    REMOVED      = 'removed',     'Retiré'


class CandlingResult(models.TextChoices):
    FERTILE   = 'fertile',   'Fertile / Vivant'
    CLEAR     = 'clear',     'Clair (infertile)'
    DEAD      = 'dead',      'Mort embryonnaire'
    UNCERTAIN = 'uncertain', 'Incertain'
    READY     = 'ready',     'Prêt pour éclosion'


class BatchStatus(models.TextChoices):
    ACTIVE    = 'active',    'En cours'
    LOCKDOWN  = 'lockdown',  'Lockdown (J18)'
    HATCHING  = 'hatching',  'Éclosion en cours'
    COMPLETED = 'completed', 'Terminé'
    ABORTED   = 'aborted',   'Abandonné'


class SpeciesChoices(models.TextChoices):
    CHICKEN  = 'chicken',  'Poulet (21j)'
    DUCK     = 'duck',     'Canard (28j)'
    QUAIL    = 'quail',    'Caille (17j)'
    TURKEY   = 'turkey',   'Dinde (28j)'
    GOOSE    = 'goose',    'Oie (30j)'
    PHEASANT = 'pheasant', 'Faisan (24j)'
    OTHER    = 'other',    'Autre'


# Durée d'incubation par espèce (jours)
INCUBATION_DAYS = {
    'chicken':  21,
    'duck':     28,
    'quail':    17,
    'turkey':   28,
    'goose':    30,
    'pheasant': 24,
    'other':    21,
}


class IncubationBatch(models.Model):
    """Lot d'incubation — unité d'analyse principale."""

    name      = models.CharField(max_length=100, verbose_name="Nom du lot")
    species   = models.CharField(
        max_length=20, choices=SpeciesChoices.choices,
        default=SpeciesChoices.CHICKEN, verbose_name="Espèce"
    )
    breed     = models.CharField(max_length=100, blank=True, verbose_name="Race / Souche")
    source    = models.CharField(max_length=200, blank=True, verbose_name="Provenance des œufs")

    entry_date  = models.DateField(verbose_name="Date d'entrée en couveuse")
    status      = models.CharField(
        max_length=20, choices=BatchStatus.choices,
        default=BatchStatus.ACTIVE, verbose_name="Statut"
    )
    total_eggs  = models.PositiveIntegerField(verbose_name="Nombre total d'œufs")

    # Conditions cibles
    target_temp     = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Température cible (°C)")
    target_humidity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Humidité cible (%)")

    # Résultats fin de cycle
    hatched_count     = models.PositiveIntegerField(null=True, blank=True, verbose_name="Œufs éclos")
    failed_count      = models.PositiveIntegerField(null=True, blank=True, verbose_name="Œufs échoués")
    actual_hatch_date = models.DateField(null=True, blank=True, verbose_name="Date réelle d'éclosion")

    notes      = models.TextField(blank=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lot d'incubation"
        verbose_name_plural = "Lots d'incubation"
        ordering = ['-entry_date']

    def __str__(self):
        return f"{self.name} ({self.entry_date})"

    # ── Durée selon espèce ──────────────────────────────────────────────────

    @property
    def total_days(self):
        return INCUBATION_DAYS.get(self.species, 21)

    # ── Dates calculées ─────────────────────────────────────────────────────

    @property
    def candling_1_date(self):
        return self.entry_date + timedelta(days=7)

    @property
    def candling_2_date(self):
        return self.entry_date + timedelta(days=14)

    @property
    def candling_3_date(self):
        return self.entry_date + timedelta(days=self.total_days - 3)

    @property
    def lockdown_date(self):
        return self.entry_date + timedelta(days=self.total_days - 3)

    @property
    def estimated_hatch_date(self):
        return self.entry_date + timedelta(days=self.total_days)

    # ── Progression ─────────────────────────────────────────────────────────

    @property
    def incubation_day(self):
        today = timezone.now().date()
        delta = (today - self.entry_date).days
        return max(0, min(delta, self.total_days))

    @property
    def progress_percent(self):
        return min(100, int((self.incubation_day / self.total_days) * 100))

    # ── Alertes ─────────────────────────────────────────────────────────────

    @property
    def today_alerts(self):
        today = timezone.now().date()
        alerts = []
        if today == self.candling_1_date:
            alerts.append({'type': 'candling', 'label': '🔍 Mirage 1 aujourd\'hui', 'priority': 'high'})
        if today == self.candling_2_date:
            alerts.append({'type': 'candling', 'label': '🔍 Mirage 2 aujourd\'hui', 'priority': 'high'})
        if today == self.candling_3_date:
            alerts.append({'type': 'lockdown', 'label': '🔒 Mirage 3 + Lockdown aujourd\'hui', 'priority': 'critical'})
        if today == self.estimated_hatch_date:
            alerts.append({'type': 'hatch', 'label': '🐣 Éclosion prévue aujourd\'hui !', 'priority': 'critical'})
        return alerts

    @property
    def upcoming_events(self):
        today = timezone.now().date()
        events = []
        checks = [
            (self.candling_1_date,      'Mirage 1',           'candling', 1),
            (self.candling_2_date,      'Mirage 2',           'candling', 2),
            (self.candling_3_date,      'Mirage 3 + Lockdown','lockdown', 3),
            (self.estimated_hatch_date, 'Éclosion estimée',   'hatch',    0),
        ]
        for date, label, etype, num in checks:
            diff = (date - today).days
            if 0 <= diff <= 7:
                events.append({'date': date, 'label': label, 'type': etype, 'days_left': diff, 'num': num})
        return events

    # ── Statistiques ────────────────────────────────────────────────────────

    @property
    def hatch_rate(self):
        if self.hatched_count is None or self.total_eggs == 0:
            return None
        return round((self.hatched_count / self.total_eggs) * 100, 1)

    @property
    def fertility_rate(self):
        fertile = self.eggs.filter(
            status__in=[EggStatus.FERTILE, EggStatus.HATCHED, EggStatus.FAILED, EggStatus.DEAD_EMBRYO]
        ).count()
        total = self.eggs.exclude(status=EggStatus.REMOVED).count()
        if total == 0:
            return None
        return round((fertile / total) * 100, 1)

    @property
    def embryo_mortality_rate(self):
        dead = self.eggs.filter(status=EggStatus.DEAD_EMBRYO).count()
        fertile = self.eggs.filter(
            status__in=[EggStatus.FERTILE, EggStatus.HATCHED, EggStatus.FAILED, EggStatus.DEAD_EMBRYO]
        ).count()
        if fertile == 0:
            return None
        return round((dead / fertile) * 100, 1)

    @property
    def egg_stats(self):
        """Résumé des statuts pour graphique."""
        from django.db.models import Count
        stats = {s: 0 for s in EggStatus.values}
        qs = self.eggs.values('status').annotate(count=Count('id'))
        for row in qs:
            stats[row['status']] = row['count']
        return stats

    @property
    def timeline_steps(self):
        today = timezone.now().date()
        steps = [
            {'label': 'Entrée',   'date': self.entry_date,          'day': 0,               'type': 'start'},
            {'label': 'Mirage 1', 'date': self.candling_1_date,     'day': 7,               'type': 'candling'},
            {'label': 'Mirage 2', 'date': self.candling_2_date,     'day': 14,              'type': 'candling'},
            {'label': 'Lockdown', 'date': self.lockdown_date,       'day': self.total_days - 3, 'type': 'lockdown'},
            {'label': 'Éclosion', 'date': self.estimated_hatch_date,'day': self.total_days, 'type': 'hatch'},
        ]
        for step in steps:
            step['is_past']   = step['date'] < today
            step['is_today']  = step['date'] == today
            step['is_future'] = step['date'] > today
        return steps


class Egg(models.Model):
    """
    Œuf individuel dans un lot.

    - identifier : numéro séquentiel auto (001, 002…) inscrit sur l'œuf
    - Position physique dans la couveuse : floor + column + row → code E2A3
      floor  : étage 1, 2 ou 3
      column : A(1), B(2), C(3), D(4), E(5)
      row    : ligne 1 à 6
    """

    FLOOR_CHOICES  = [(1, 'Étage 1'), (2, 'Étage 2'), (3, 'Étage 3')]
    COLUMN_CHOICES = [(1,'A'),(2,'B'),(3,'C'),(4,'D'),(5,'E')]
    ROW_CHOICES    = [(i, str(i)) for i in range(1, 7)]

    batch      = models.ForeignKey(IncubationBatch, on_delete=models.CASCADE, related_name='eggs', verbose_name="Lot")

    # Numéro séquentiel inscrit sur l'œuf (001, 002…) — généré automatiquement
    identifier = models.CharField(max_length=10, verbose_name="N° sur l'œuf", editable=False)

    # Position physique dans la couveuse — saisie manuellement
    floor  = models.PositiveSmallIntegerField(choices=FLOOR_CHOICES, verbose_name="Étage")
    column = models.PositiveSmallIntegerField(choices=COLUMN_CHOICES, verbose_name="Colonne")
    row    = models.PositiveSmallIntegerField(choices=ROW_CHOICES,    verbose_name="Ligne")

    status   = models.CharField(max_length=20, choices=EggStatus.choices, default=EggStatus.PENDING, verbose_name="Statut")
    weight_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Poids initial (g)")
    notes    = models.TextField(blank=True, verbose_name="Notes")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Œuf"
        verbose_name_plural = "Œufs"
        ordering = ['identifier']
        unique_together = [
            ['batch', 'floor', 'column', 'row'],  # Une seule position par lot
        ]

    def save(self, *args, **kwargs):
        # Génère l'identifiant séquentiel automatiquement à la création
        if not self.identifier:
            last = Egg.objects.filter(batch=self.batch).order_by('-identifier').first()
            if last and last.identifier.isdigit():
                self.identifier = str(int(last.identifier) + 1).zfill(3)
            else:
                count = Egg.objects.filter(batch=self.batch).count()
                self.identifier = str(count + 1).zfill(3)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Œuf {self.identifier} — {self.position_code} — {self.batch.name}"

    @property
    def position_code(self):
        """Code position affiché : E2A3"""
        return f"E{self.floor}{chr(64 + self.column)}{self.row}"

    @property
    def position_display(self):
        """Affichage lisible : Ét.2 / Col.A / L.3"""
        return f"Ét.{self.floor} / Col.{chr(64 + self.column)} / L.{self.row}"

    @property
    def latest_observation(self):
        return self.observations.order_by('-observed_at').first()

    @property
    def status_css(self):
        css = {
            'pending':     'bg-amber-50 border-amber-200 text-amber-700',
            'fertile':     'bg-green-50 border-green-200 text-green-700',
            'clear':       'bg-gray-50 border-gray-200 text-gray-400',
            'dead_embryo': 'bg-red-50 border-red-200 text-red-600',
            'cracked':     'bg-orange-50 border-orange-200 text-orange-600',
            'hatched':     'bg-emerald-50 border-emerald-300 text-emerald-700',
            'failed':      'bg-red-100 border-red-300 text-red-700',
            'removed':     'bg-gray-100 border-gray-300 text-gray-400',
        }
        return css.get(self.status, 'bg-gray-50 border-gray-200 text-gray-500')


class EggObservation(models.Model):
    """Observation d'un œuf lors d'un mirage."""

    CANDLING_CHOICES = [
        (0, 'Observation libre'),
        (1, 'Mirage 1 (J7)'),
        (2, 'Mirage 2 (J14)'),
        (3, 'Mirage 3 (J18)'),
    ]

    egg             = models.ForeignKey(Egg, on_delete=models.CASCADE, related_name='observations', verbose_name="Œuf")
    candling_number = models.PositiveSmallIntegerField(choices=CANDLING_CHOICES, default=0, verbose_name="Mirage")
    result          = models.CharField(max_length=20, choices=CandlingResult.choices, verbose_name="Résultat")
    notes           = models.TextField(blank=True, verbose_name="Observations")
    observed_at     = models.DateTimeField(default=timezone.now, verbose_name="Date")
    observed_by     = models.CharField(max_length=100, blank=True, verbose_name="Observé par")

    class Meta:
        verbose_name = "Observation"
        verbose_name_plural = "Observations"
        ordering = ['-observed_at']

    def __str__(self):
        return f"{self.get_candling_number_display()} — {self.egg}"


class IncubatorLog(models.Model):
    """Journal des conditions de la couveuse."""

    batch       = models.ForeignKey(IncubationBatch, on_delete=models.CASCADE, related_name='logs', verbose_name="Lot")
    logged_at   = models.DateTimeField(default=timezone.now, verbose_name="Date/Heure")
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Température (°C)")
    humidity    = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Humidité (%)")
    co2_ppm     = models.PositiveIntegerField(null=True, blank=True, verbose_name="CO2 (ppm)")
    event       = models.CharField(max_length=200, blank=True, verbose_name="Événement")
    notes       = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        verbose_name = "Log couveuse"
        verbose_name_plural = "Logs couveuse"
        ordering = ['-logged_at']

    def __str__(self):
        return f"Log {self.logged_at:%d/%m %H:%M} — {self.batch.name}"