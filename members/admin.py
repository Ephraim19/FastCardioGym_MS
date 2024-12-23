from django.contrib import admin
from .models import Member,CheckInOutRecord,PaymentDetails, Freeze_member
# Register your models here.
admin.site.register(Member)
admin.decorators.register(PaymentDetails)
admin.site.register(CheckInOutRecord)
admin.site.register(Freeze_member)