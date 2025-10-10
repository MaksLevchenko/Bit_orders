from django import forms
from django.core.validators import MinValueValidator


class DealCreateForm(forms.Form):
    # Основные поля
    title = forms.CharField(
        label='Название сделки',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название сделки'
        })
    )

    opportunity = forms.DecimalField(
        label='Сумма сделки',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00'
        })
    )

    CURRENCY_CHOICES = [
        ('RUB', 'Рубли (RUB)'),
        ('USD', 'Доллары (USD)'),
        ('EUR', 'Евро (EUR)'),
    ]

    currency_id = forms.ChoiceField(
        label='Валюта',
        choices=CURRENCY_CHOICES,
        initial='RUB',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Кастомные поля
    DEAL_TYPE_CHOICES = [
        ('SALE', 'Продажа'),
        ('SERVICE', 'Услуга'),
        ('GOODS', 'Товары'),
        ('PROJECT', 'Проект'),
    ]

    deal_type = forms.ChoiceField(
        label='Тип сделки',
        choices=DEAL_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    PRIORITY_CHOICES = [
        ('LOW', 'Низкий'),
        ('MEDIUM', 'Средний'),
        ('HIGH', 'Высокий'),
    ]

    priority = forms.ChoiceField(
        label='Приоритет',
        choices=PRIORITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    contact_email = forms.EmailField(
        label='Email контакта',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )

    contact_phone = forms.CharField(
        label='Телефон контакта',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (XXX) XXX-XX-XX'
        })
    )

    project_deadline = forms.DateField(
        label='Срок выполнения',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    description = forms.CharField(
        label='Описание',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Подробное описание сделки...'
        })
    )

    send_notification = forms.BooleanField(
        label='Отправить уведомление менеджеру',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_opportunity(self):
        opportunity = self.cleaned_data['opportunity']
        if opportunity <= 0:
            raise forms.ValidationError("Сумма сделки должна быть положительной")
        return opportunity