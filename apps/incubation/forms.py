from django import forms
from .models import IncubationBatch, Egg, EggObservation, IncubatorLog, CandlingResult, EggStatus

TAILWIND_INPUT  = 'input input-bordered w-full text-sm'
TAILWIND_SELECT = 'select select-bordered w-full text-sm'
TAILWIND_AREA   = 'textarea textarea-bordered w-full text-sm'


class IncubationBatchForm(forms.ModelForm):
    class Meta:
        model  = IncubationBatch
        fields = ['name', 'species', 'breed', 'source', 'entry_date',
                  'total_eggs', 'target_temp', 'target_humidity', 'notes']
        widgets = {
            'name':             forms.TextInput(attrs={'class': TAILWIND_INPUT, 'placeholder': 'ex: Marans Noir Cuivré — Lot 1'}),
            'species':          forms.Select(attrs={'class': TAILWIND_SELECT}),
            'breed':            forms.TextInput(attrs={'class': TAILWIND_INPUT, 'placeholder': 'ex: Marans Noir Cuivré'}),
            'source':           forms.TextInput(attrs={'class': TAILWIND_INPUT, 'placeholder': 'ex: Ferme Dupont, Élevage propre…'}),
            'entry_date':       forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'total_eggs':       forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'min': 1}),
            'target_temp':      forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1', 'placeholder': '37.8'}),
            'target_humidity':  forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '1', 'placeholder': '55'}),
            'notes':            forms.Textarea(attrs={'class': TAILWIND_AREA, 'rows': 3}),
        }


class BatchCompleteForm(forms.ModelForm):
    class Meta:
        model  = IncubationBatch
        fields = ['hatched_count', 'failed_count', 'actual_hatch_date', 'notes']
        widgets = {
            'hatched_count':    forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'min': 0}),
            'failed_count':     forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'min': 0}),
            'actual_hatch_date':forms.DateInput(attrs={'class': TAILWIND_INPUT, 'type': 'date'}),
            'notes':            forms.Textarea(attrs={'class': TAILWIND_AREA, 'rows': 3}),
        }


class EggForm(forms.ModelForm):
    class Meta:
        model  = Egg
        fields = ['floor', 'column', 'row', 'weight_g', 'notes']
        widgets = {
            'floor':    forms.Select(attrs={'class': TAILWIND_SELECT}),
            'column':   forms.Select(attrs={'class': TAILWIND_SELECT}),
            'row':      forms.Select(attrs={'class': TAILWIND_SELECT}),
            'weight_g': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'notes':    forms.Textarea(attrs={'class': TAILWIND_AREA, 'rows': 2}),
        }


class EggBulkCreateForm(forms.Form):
    """
    Saisie individuelle : on entre le nombre d'œufs total,
    puis chaque œuf reçoit son ID (001, 002…) et sa position
    via un formset dynamique.
    """
    count = forms.IntegerField(
        min_value=1, max_value=90,
        label="Nombre d'œufs à enregistrer",
        widget=forms.NumberInput(attrs={
            'class': TAILWIND_INPUT,
            'placeholder': 'ex: 12',
            'min': 1, 'max': 90,
        })
    )


class EggPositionForm(forms.Form):
    """Formulaire pour un seul œuf dans le formset de saisie individuelle."""
    floor = forms.ChoiceField(
        choices=[('1','Étage 1'),('2','Étage 2'),('3','Étage 3')],
        widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full text-sm'})
    )
    column = forms.ChoiceField(
        choices=[('1','A'),('2','B'),('3','C'),('4','D'),('5','E')],
        widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full text-sm'})
    )
    row = forms.ChoiceField(
        choices=[(str(i), str(i)) for i in range(1, 7)],
        widget=forms.Select(attrs={'class': 'select select-bordered select-sm w-full text-sm'})
    )


class EggObservationForm(forms.ModelForm):
    class Meta:
        model  = EggObservation
        fields = ['candling_number', 'result', 'notes', 'observed_by']
        widgets = {
            'candling_number': forms.Select(attrs={'class': TAILWIND_SELECT}),
            'result':          forms.Select(attrs={'class': TAILWIND_SELECT}),
            'notes':           forms.Textarea(attrs={'class': TAILWIND_AREA, 'rows': 3}),
            'observed_by':     forms.TextInput(attrs={'class': TAILWIND_INPUT}),
        }

    def save(self, commit=True):
        obs = super().save(commit=commit)
        # Met à jour le statut de l'œuf selon le résultat
        if commit:
            status_map = {
                CandlingResult.FERTILE:   EggStatus.FERTILE,
                CandlingResult.CLEAR:     EggStatus.CLEAR,
                CandlingResult.DEAD:      EggStatus.DEAD_EMBRYO,
                CandlingResult.READY:     EggStatus.FERTILE,
            }
            new_status = status_map.get(obs.result)
            if new_status:
                obs.egg.status = new_status
                obs.egg.save(update_fields=['status', 'updated_at'])
        return obs


class IncubatorLogForm(forms.ModelForm):
    class Meta:
        model  = IncubatorLog
        fields = ['temperature', 'humidity', 'co2_ppm', 'event', 'notes']
        widgets = {
            'temperature': forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '0.1'}),
            'humidity':    forms.NumberInput(attrs={'class': TAILWIND_INPUT, 'step': '1'}),
            'co2_ppm':     forms.NumberInput(attrs={'class': TAILWIND_INPUT}),
            'event':       forms.TextInput(attrs={'class': TAILWIND_INPUT}),
            'notes':       forms.Textarea(attrs={'class': TAILWIND_AREA, 'rows': 2}),
        }