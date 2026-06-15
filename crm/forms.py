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
        fields = ['client', 'title', 'status', 'value', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['client'].queryset = Client.objects.filter(user=user)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
