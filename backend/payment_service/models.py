import uuid
from django.db import models


class StudioPayment(models.Model):
    """
    Модель для зберігання інформації про платіж за оренду.
    """
    # Використовуємо UUID як order_id для LiqPay
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Сума до сплати в UAH")
    description = models.CharField(max_length=255, default="Передоплата за оренду студії")
    is_paid = models.BooleanField(default=False, verbose_name="Оплачено")
    created_at = models.DateTimeField(auto_now_add=True)

    # Поля для відповіді від LiqPay
    liqpay_status = models.CharField(max_length=50, blank=True, null=True,
                                     help_text="Статус від LiqPay (напр. 'success', 'sandbox')")

    # Поля для відповіді від Checkbox
    checkbox_receipt_id = models.CharField(max_length=255, blank=True, null=True,
                                           help_text="ID чека в системі Checkbox")
    checkbox_fiscal_code = models.CharField(max_length=255, blank=True, null=True, help_text="Фіскальний номер чека")
    checkbox_status = models.CharField(max_length=50, blank=True, null=True,
                                       help_text="Статус чека в Checkbox (напр. 'DONE')")

    def __str__(self):
        return f"Платіж {self.id} на суму {self.amount} UAH"

    class Meta:
        verbose_name = "Платіж за студію"
        verbose_name_plural = "Платежі за студію"
