from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_page, name='login' ),
    path('log-in/',views.custom_authenticate, name = "Log in" ),
    path('log-out/',views.custom_logout, name = "Log out" ),
    
    path('dashboard/',views.dashboard, name = "Dashboard" ),
    path('newmember/', views.newmember ,name= "New member"),
    path('newmember/save/',views.save_member,name="Save member" ),
    
    path('newmember/payment/<int:member_id>/', views.save_payment, name='Payment'),
    path('members/',views.members,name='Members'),
    path('members/<int:member_id>/',views.member_details,name='Member details'),
    
    path('member/freeze/<int:member_id>/', views.freeze_member, name='freeze'),
    path('member/unfreeze/<int:member_id>/', views.unfreeze_member, name='unfreeze'),
    
    path('checkin/',views.checkin,name="Checkin" ),
    path('checkin/check-in-out/', views.check_in_out, name='check_in_out'),
    path('checkin/member-history/', views.get_member_history, name='member_history'),
    
    path('finance/',views.finance,name="Finance" ),
    path('revenue-summary/', views.RevenueAndMembershipView.as_view(), name='revenue-summary'),
    
    path('reminders/',views.reminders, name = "Reminders" ),
    path('reminders/send/', views.send_reminder, name='send_reminder'),
    path('reminders/mark-sent/', views.mark_reminder_sent, name='mark_sent'),
    
    path('expenses/',views.expenses,name="Expenses" ),
    path('expenses/new/',views.new_expense,name="New Expense" ),
    
    
    path('member/<int:member_id>/progress/', views.member_progress, name='member_progress'),
    path('member/<int:member_id>/progress/add/', views.add_progress, name='add_progress'),
    path('member/<int:member_id>/progress/history/', views.get_progress_history, name='progress_history'),
    
    path('reports/',views.reports,name="Reports" ),
    path('reports/download/',views.download_report,name="download report" ),
    
    path('status/', views.member_status, name='member_status'),
    
    path('tasks/', views.tasks, name = "Tasks"),
    path('tasks/add/', views.add_task, name = "add_task" ),
    path('update_task/<int:task_id>/', views.update_task, name='update_task'),
    path('delete_task/<int:task_id>/', views.delete_task, name='delete_task'),
]