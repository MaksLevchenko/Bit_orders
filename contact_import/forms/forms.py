
from django import forms


class ImportContactsForm(forms.Form):
    file = forms.FileField(
        label='Файл для импорта',
        help_text='Поддерживаемые форматы: CSV, XLSX'
    )

    FILE_TYPES = [
        ('csv', 'CSV'),
        ('xlsx', 'XLSX'),
    ]

    file_type = forms.ChoiceField(
        choices=FILE_TYPES,
        label='Тип файла'
    )


class ExportContactsForm(forms.Form):
    FILE_TYPES = [
        ('csv', 'CSV'),
        ('xlsx', 'XLSX'),
    ]

    file_type = forms.ChoiceField(
        choices=FILE_TYPES,
        label='Формат экспорта'
    )

    last_days = forms.IntegerField(
        required=False,
        label='За последние N дней',
        min_value=1,
        help_text='Оставьте пустым для экспорта всех контактов'
    )

    company = forms.CharField(
        required=False,
        label='Компания',
        max_length=255,
        help_text='Начните вводить название компании',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Начните вводить название компании...',
            'autocomplete': 'off',
            'id': 'company-autocomplete'
        })
    )