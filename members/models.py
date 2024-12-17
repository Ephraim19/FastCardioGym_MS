from django.db import models
from django.utils import timezone
# Create your models here.

class Member(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    additional_info = models.TextField(blank=True,null=True)


    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class PaymentDetails(models.Model):
    # Payment plan options
    PLAN_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('student', 'Student Package'),
    ]
    
    # Fields for the payment details
    member = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='payments', verbose_name="Member")
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, verbose_name="Payment Plan")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount Paid")
    payment_date = models.DateField(default=timezone.now, verbose_name="Payment Date")
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="Transaction ID")
    # notes = models.TextField(blank=True, null=True, verbose_name="Additional Notes")

    
    # Metadata for admin interface
    class Meta:
        verbose_name = "Payment Detail"
        verbose_name_plural = "Payment Details"
        ordering = ['-payment_date']

    # String representation for the model
    def __str__(self):
        return f"{self.member} - {self.plan} - {self.payment_date}"
    
class CheckInOutRecord(models.Model):
    """
    Tracks check-in and check-out records for members
    """
    ACTIONS = [
        ('check_in', 'Check In'),
        ('check_out', 'Check Out')
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='CheckinOut')
    action = models.CharField(max_length=10, choices=ACTIONS)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.member} - {self.get_action_display()} at {self.timestamp}"
    
