from django.contrib import admin
from .models import IncubationBatch, Egg, EggObservation, IncubatorLog


class EggInline(admin.TabularInline):
    model = Egg
    extra = 0
    fields = ['identifier', 'position_label', 'status', 'weight_g', 'notes']
    readonly_fields = ['created_at']


class IncubatorLogInline(admin.TabularInline):
    model = IncubatorLog
    extra = 0
    fields = ['logged_at', 'temperature', 'humidity', 'event']


@admin.register(IncubationBatch)
class IncubationBatchAdmin(admin.ModelAdmin):
    list_display  = ['name', 'species', 'entry_date', 'total_eggs', 'status', 'hatch_rate_display']
    list_filter   = ['status', 'species']
    search_fields = ['name', 'breed', 'source']
    inlines       = [EggInline, IncubatorLogInline]
    readonly_fields = [
        'candling_1_date', 'candling_2_date', 'candling_3_date',
        'lockdown_date', 'estimated_hatch_date', 'incubation_day',
        'hatch_rate', 'fertility_rate', 'embryo_mortality_rate',
    ]
    fieldsets = (
        ('Identification', {
            'fields': ('name', 'species', 'breed', 'source', 'status')
        }),
        ('Incubation', {
            'fields': ('entry_date', 'total_eggs', 'target_temp', 'target_humidity')
        }),
        ('Dates calculées', {
            'fields': ('candling_1_date', 'candling_2_date', 'candling_3_date',
                       'lockdown_date', 'estimated_hatch_date', 'incubation_day'),
            'classes': ('collapse',),
        }),
        ('Résultats', {
            'fields': ('hatched_count', 'failed_count', 'actual_hatch_date',
                       'hatch_rate', 'fertility_rate', 'embryo_mortality_rate')
        }),
        ('Notes', {'fields': ('notes',)}),
    )

    def hatch_rate_display(self, obj):
        r = obj.hatch_rate
        return f"{r}%" if r is not None else "—"
    hatch_rate_display.short_description = "Taux d'éclosion"


class EggObservationInline(admin.TabularInline):
    model = EggObservation
    extra = 0
    fields = ['candling_number', 'result', 'notes', 'observed_at']


@admin.register(Egg)
class EggAdmin(admin.ModelAdmin):
    list_display  = ['identifier', 'batch', 'position_display', 'status']
    list_filter   = ['status', 'batch']
    search_fields = ['identifier', 'batch__name']
    inlines       = [EggObservationInline]


@admin.register(EggObservation)
class EggObservationAdmin(admin.ModelAdmin):
    list_display = ['egg', 'candling_number', 'result', 'observed_at']
    list_filter  = ['result', 'candling_number']


@admin.register(IncubatorLog)
class IncubatorLogAdmin(admin.ModelAdmin):
    list_display = ['batch', 'logged_at', 'temperature', 'humidity', 'event']
    list_filter  = ['batch']
