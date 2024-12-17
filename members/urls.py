from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_page, name='login' ),
    path('dashboard/',views.custom_authenticate, name = "Dashboard" ),
    path('newmember/', views.newmember ,name= "New member"),
    path('newmember/save/',views.save_member,name="Save member" ),
    path('newmember/payment/<int:member_id>/', views.save_payment, name='Payment'),
    path('members/',views.members,name='Members'),
    path('checkin/',views.checkin,name="Checkin" ),
    path('checkin/check-in-out/', views.check_in_out, name='check_in_out'),
    path('checkin/member-history/', views.get_member_history, name='member_history'),
    path('finance/',views.finance,name="Finance" ),

    path('revenue-summary/', views.RevenueAndMembershipView.as_view(), name='revenue-summary')

]