from django import forms

from .models import Client, Job


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'company_name', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['client', 'title', 'status', 'start_date', 'due_date', 'value', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'due_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['client'].queryset = Client.objects.filter(user=user)
        self.fields['start_date'].input_formats = ['%Y-%m-%d']
        self.fields['due_date'].input_formats = ['%Y-%m-%d']
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
