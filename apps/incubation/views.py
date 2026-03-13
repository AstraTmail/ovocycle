import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import HttpResponse
from django.urls import reverse, reverse_lazy
from django.db.models import Count, Avg, Max
from django.utils import timezone
from datetime import timedelta
from django.template.loader import render_to_string

from .models import IncubationBatch, Egg, EggObservation, IncubatorLog, BatchStatus, EggStatus
from .forms import (
    IncubationBatchForm, BatchCompleteForm, EggForm,
    EggBulkCreateForm, EggPositionForm, EggObservationForm, IncubatorLogForm,
)


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()

        active_batches = IncubationBatch.objects.filter(
            status__in=[BatchStatus.ACTIVE, BatchStatus.LOCKDOWN, BatchStatus.HATCHING]
        ).prefetch_related('eggs')

        # Événements à venir
        upcoming = []
        for batch in active_batches:
            for evt in batch.upcoming_events:
                upcoming.append({**evt, 'batch': batch})
        upcoming.sort(key=lambda x: x['date'])

        # Stats globales
        completed = IncubationBatch.objects.filter(status=BatchStatus.COMPLETED)
        hatch_rates = [b.hatch_rate for b in completed if b.hatch_rate is not None]
        avg_hatch = round(sum(hatch_rates) / len(hatch_rates), 1) if hatch_rates else 0

        # Données graphique (10 derniers cycles)
        chart_batches = list(completed.order_by('-entry_date')[:10])
        chart_batches.reverse()
        chart_data = json.dumps([
            {'name': b.name[:15], 'rate': b.hatch_rate or 0}
            for b in chart_batches
        ])

        ctx.update({
            'active_batches': active_batches,
            'upcoming_events': upcoming[:6],
            'total_active': active_batches.count(),
            'total_completed': completed.count(),
            'avg_hatch_rate': avg_hatch,
            'total_eggs_active': sum(b.total_eggs for b in active_batches),
            'chart_data': chart_data,
        })
        return ctx


# ─── LOTS ─────────────────────────────────────────────────────────────────────

class BatchListView(LoginRequiredMixin, ListView):
    model = IncubationBatch
    template_name = 'batches/list.html'
    context_object_name = 'batches'

    def get_queryset(self):
        qs = super().get_queryset().annotate(egg_count=Count('eggs'))
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = BatchStatus.choices
        ctx['current_status'] = self.request.GET.get('status', '')
        return ctx


class BatchDetailView(LoginRequiredMixin, DetailView):
    model = IncubationBatch
    template_name = 'batches/detail.html'
    context_object_name = 'batch'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        batch = self.object
        ctx['eggs'] = batch.eggs.prefetch_related('observations').all()
        ctx['logs'] = batch.logs.order_by('-logged_at')[:15]
        ctx['log_form'] = IncubatorLogForm()
        # Données stats pour graphique en donut
        stats = batch.egg_stats
        ctx['egg_stats_json'] = json.dumps(stats)
        return ctx


