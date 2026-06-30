from django import forms

from .models import Expense, Income


class BaseFinanceForm(forms.ModelForm):
    input_class = 'form-control'

    def _apply_widget_classes(self):
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', self.input_class)


class IncomeForm(BaseFinanceForm):
    source_name = forms.CharField(
        label='Source',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Income
        fields = ['source_name', 'amount', 'date_received', 'description']
        widgets = {
            'date_received': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_widget_classes()
        self.fields['date_received'].input_formats = ['%Y-%m-%d']
        if self.instance.pk:
            self.fields['source_name'].initial = self.instance.source.name


class ExpenseForm(BaseFinanceForm):
    category_name = forms.CharField(
        label='Category',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Expense
        fields = ['category_name', 'amount', 'date_paid', 'description']
        widgets = {
            'date_paid': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_widget_classes()
        self.fields['date_paid'].input_formats = ['%Y-%m-%d']
        if self.instance.pk:
            self.fields['category_name'].initial = self.instance.category.name
