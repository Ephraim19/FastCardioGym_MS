from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_page, name='login' ),
    path('log-in/',views.custom_authenticate, name = "Log in" ),
    path('dashboard/',views.dashboard, name = "Dashboard" ),
    path('newmember/', views.newmember ,name= "New member"),
    path('newmember/save/',views.save_member,name="Save member" ),
    
    path('newmember/payment/<int:member_id>/', views.save_payment, name='Payment'),
    path('members/',views.members,name='Members'),
    path('members/<int:member_id>/',views.member_details,name='Member details'),
    path('member/freeze/<int:member_id>/', views.freeze_member, name='freeze'),
    
    
    path('checkin/',views.checkin,name="Checkin" ),
    path('checkin/check-in-out/', views.check_in_out, name='check_in_out'),
    path('checkin/member-history/', views.get_member_history, name='member_history'),
    
    path('finance/',views.finance,name="Finance" ),
    path('revenue-summary/', views.RevenueAndMembershipView.as_view(), name='revenue-summary'),
    
    path('reminders/',views.reminders, name = "Reminders" ),
    path('reminders/all/',views.all_reminders, name = "All Reminders" ),

    
]