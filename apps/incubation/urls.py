from django.urls import path
from . import views

app_name = 'incubation'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Lots
    path('lots/',                            views.BatchListView.as_view(),    name='batch-list'),
    path('lots/nouveau/',                    views.BatchCreateView.as_view(),   name='batch-create'),
    path('lots/<int:pk>/',                   views.BatchDetailView.as_view(),   name='batch-detail'),
    path('lots/<int:pk>/modifier/',          views.BatchUpdateView.as_view(),   name='batch-update'),
    path('lots/<int:pk>/terminer/',          views.BatchCompleteView.as_view(), name='batch-complete'),
    path('lots/<int:pk>/supprimer/',         views.BatchDeleteView.as_view(),   name='batch-delete'),

    # Œufs
    path('lots/<int:batch_pk>/oeufs/masse/', views.EggBulkCreateView.as_view(), name='egg-bulk'),
    path('lots/<int:batch_pk>/oeufs/add/',   views.EggCreateView.as_view(),     name='egg-create'),
    path('oeufs/<int:pk>/modifier/',         views.EggUpdateView.as_view(),      name='egg-update'),
    path('oeufs/<int:pk>/statut/',           views.EggUpdateStatusView.as_view(), name='egg-status'),

    # Observations
    path('oeufs/<int:egg_pk>/observer/',     views.ObservationCreateView.as_view(), name='observation-create'),

    # Journal couveuse
    path('lots/<int:batch_pk>/log/',         views.IncubatorLogCreateView.as_view(), name='log-create'),

    # HTMX partials
    path('htmx/alertes/',                    views.AlertsPartialView.as_view(),     name='htmx-alerts'),
    path('htmx/lots/<int:batch_pk>/grille/', views.EggGridPartialView.as_view(),    name='htmx-grid'),
    path('htmx/lots/<int:pk>/stats/',        views.BatchStatsPartialView.as_view(), name='htmx-stats'),
]