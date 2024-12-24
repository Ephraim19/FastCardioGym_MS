from django.contrib import admin
from .models import Member,CheckInOutRecord,PaymentDetails, Freeze_member, Expense, MemberProgress
# Register your models here.
admin.site.register(Member)
admin.decorators.register(PaymentDetails)
admin.site.register(CheckInOutRecord)
admin.site.register(Freeze_member)
admin.site.register(Expense)
admin.site.register(MemberProgress)
