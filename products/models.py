from django.core.signing import Signer
from django.db import models
import uuid
from django.urls import reverse


class ProductQRCode(models.Model):
    """Модель для хранения сгенерированных QR-кодов"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.IntegerField(verbose_name="ID товара в Bitrix24")
    product_name = models.CharField(max_length=255, verbose_name="Название товара")
    product_image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="URL изображения товара"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        verbose_name = "QR-код товара"
        verbose_name_plural = "QR-коды товаров"
        ordering = ['-created_at']

    def __str__(self):
        return f"QR для {self.product_name} ({self.product_id})"


    def get_signed_token(self):
        """Генерация подписанного токена с использованием Signer"""
        signer = Signer()
        # Подписываем комбинацию product_id и uuid
        signed_value = signer.sign(f"{self.product_id}:{self.id}")
        return signed_value

    def get_absolute_url(self):
        """Получить защищенный URL с подписанным токеном"""
        signed_token = self.get_signed_token()
        return reverse('product_qr_detail', kwargs={'signed_token': signed_token})

    @classmethod
    def verify_token(cls, signed_token):
        """Проверка и расшифровка подписанного токена"""
        try:
            signer = Signer()
            unsigned_value = signer.unsign(signed_token)
            product_id, qr_code_id = unsigned_value.split(':')

            # Проверяем существование QR-кода
            qr_code = cls.objects.get(
                id=qr_code_id,
                product_id=product_id,
                is_active=True
            )
            return qr_code

        except (ValueError, cls.DoesNotExist, Exception):
            return None
