from django.contrib import admin
from .models import Member,CheckInOutRecord,PaymentDetails, Freeze_member, Expense, MemberProgress, gym_reminder
# Register your models here.
admin.site.register(Member)
admin.site.register(PaymentDetails)
admin.site.register(CheckInOutRecord)
admin.site.register(Freeze_member)
admin.site.register(Expense)
admin.site.register(MemberProgress)
admin.site.register(gym_reminder)

