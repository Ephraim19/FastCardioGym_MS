from django.contrib import admin
from .models import Member,CheckInOutRecord,PaymentDetails
# Register your models here.
admin.site.register(Member)
admin.decorators.register(PaymentDetails)
admin.site.register(CheckInOutRecord)