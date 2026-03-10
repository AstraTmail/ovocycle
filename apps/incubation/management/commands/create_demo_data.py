"""
Management command : génère des données de démonstration réalistes.
Usage: python manage.py create_demo_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'Crée des données de démonstration pour OvoCycle'

    def handle(self, *args, **options):
        from apps.incubation.models import (
            IncubationBatch, Egg, EggObservation, IncubatorLog,
            BatchStatus, EggStatus, CandlingResult, SpeciesChoices
        )

        today = date.today()
        self.stdout.write('🥚 Création des données de démonstration...')

        # ── Cycles terminés (historique) ──────────────────────────────────────
        completed_data = [
            ('Marans Noir Cuivré — Lot 1', 'chicken', 'Marans Noir Cuivré', today - timedelta(days=100), 30, 22, 8),
            ('Sussex Blanc — Lot 1',        'chicken', 'Sussex Blanc Herminé', today - timedelta(days=70),  28, 20, 8),
            ('Wyandotte Dorée — Lot 1',     'chicken', 'Wyandotte Dorée Liseré', today - timedelta(days=50), 24, 15, 9),
            ('Caille Japonaise — Lot 1',    'quail',   'Coturnix Japonica', today - timedelta(days=40),  48, 38, 10),
            ('Marans Noir Cuivré — Lot 2',  'chicken', 'Marans Noir Cuivré', today - timedelta(days=30),  32, 27, 5),
            ('Sussex Blanc — Lot 2',        'chicken', 'Sussex Blanc Herminé', today - timedelta(days=25), 30, 24, 6),
        ]

        for name, species, breed, entry_date, total, hatched, failed in completed_data:
            batch = IncubationBatch.objects.create(
                name=name,
                species=species,
                breed=breed,
                entry_date=entry_date,
                total_eggs=total,
                status=BatchStatus.COMPLETED,
                target_temp='37.80',
                target_humidity='55.00',
                hatched_count=hatched,
                failed_count=failed,
                actual_hatch_date=entry_date + timedelta(days=21),
            )
            # Créer quelques œufs avec statuts
            self._create_eggs(batch, total, hatched, failed)
            self.stdout.write(f'  ✓ Lot terminé : {name} ({batch.hatch_rate}%)')

        # ── Lot actif — J18 (lockdown) ────────────────────────────────────────
        batch_lockdown = IncubationBatch.objects.create(
            name='Marans Noir Cuivré — Lot Actuel',
            species='chicken',
            breed='Marans Noir Cuivré',
            entry_date=today - timedelta(days=18),
            total_eggs=30,
            status=BatchStatus.LOCKDOWN,
            target_temp='37.80',
            target_humidity='55.00',
            notes='Lot de test avec couveuse principale. Suivi rigoureux.',
        )
        self._create_eggs(batch_lockdown, 30, None, None)
        # Ajouter logs couveuse
        for i in range(5):
            IncubatorLog.objects.create(
                batch=batch_lockdown,
                logged_at=timezone.now() - timedelta(hours=i*12),
                temperature=37.8 + random.uniform(-0.2, 0.2),
                humidity=55 + random.uniform(-3, 3),
                event='Relevé automatique' if i > 0 else 'Passage en lockdown — arrêt retournement',
            )
        self.stdout.write(f'  ✓ Lot actif J18 (lockdown) : {batch_lockdown.name}')

        # ── Lot actif — J11 ───────────────────────────────────────────────────
        batch_mid = IncubationBatch.objects.create(
            name='Sussex Blanc — Lot Actuel',
            species='chicken',
            breed='Sussex Blanc Herminé',
            entry_date=today - timedelta(days=11),
            total_eggs=32,
            status=BatchStatus.ACTIVE,
            target_temp='37.80',
            target_humidity='55.00',
        )
        self._create_eggs(batch_mid, 32, None, None)
        self.stdout.write(f'  ✓ Lot actif J11 : {batch_mid.name}')

        # ── Lot actif — J5 ────────────────────────────────────────────────────
        batch_new = IncubationBatch.objects.create(
            name='Caille Japonaise — Lot Actuel',
            species='quail',
            breed='Coturnix Japonica',
            entry_date=today - timedelta(days=5),
            total_eggs=48,
            status=BatchStatus.ACTIVE,
            target_temp='37.50',
            target_humidity='60.00',
        )
        self._create_eggs(batch_new, 48, None, None)
        self.stdout.write(f'  ✓ Lot actif J5 : {batch_new.name}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅  Données de démonstration créées avec succès !'))
        self.stdout.write(f'   Total : {IncubationBatch.objects.count()} lots, {Egg.objects.count()} œufs')

    def _create_eggs(self, batch, total, hatched, failed):
        from apps.incubation.models import Egg, EggObservation, EggStatus, CandlingResult

        cols = 8
        eggs = []
        for i in range(1, total + 1):
            r = ((i - 1) // cols) + 1
            c = ((i - 1) % cols) + 1
            eggs.append(Egg(
                batch=batch,
                identifier=str(i).zfill(3),
                row=r, column=c,
                position_label=f"{'ABCDEFGH'[r-1]}{c}",
            ))
        created_eggs = Egg.objects.bulk_create(eggs)

        # Si cycle terminé → assigner des statuts
        if hatched is not None:
            all_eggs = list(batch.eggs.all())
            random.shuffle(all_eggs)
            for i, egg in enumerate(all_eggs):
                if i < hatched:
                    egg.status = EggStatus.HATCHED
                elif i < hatched + failed:
                    egg.status = EggStatus.FAILED
                elif i < hatched + failed + int((total - hatched - failed) * 0.3):
                    egg.status = EggStatus.DEAD_EMBRYO
                else:
                    egg.status = EggStatus.CLEAR
                egg.save(update_fields=['status'])
