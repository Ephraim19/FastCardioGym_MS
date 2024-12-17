from django.urls import path
from . import views

urlpatterns = [
    path('',views.login, name='login' ),
    path('dashboard/',views.authenticate, name = "Dashboard" ),
    path('dashboard/newmember/', views.newmember ,name= "New member"),
    path('dashboard/newmember/save/',views.save_member,name="Save member" ),
    path('dashboard/newmember/payment/<int:member_id>/', views.save_payment, name='Payment'),
    path('dashboard/members/',views.members,name='Members'),
    path('dashboard/checkin/',views.checkin,name="Checkin" ),
    path('dashboard/checkin/check-in-out/', views.check_in_out, name='check_in_out'),
    path('dashboard/checkin/member-history/', views.get_member_history, name='member_history'),
    path('dashboard/finance/',views.finance,name="Finance" ),

    path('revenue-summary/', views.RevenueAndMembershipView.as_view(), name='revenue-summary')

]