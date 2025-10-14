from django import forms
from products.services import Bitrix24ProductService


class ProductSearchForm(forms.Form):
    """Форма для поиска товара"""
    PRODUCT_CHOICE_METHODS = [
        ('id', 'Поиск по ID'),
        ('name', 'Поиск по названию'),
    ]

    choice_method = forms.ChoiceField(
        choices=PRODUCT_CHOICE_METHODS,
        initial='id',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Способ выбора товара'
    )

    product_id = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ID товара...',
        }),
        label='ID товара'
    )

    product_name = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название товара...',
            'autocomplete': 'off',
        }),
        label='Название товара'
    )

    def clean(self):
        cleaned_data = super().clean()
        choice_method = cleaned_data.get('choice_method')
        product_id = cleaned_data.get('product_id')
        product_name = cleaned_data.get('product_name')

        if choice_method == 'id' and not product_id:
            raise forms.ValidationError("Введите ID товара для поиска по ID")

        if choice_method == 'name' and not product_name:
            raise forms.ValidationError("Введите название товара для поиска по названию")

        return cleaned_data

    def get_product(self):
        """Получить товар на основе выбранного метода"""
        bitrix_service = Bitrix24ProductService()
        choice_method = self.cleaned_data.get('choice_method')

        if choice_method == 'id':
            product_id = self.cleaned_data.get('product_id')
            return bitrix_service.get_product_by_id(product_id)

        elif choice_method == 'name':
            product_name = self.cleaned_data.get('product_name')
            products = bitrix_service.search_products(product_name, limit=1)
            return products[0] if products else None

        return None


class QRGenerationForm(forms.Form):
    """Форма для генерации QR-кода"""
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    product_name = forms.CharField(widget=forms.HiddenInput())
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Дополнительные заметки для этого QR-кода...'
        }),
        label='Заметки'
    )