class BatchCreateView(LoginRequiredMixin, CreateView):
    model = IncubationBatch
    form_class = IncubationBatchForm
    template_name = 'batches/form.html'

    def get_success_url(self):
        return reverse('incubation:batch-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'✓ Lot "{self.object.name}" créé avec succès !')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Nouveau lot d\'incubation'
        ctx['submit_label'] = 'Créer le lot'
        return ctx


class BatchUpdateView(LoginRequiredMixin, UpdateView):
    model = IncubationBatch
    form_class = IncubationBatchForm
    template_name = 'batches/form.html'

    def get_success_url(self):
        return reverse('incubation:batch-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'✓ Lot "{self.object.name}" mis à jour.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Modifier — {self.object.name}'
        ctx['submit_label'] = 'Enregistrer les modifications'
        return ctx


class BatchCompleteView(LoginRequiredMixin, UpdateView):
    model = IncubationBatch
    form_class = BatchCompleteForm
    template_name = 'batches/complete.html'

    def form_valid(self, form):
        batch = form.save(commit=False)
        batch.status = BatchStatus.COMPLETED
        batch.save()
        messages.success(self.request, f'🐣 Cycle "{batch.name}" terminé ! Taux d\'éclosion : {batch.hatch_rate}%')
        return redirect('incubation:batch-detail', pk=batch.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['batch'] = self.object
        return ctx


class BatchDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        # Sécurité : si quelqu'un accède à l'URL en GET, on redirige
        return redirect('incubation:batch-detail', pk=pk)

    def post(self, request, pk):
        batch = get_object_or_404(IncubationBatch, pk=pk)
        name = batch.name
        batch.delete()
        messages.success(request, f'🗑 Lot "{name}" supprimé définitivement.')
        return redirect('incubation:batch-list')


# ─── ŒUFS ─────────────────────────────────────────────────────────────────────

class EggBulkCreateView(LoginRequiredMixin, View):
    template_name = 'eggs/bulk_create.html'

    def get(self, request, batch_pk):
        batch = get_object_or_404(IncubationBatch, pk=batch_pk)
        count_str = request.GET.get('count')
        if count_str and count_str.isdigit():
            count = int(count_str)
            next_id = self._next_id(batch)
            position_forms = [
                (str(next_id + i).zfill(3), EggPositionForm(prefix=f'egg_{i}'))
                for i in range(count)
            ]
            return render(request, self.template_name, {
                'batch': batch, 'position_forms': position_forms,
                'count': count, 'step': 2,
            })
        return render(request, self.template_name, {
            'batch': batch, 'form': EggBulkCreateForm(),
            'step': 1, 'existing_count': batch.eggs.count(),
        })

    def post(self, request, batch_pk):
        batch = get_object_or_404(IncubationBatch, pk=batch_pk)
        count = int(request.POST.get('count') or 0)
        if count == 0:
            messages.error(request, 'Aucun oeuf a enregistrer.')
            return redirect('incubation:egg-bulk', batch_pk=batch_pk)

        next_id = self._next_id(batch)
        errors = []
        eggs_to_create = []

        for i in range(count):
            identifier = str(next_id + i).zfill(3)
            form = EggPositionForm(request.POST, prefix=f'egg_{i}')
            if form.is_valid():
                eggs_to_create.append(Egg(
                    batch=batch,
                    identifier=identifier,
                    floor=int(form.cleaned_data['floor']),
                    column=int(form.cleaned_data['column']),
                    row=int(form.cleaned_data['row']),
                ))
            else:
                errors.append(f"Oeuf {identifier} : {dict(form.errors)}")

        if errors:
            position_forms = [
                (str(next_id + i).zfill(3), EggPositionForm(request.POST, prefix=f'egg_{i}'))
                for i in range(count)
            ]
            return render(request, self.template_name, {
                'batch': batch, 'position_forms': position_forms,
                'count': count, 'step': 2, 'errors': errors,
            })

        # Vérifier doublons entre les nouveaux œufs
        new_positions = [(e.floor, e.column, e.row) for e in eggs_to_create]
        if len(new_positions) != len(set(new_positions)):
            duplicate_conflicts = [p for p in new_positions if new_positions.count(p) > 1]
            errors = [f"Position E{p[0]}{['','A','B','C','D','E'][p[1]]}{p[2]} saisie plusieurs fois." for p in set(duplicate_conflicts)]
            position_forms = [
                (str(next_id + i).zfill(3), EggPositionForm(request.POST, prefix=f'egg_{i}'))
                for i in range(count)
            ]
            return render(request, self.template_name, {
                'batch': batch, 'position_forms': position_forms,
                'count': count, 'step': 2, 'errors': errors,
            })

        # Vérifier conflits avec les œufs déjà existants dans ce lot
        existing_positions = set(
            batch.eggs.values_list('floor', 'column', 'row')
        )
        conflicts = [
            f"Position E{e.floor}{['','A','B','C','D','E'][e.column]}{e.row} déjà occupée dans ce lot."
            for e in eggs_to_create
            if (e.floor, e.column, e.row) in existing_positions
        ]
        if conflicts:
            position_forms = [
                (str(next_id + i).zfill(3), EggPositionForm(request.POST, prefix=f'egg_{i}'))
                for i in range(count)
            ]
            return render(request, self.template_name, {
                'batch': batch, 'position_forms': position_forms,
                'count': count, 'step': 2, 'errors': conflicts,
            })

        try:
            Egg.objects.bulk_create(eggs_to_create)
            messages.success(request, f'✓ {len(eggs_to_create)} oeuf(s) enregistre(s).')
        except Exception as e:
            messages.error(request, f'Erreur : {e}')
        return redirect('incubation:batch-detail', pk=batch.pk)

    def _next_id(self, batch):
        last = batch.eggs.order_by('-identifier').first()
        if last:
            try:
                return int(last.identifier) + 1
            except ValueError:
                pass
        return batch.eggs.count() + 1


class EggCreateView(LoginRequiredMixin, CreateView):
    model = Egg
    form_class = EggForm
    template_name = 'eggs/form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.batch = get_object_or_404(IncubationBatch, pk=kwargs['batch_pk'])

    def _next_identifier(self):
        last = self.batch.eggs.order_by('-identifier').first()
        if last:
            try:
                return str(int(last.identifier) + 1).zfill(3)
            except ValueError:
                pass
        return str(self.batch.eggs.count() + 1).zfill(3)

    def form_valid(self, form):
        form.instance.batch = self.batch
        form.instance.identifier = self._next_identifier()
        messages.success(self.request, f'✓ Œuf {form.instance.identifier} ({form.instance.position_code}) ajouté.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, f'Erreur formulaire : {dict(form.errors)}')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('incubation:batch-detail', kwargs={'pk': self.batch.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['batch'] = self.batch
        ctx['next_identifier'] = self._next_identifier()
        return ctx


class EggUpdateView(LoginRequiredMixin, UpdateView):
    model = Egg
    form_class = EggForm
    template_name = 'eggs/form.html'

    def form_valid(self, form):
        egg = form.save(commit=False)
        # Statut géré manuellement (non inclus dans EggForm)
        new_status = self.request.POST.get('status')
        valid = [s for s, _ in EggStatus.choices]
        if new_status in valid:
            egg.status = new_status
        egg.save()
        messages.success(self.request, f'✓ Œuf {egg.identifier} ({egg.position_code}) mis à jour.')
        return redirect('incubation:batch-detail', pk=egg.batch.pk)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['batch'] = self.object.batch
        ctx['next_identifier'] = self.object.identifier
        ctx['is_update'] = True
        return ctx


class EggUpdateStatusView(LoginRequiredMixin, View):
    """HTMX: mise à jour rapide du statut d'un œuf."""

    def post(self, request, pk):
        egg = get_object_or_404(Egg, pk=pk)
        new_status = request.POST.get('status')
        valid_statuses = [s for s, _ in EggStatus.choices]
        if new_status in valid_statuses:
            egg.status = new_status
            egg.save(update_fields=['status', 'updated_at'])

        # Retourne la ligne HTMX
        html = render_to_string(
            'eggs/partials/egg_row.html',
            {'egg': egg, 'batch': egg.batch},
            request=request
        )
        return HttpResponse(html)


# ─── OBSERVATIONS ─────────────────────────────────────────────────────────────

class ObservationCreateView(LoginRequiredMixin, CreateView):
    model = EggObservation
    form_class = EggObservationForm
    template_name = 'eggs/observation_form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.egg = get_object_or_404(Egg, pk=kwargs['egg_pk'])

    def form_valid(self, form):
        form.instance.egg = self.egg
        response = super().form_valid(form)
        messages.success(self.request, f'Observation enregistrée pour l\'œuf {self.egg.identifier}.')
        return response

    def get_success_url(self):
        return reverse('incubation:batch-detail', kwargs={'pk': self.egg.batch.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['egg'] = self.egg
        ctx['batch'] = self.egg.batch
        ctx['history'] = self.egg.observations.all()
        return ctx


# ─── JOURNAL COUVEUSE ─────────────────────────────────────────────────────────

class IncubatorLogCreateView(LoginRequiredMixin, View):
    """HTMX: ajout d'un log couveuse depuis le détail du lot."""

    def post(self, request, batch_pk):
        batch = get_object_or_404(IncubationBatch, pk=batch_pk)
        form  = IncubatorLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.batch = batch
            log.save()
            # Réponse HTMX partielle
            html = render_to_string(
                'batches/partials/log_item.html',
                {'log': log},
                request=request
            )
            return HttpResponse(html)
        return HttpResponse(status=400)


# ─── HTMX PARTIALS ────────────────────────────────────────────────────────────

class AlertsPartialView(LoginRequiredMixin, View):
    """HTMX: bannière d'alertes, rafraîchie toutes les 60s."""

    def get(self, request):
        active = IncubationBatch.objects.filter(
            status__in=[BatchStatus.ACTIVE, BatchStatus.LOCKDOWN, BatchStatus.HATCHING]
        )
        alerts = []
        for batch in active:
            for alert in batch.today_alerts:
                alerts.append({**alert, 'batch': batch})

        html = render_to_string('components/alerts.html', {'alerts': alerts}, request=request)
        return HttpResponse(html)


class EggGridPartialView(LoginRequiredMixin, View):
    """HTMX: heatmap grille des œufs — affichage par étage."""

    def get(self, request, batch_pk):
        batch = get_object_or_404(IncubationBatch, pk=batch_pk)
        eggs  = batch.eggs.all()

        if not eggs.exists():
            return HttpResponse(
                '<div class="text-center text-[#A09A92] py-12 bg-white rounded-xl border border-[#E5E0D8]">' +
                '<p class="text-4xl mb-3">🥚</p>' +
                '<p class="text-sm">Aucun œuf enregistré. Cliquez sur "＋ Créer les emplacements".</p>' +
                '</div>'
            )

        floors = {}
        for egg in eggs:
            floors.setdefault(egg.floor, {}).setdefault(egg.column, {})[egg.row] = egg

        html = render_to_string('eggs/partials/grid.html', {
            'batch':      batch,
            'floors':     floors,
            'cols':       range(1, 6),
            'rows':       range(1, 7),
            'floor_list': sorted(floors.keys()),
        }, request=request)
        return HttpResponse(html)


class BatchStatsPartialView(LoginRequiredMixin, View):
    """HTMX: statistiques rapides d'un lot."""

    def get(self, request, pk):
        batch = get_object_or_404(IncubationBatch, pk=pk)
        html  = render_to_string('batches/partials/stats.html', {'batch': batch}, request=request)
        return HttpResponse(html)