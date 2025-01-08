from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

class Member(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    date_joined = models.DateTimeField(auto_now_add=True)
    membership_expiry = models.DateField(null=True, blank=True, help_text="Date when the membership expires")
    is_active = models.BooleanField(default=False)
    is_frozen = models.BooleanField(default=False)
    additional_info = models.TextField(blank=True,null=True)
    gender = models.CharField(max_length= 6)
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Positive balance indicates credit, negative indicates debt"
    )
    balance_due_date = models.DateField(null = True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    

    
class PaymentDetails(models.Model):
    # Payment plan options
    PLAN_CHOICES = [
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannually', 'Biannually'),
        ('annually', 'Annually'),
        ('student', 'Student Package'),
        ('complete', 'Complete Payment'),
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
    

class gym_reminder(models.Model):
    
    REMINDER_TYPES = [
        ('attendance', 'Attendance Reminder'),
        ('expiry', 'Subscription Expiry Reminder'),
    ]
    
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='reminders')
    reminder = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=20, choices=REMINDER_TYPES)
    is_sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.member} - {self.reminder}"
    
    
class Freeze_member(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    frozen_date = models.DateField(auto_now_add=True)
    unfrozen_date = models.DateField(null=True, blank=True)
    freeze_time = models.IntegerField(null=True, blank=True)  # Store the total days frozen
    def __str__(self):
        return f"{self.member.first_name}"
    

    

class Expense(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expense_type = models.CharField(max_length=20 )
    details = models.TextField()
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.expense_type}-{self.amount} 0n {self.date}"
    
class MemberProgress(models.Model):
    member = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='progress')
    date = models.DateField(auto_now_add=True)
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    body_fat = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    muscle_mass = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    chest = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    waist = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Member Progress"
        verbose_name_plural = "Member Progress Records"

    def __str__(self):
        return f"{self.member} - Progress on {self.date}"
    
    
class Task(models.Model):
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    due_date = models.DateField()
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']