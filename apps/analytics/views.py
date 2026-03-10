import json
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Avg, Q
from apps.incubation.models import IncubationBatch, Egg, EggStatus, BatchStatus, SpeciesChoices


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        completed = IncubationBatch.objects.filter(
            status=BatchStatus.COMPLETED,
            hatched_count__isnull=False
        ).order_by('entry_date')

        # ── Graphique évolution taux d'éclosion ──
        hatch_chart = json.dumps([
            {
                'name':       b.name[:20],
                'date':       b.entry_date.isoformat(),
                'hatch_rate': b.hatch_rate or 0,
                'fertility':  b.fertility_rate or 0,
                'total':      b.total_eggs,
                'hatched':    b.hatched_count or 0,
            }
            for b in completed
        ])

        # ── Statistiques globales ──
        hatch_rates = [b.hatch_rate for b in completed if b.hatch_rate is not None]
        avg_hatch   = round(sum(hatch_rates) / len(hatch_rates), 1) if hatch_rates else 0
        best_batch  = max(completed, key=lambda b: b.hatch_rate or 0, default=None)
        worst_batch = min(completed, key=lambda b: b.hatch_rate or 0, default=None)

        # ── Analyse par espèce ──
        species_data = {}
        for batch in completed:
            s = batch.get_species_display()
            if s not in species_data:
                species_data[s] = {'count': 0, 'rates': [], 'total_eggs': 0, 'total_hatched': 0}
            species_data[s]['count']        += 1
            species_data[s]['total_eggs']   += batch.total_eggs
            species_data[s]['total_hatched']+= batch.hatched_count or 0
            if batch.hatch_rate:
                species_data[s]['rates'].append(batch.hatch_rate)
        for s in species_data:
            rates = species_data[s]['rates']
            species_data[s]['avg_rate'] = round(sum(rates) / len(rates), 1) if rates else 0

        # ── Analyse causes d'échec ──
        failure_data = {
            'clear':       Egg.objects.filter(status=EggStatus.CLEAR).count(),
            'dead_embryo': Egg.objects.filter(status=EggStatus.DEAD_EMBRYO).count(),
            'cracked':     Egg.objects.filter(status=EggStatus.CRACKED).count(),
            'failed':      Egg.objects.filter(status=EggStatus.FAILED).count(),
        }
        failure_json = json.dumps([
            {'label': 'Clair (infertile)', 'value': failure_data['clear'],       'color': '#9CA3AF'},
            {'label': 'Mort embryonnaire', 'value': failure_data['dead_embryo'], 'color': '#EF4444'},
            {'label': 'Fissuré',           'value': failure_data['cracked'],     'color': '#F97316'},
            {'label': 'Échoué éclosion',   'value': failure_data['failed'],      'color': '#DC2626'},
        ])

        # ══ STATISTIQUES PAR EMPLACEMENT ══════════════════════════════════════

        col_labels = {1:'A', 2:'B', 3:'C', 4:'D', 5:'E'}

        def position_stats(eggs_qs):
            """Calcule taux d'éclosion et de mortalité pour un groupe d'œufs."""
            total   = eggs_qs.exclude(status=EggStatus.REMOVED).count()
            hatched = eggs_qs.filter(status=EggStatus.HATCHED).count()
            dead    = eggs_qs.filter(status=EggStatus.DEAD_EMBRYO).count()
            clear   = eggs_qs.filter(status=EggStatus.CLEAR).count()
            fertile = eggs_qs.filter(status__in=[
                EggStatus.FERTILE, EggStatus.HATCHED,
                EggStatus.FAILED, EggStatus.DEAD_EMBRYO
            ]).count()
            return {
                'total':        total,
                'hatched':      hatched,
                'dead':         dead,
                'clear':        clear,
                'fertile':      fertile,
                'hatch_rate':   round(hatched / total * 100, 1) if total else 0,
                'mort_rate':    round(dead / fertile * 100, 1) if fertile else 0,
                'fertility_rate': round(fertile / total * 100, 1) if total else 0,
            }

        all_eggs = Egg.objects.all()

        # — Stats par étage —
        floor_stats = []
        for floor in [1, 2, 3]:
            s = position_stats(all_eggs.filter(floor=floor))
            s['label'] = f'Étage {floor}'
            s['floor'] = floor
            floor_stats.append(s)

        # — Stats par colonne —
        col_stats = []
        for col_num, col_letter in col_labels.items():
            s = position_stats(all_eggs.filter(column=col_num))
            s['label'] = f'Colonne {col_letter}'
            s['col']   = col_letter
            col_stats.append(s)

        # — Stats par ligne —
        row_stats = []
        for row in range(1, 7):
            s = position_stats(all_eggs.filter(row=row))
            s['label'] = f'Ligne {row}'
            s['row']   = row
            row_stats.append(s)

        # — Meilleurs et pires emplacements (parmi ceux ayant au moins 5 œufs) —
        slot_stats = []
        for floor in [1, 2, 3]:
            for col in range(1, 6):
                for row in range(1, 7):
                    s = position_stats(all_eggs.filter(floor=floor, column=col, row=row))
                    if s['total'] >= 3:  # min 3 passages sur cet emplacement
                        s['code'] = f"E{floor}{col_labels[col]}{row}"
                        slot_stats.append(s)

        slot_stats_sorted = sorted(slot_stats, key=lambda x: x['hatch_rate'], reverse=True)
        best_slots  = slot_stats_sorted[:5]
        worst_slots = [s for s in slot_stats_sorted if s['total'] >= 3][-5:][::-1]

        # — Heatmap données pour Chart.js (grille 5×6 par étage) —
        heatmap_data = {}
        for floor in [1, 2, 3]:
            grid = []
            for col in range(1, 6):
                for row in range(1, 7):
                    s = position_stats(all_eggs.filter(floor=floor, column=col, row=row))
                    grid.append({
                        'x': col - 1,   # 0-4
                        'y': row - 1,   # 0-5
                        'v': s['hatch_rate'],
                        'total': s['total'],
                        'code': f"E{floor}{col_labels[col]}{row}",
                    })
            heatmap_data[floor] = grid

        # — Emplacement le plus fiable (faible mortalité embryonnaire) —
        reliable_slots = sorted(
            [s for s in slot_stats if s['fertile'] >= 2],
            key=lambda x: x['mort_rate']
        )[:5]

        ctx.update({
            'completed_batches': completed,
            'hatch_chart':       hatch_chart,
            'failure_json':      failure_json,
            'total_batches':     completed.count(),
            'total_eggs':        sum(b.total_eggs for b in completed),
            'total_hatched':     sum(b.hatched_count or 0 for b in completed),
            'avg_hatch_rate':    avg_hatch,
            'best_batch':        best_batch,
            'worst_batch':       worst_batch,
            'species_data':      species_data,
            # Stats emplacements
            'floor_stats':       floor_stats,
            'col_stats':         col_stats,
            'row_stats':         row_stats,
            'best_slots':        best_slots,
            'worst_slots':       worst_slots,
            'reliable_slots':    reliable_slots,
            'heatmap_json':      json.dumps(heatmap_data),
            'total_eggs_all':    all_eggs.count(),
            'hatched_all':       all_eggs.filter(status=EggStatus.HATCHED).count(),
        })
        return ctx