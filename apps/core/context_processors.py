from django.utils import timezone


def global_context(request):
    """
    Context processor global : alertes du jour injectées dans tous les templates.
    """
    from apps.incubation.models import IncubationBatch, BatchStatus

    today = timezone.now().date()
    alerts = []

    try:
        active_batches = IncubationBatch.objects.filter(
            status__in=[BatchStatus.ACTIVE, BatchStatus.LOCKDOWN, BatchStatus.HATCHING]
        )
        for batch in active_batches:
            for alert in batch.today_alerts:
                alerts.append({**alert, 'batch': batch})
    except Exception:
        pass  # Sécurité si les tables n'existent pas encore

    return {
        'global_alerts': alerts,
        'today': today,
    }
