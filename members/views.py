from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from .models import Member, PaymentDetails, CheckInOutRecord, gym_reminder, Freeze_member, Expense, MemberProgress, Task
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Max, Min, F, Q, ExpressionWrapper, FloatField
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import timedelta,datetime
from django.db.models.functions import TruncMonth, ExtractHour, ExtractWeekDay
from django.db.models import Count, Q, Max, Subquery, OuterRef, Avg, Min
from django.contrib.auth.decorators import login_required
import json
from decimal import Decimal
from .fastcardio_report import create_fastcardio_report
from functools import wraps

def allowed_users_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        allowed_users = ['FastcardioAdmin']
        if request.user.username not in allowed_users:
            # messages.error(request, 'Access denied.')
            return redirect('New Expense')
        return view_func(request, *args, **kwargs)
    return wrapper

def allowed_users_only_1(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        allowed_users = ['FastcardioAdmin']
        if request.user.username not in allowed_users:
            messages.error(request, 'Access denied.')
            return redirect('Dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


PLAN_PRICES = {
    'daily': 500,
    'monthly': 4000,
    'quarterly': 10500,
    'biannually': 21000,
    'annually': 42000,
    'student': 3000
}

def login_page(request):
    return render(request, 'index.html')

def custom_authenticate(request):
    if request.method != "POST":
        return redirect('login')
        
    username = request.POST.get('username')
    print(username)
    password = request.POST.get('password')
    
    if not username or not password:
        messages.error(request, 'Username and password are required.')
        return redirect('login')
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None and user.is_superuser:
        login(request, user)
        return redirect('Dashboard')
    
    messages.error(request, 'Invalid credentials or insufficient permissions.')
    return redirect('login')


def custom_logout(request):
    logout(request)
    return redirect('login') 
def dashboard(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    one_weeks_ago = today - timedelta(days=7)

    # Deactivate members with overdue balance
    overdue_members = Member.objects.filter(
        balance_due_date__lt=today,
        balance__lt=0,
        is_active=True
    )
    overdue_members.update(is_active=False)
    
    # All Members count
    all_members = Member.objects.count()
    new_members_last_month = Member.objects.filter(
        date_joined__date__gte=thirty_days_ago
    ).count()

    # Check and update expired memberships based on latest payment
    daily_expiry = today - timedelta(days=0)
    monthly_expiry = today - timedelta(days=30)
    quarterly_expiry = today - timedelta(days=90)
    biannual_expiry = today - timedelta(days=182)
    yearly_expiry = today - timedelta(days=365)
    student_expiry = today - timedelta(days=30)

    # Get latest payment for each member
    latest_payments_subquery = PaymentDetails.objects.filter(
        member=OuterRef('pk')
    ).order_by('-payment_date')[:1]

    # Find expired members based on their latest payment
    expired_members = Member.objects.annotate(
        latest_payment_date=Subquery(latest_payments_subquery.values('payment_date')),
        latest_plan=Subquery(latest_payments_subquery.values('plan'))
    ).filter(
        Q(latest_plan='daily', latest_payment_date__lt=daily_expiry) |
        Q(latest_plan='monthly', latest_payment_date__lt=monthly_expiry) |
        Q(latest_plan='quarterly', latest_payment_date__lt=quarterly_expiry) |
        Q(latest_plan='biannually', latest_payment_date__lt=biannual_expiry) |
        Q(latest_plan='annually', latest_payment_date__lt=yearly_expiry) |
        Q(latest_plan='student', latest_payment_date__lt=student_expiry)
    )

    # Update expired members to inactive
    expired_members.update(is_active=False)
    expired_count = expired_members.count()

    # Active Members (not frozen and is_active)
    active_members = Member.objects.filter(
        is_active=True,
        is_frozen=False
    ).count()

    # New members this month
    new_members = Member.objects.filter(
        date_joined__date__gte=thirty_days_ago
    ).count()
    new_members_prev_month = Member.objects.filter(
        date_joined__date__gte=thirty_days_ago - timedelta(days=30),
        date_joined__date__lt=thirty_days_ago
    ).count()
    new_members_change = new_members - new_members_prev_month

    # Active Check-ins today
    active_checkins = CheckInOutRecord.objects.filter(
        action='check_in',
        timestamp__date=today
    ).count()

    # Frozen Members
    frozen_members = Member.objects.filter(is_frozen=True).count()

    # Not Attending (no check-ins in last week)
    attending_member_ids = CheckInOutRecord.objects.filter(
        action='check_in',
        timestamp__date__gte=one_weeks_ago
    ).values_list('member_id', flat=True).distinct()

    not_attending = Member.objects.exclude(
        id__in=attending_member_ids
    ).filter(is_active=True).count()

    # Add overdue members to context
    context = {
        'all_members': {
            'value': all_members,
            'change': f'+{new_members_last_month} this month'
        },
        'active_members': {
            'value': active_members,
            'change': f'+{new_members_last_month} this month'
        },
        'new_members': {
            'value': new_members,
            'change': f'+{new_members_change} from last month'
        },
        'active_checkins': {
            'value': active_checkins,
            'change': 'Today'
        },
        'expired_members': {
            'value': expired_count + overdue_members.count(),
            'change': 'Action needed'
        },
        'frozen_members': {
            'value': frozen_members,
            'change': 'On temporary hold'
        },
        'not_attending': {
            'value': not_attending,
            'change': '1 week inactive'
        }
    }

    return render(request, 'dashboard.html', context)

def newmember(request):
    return render(request, 'newmember.html')

def save_member(request):
    if request.method == "POST":
        f_name = request.POST.get('fname')
        l_name = request.POST.get('lname')
        phone = request.POST.get('phone')
        info = request.POST.get('info')
        gender = request.POST.get('gender')
        
        #Check if member already exists
        member_exists = Member.objects.filter(phone_number=phone).exists()
        if member_exists:
            messages.error(request, 'Member with this phone number already exists. Please search for the member and update their records.')
            return redirect('Members')
        
        # Create and save the member
        member = Member.objects.create(
            first_name=f_name,
            last_name=l_name,
            phone_number=phone,
            additional_info=info,
            gender = gender
        )
        print(f"Saved: {member}")
        
        # Option 1: Pass member ID through session
        request.session['new_member_id'] = member.id
        
        # Option 2: Redirect with member ID as parameter
        return redirect("Payment", member_id=member.id)
    
    return HttpResponse("Error saving member")


def save_payment(request, member_id=None):
    if member_id is None:
        member_id = request.session.get('new_member_id')
    
    try:
        member = get_object_or_404(Member, id=member_id)
    except:
        return HttpResponse("Member not found")
    
    if request.method == "POST":
        if 'new_member_id' in request.session:
            del request.session['new_member_id']
        
        plan = request.POST.get('plan')
        amount = Decimal(request.POST.get('amount'))
        transaction_id = request.POST.get('code')
        balance_due_date = request.POST.get('due_date')
        
        expected_amount = PLAN_PRICES.get(plan)
        
        if expected_amount is None and plan != 'complete':
            messages.error(request, 'Invalid plan selected!')
            return redirect("Members")
        
        PaymentDetails.objects.create(
            member=member,
            plan=plan,
            amount=amount,
            transaction_id=transaction_id
        )
        
        if plan != 'complete':
            expiry_periods = {
                'daily': timedelta(days=1),
                'monthly': timedelta(days=30),
                'quarterly': timedelta(days=90),
                'biannually': timedelta(days=182),
                'annually': timedelta(days=365),
                'student': timedelta(days=30)
            }
            
            current_date = timezone.now().date()
            start_date = max(current_date, member.membership_expiry or current_date)
            new_expiry = start_date + expiry_periods.get(plan, timedelta(0))
            member.membership_expiry = new_expiry
        
        if plan == 'complete':
            difference = amount + member.balance
            member.balance = difference
            if difference >= 0:
                member.membership_expiry = ''
        else:
            difference = amount - expected_amount
            member.balance = difference
            
            # Set balance due date if there's an underpayment
            if difference < 0 and balance_due_date:
                member.balance_due_date = balance_due_date
            elif difference >= 0:
                member.balance_due_date = None
        
        if plan != 'complete':
            if amount >= expected_amount or (amount + member.balance >= expected_amount):
                member.is_active = True
                if difference > 0:
                    messages.success(request, 
                        f'Overpayment of {difference:.2f} recorded. Current balance: {member.balance:.2f}')
            else:
                member.is_active = True
                messages.warning(request,
                    f'Underpayment of {abs(difference):.2f} due by {balance_due_date}. Current balance: {member.balance:.2f}.')
        else:
            member.is_active = True
            messages.success(request, f'Complete payment of {amount:.2f} recorded. Balance: {member.balance:.2f}')
        
        member.save()
        
        messages.success(request, 
            f'Payment saved successfully for {member}! '
            f'Membership is active until {member.membership_expiry.strftime("%Y-%m-%d")}.')
        
        return redirect("Members")
    
    # Render payment form with member context
    return render(request, 'payment.html', {'member': member})

def calculate_expiry_date(payment_date, plan):
    if not payment_date:
        return None
    
    expiry_periods = {
        'daily': timedelta(days=1),
        'monthly': timedelta(days=30),
        'quarterly': timedelta(days=90),
        'biannually': timedelta(days=180),
        'annually': timedelta(days=365),
        'student': timedelta(days=30),  # Assuming student package is monthly
    }
    
    return payment_date + expiry_periods.get(plan, timedelta(0))

def calculate_expiry_date(payment_date, plan):
    if plan == 'daily':
        return payment_date + timedelta(days=1)
    elif plan == 'monthly':
        return payment_date + timedelta(days=30)
    elif plan == 'quarterly':
        return payment_date + timedelta(days=90)
    elif plan == 'biannually':
        return payment_date + timedelta(days=182)
    elif plan == 'annually':
        return payment_date + timedelta(days=365)
    elif plan == 'student':
        return payment_date + timedelta(days=30)  
    
    return None


def member_details(request, member_id):
    """
    Detailed view function for individual member information, including payment history,
    check-in records, membership status, and progress tracking.
    """
    member = get_object_or_404(Member, pk=member_id)
    today = timezone.now().date()

    # Payment Information
    recent_payments = PaymentDetails.objects.filter(member=member).order_by('-payment_date')[:5]
    latest_payment = recent_payments.first()
    total_paid = PaymentDetails.objects.filter(member=member).aggregate(total=Sum('amount'))['total'] or 0

    # Membership Status Calculation
    membership_status = calculate_membership_status(member, today)

    # Check-in Statistics
    checkin_stats = get_checkin_statistics(member)

    # Progress Tracking
    latest_progress = MemberProgress.objects.filter(member=member).order_by('-date').first()
    progress_history = MemberProgress.objects.filter(member=member).order_by('-date')[:5]

    # Freeze History
    freeze_history = Freeze_member.objects.filter(member=member).order_by('-frozen_date')
    current_freeze = freeze_history.filter(unfrozen_date__isnull=True).first()

    # Balance Information
    balance_info = get_balance_status(member.balance)
    print(bool(current_freeze))
    context = {
        # Member Basic Info
        'member': member,
        'membership_status': membership_status['status'],
        'days_left': membership_status['days_left'],
        'expiry_date': member.membership_expiry,
        
        # Payment Information
        'recent_payments': recent_payments,
        'latest_payment': latest_payment,
        'current_plan': latest_payment.plan if latest_payment else "No active plan",
        'total_paid': total_paid,
        
        # Check-in Information
        'total_checkins': checkin_stats['total'],
        'checkins_this_month': checkin_stats['monthly'],
        'recent_checkins': checkin_stats['recent'],
        'last_checkin': checkin_stats['last'],
        'attendance_rate': checkin_stats['attendance_rate'],
        
        # Progress Information
        'latest_progress': latest_progress,
        'progress_history': progress_history,
        
        # Freeze Information
        'is_currently_frozen': bool(current_freeze),
        'freeze_history': freeze_history,
        'current_freeze': current_freeze,
        
        # Balance Information
        'balance': member.balance,
        'balance_status': balance_info['status'],
        'balance_message': balance_info['message']
    }

    return render(request, 'member_details.html', context)

def calculate_membership_status(member, today):
    """
    Calculate detailed membership status and days remaining
    """
    if member.is_frozen:
        return {
            'status': 'Inactive',
            'days_left': None
        }
    
    if not member.membership_expiry:
        return {
            'status': 'Inactive',
            'days_left': None
        }

    days_left = (member.membership_expiry - today).days

    if member.is_active:
        status = 'Active'
    else:
        status = 'Inactive'

    return {
        'status': status,
        'days_left': days_left
    }

def get_checkin_statistics(member):
    """
    Calculate comprehensive check-in statistics for the member
    """
    today = timezone.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    checkins = CheckInOutRecord.objects.filter(member=member, action='check_in')
    monthly_checkins = checkins.filter(timestamp__gte=first_day_of_month)
    
    # Calculate attendance rate (assuming 30 days)
    total_days = (today.date() - member.date_joined.date()).days
    attendance_rate = (checkins.count() / total_days * 100) if total_days > 0 else 0

    return {
        'total': checkins.count(),
        'monthly': monthly_checkins.count(),
        'recent': checkins.order_by('-timestamp')[:5],
        'last': checkins.order_by('-timestamp').first(),
        'attendance_rate': round(attendance_rate, 1)
    }

def get_balance_status(balance):
    """
    Generate balance status and appropriate message
    """
    if balance > 0:
        return {
            'status': 'Credit',
            'message': 'Member has credit balance'
        }
    elif balance < 0:
        return {
            'status': 'Debt',
            'message': 'Member has outstanding balance'
        }
    return {
        'status': 'Neutral',
        'message': 'Balance is cleared'
    }
def checkin(request):

    # Get recent check-in/out records (last 10)
    recent_records = CheckInOutRecord.objects.select_related('member').all()[:20]
    return render(request,"Checkin.html",{'recent_records': recent_records })
    

@csrf_exempt
@require_http_methods(["POST"])
def check_in_out(request):
    """
    Handle check-in and check-out actions via AJAX with member status validation
    """
    try:
        # Get member ID from request
        member_id = request.POST.get('id', '').strip()
        action = request.POST.get('action', '').strip()

        # Validate inputs
        if not member_id:
            return JsonResponse({
                'status': 'error', 
                'message': 'Please enter a Member ID'
            }, status=400)

        # Try to get the member
        try:
            member = Member.objects.get(phone_number=member_id)
            
            # Check if member is frozen
            if member.is_frozen:
                return JsonResponse({
                    'status': 'error',
                    'message': 'This membership is currently frozen. Please contact staff.'
                }, status=400)
            
            # Check if member is inactive
            if not member.is_active:
                return JsonResponse({
                    'status': 'error',
                    'message': 'This membership is inactive. Please renew your membership.'
                }, status=400)
            
            # Check membership expiry
            latest_payment = PaymentDetails.objects.filter(member=member).order_by('-payment_date').first()
            
            if latest_payment:
                # Calculate expiry based on plan
                if latest_payment.plan == 'daily':
                    expiry_date = latest_payment.payment_date + timedelta(days=1)
                elif latest_payment.plan == 'monthly':
                    expiry_date = latest_payment.payment_date + timedelta(days=30)
                elif latest_payment.plan == 'quarterly':
                    expiry_date = latest_payment.payment_date + timedelta(days=90)
                elif latest_payment.plan == 'biannually':
                    expiry_date = latest_payment.payment_date + timedelta(days=182)
                elif latest_payment.plan == 'annually':
                    expiry_date = latest_payment.payment_date + timedelta(days=365)
                else:  # student package
                    expiry_date = latest_payment.payment_date + timedelta(days=30)
                
                # Check if membership has expired
                if timezone.now().date() > expiry_date:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Your membership has expired. Please renew to continue.'
                    }, status=400)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No active membership found. Please make a payment.'
                }, status=400)

        except Member.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Member not found. Please check the phone number.'
            }, status=404)

        # Create check-in/out record
        record = CheckInOutRecord.objects.create(
            member=member, 
            action='check_in' if action == 'Check In' else 'check_out'
        )

        return JsonResponse({
            'status': 'success', 
            'message': f'Member {member} {action.lower()}ed successfully!',
            'record': {
                'member_id': member.id,
                'action': record.get_action_display(),
                'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)
             
        
def get_member_history(request):
    """
    Retrieve member check-in/out history. Search by name or phone number.
    If no identifier is provided, return all recent records.
    """
    member_identifier = request.GET.get('id', '').strip()
    
    try:
        if member_identifier:
            # Try to find member(s) by name or phone
            members = Member.objects.filter(
                Q(phone_number=member_identifier) |
                Q(first_name__icontains=member_identifier) |
                Q(last_name__icontains=member_identifier) |
                # Handle full name search
                Q(first_name__icontains=member_identifier.split()[0]) if ' ' in member_identifier else Q(),
                Q(last_name__icontains=member_identifier.split()[-1]) if ' ' in member_identifier else Q()
            ).distinct()

            if not members.exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Member not found'
                }, status=404)
            
            if members.count() > 1:
                # If multiple members found, return first page of combined records
                records = CheckInOutRecord.objects.filter(
                    member__in=members
                ).order_by('-timestamp')
            else:
                # Single member found
                records = members.first().CheckinOut.all().order_by('-timestamp')
        else:
            # Get all records
            records = CheckInOutRecord.objects.all().order_by('-timestamp')
        
        # Pagination
        page_number = request.GET.get('page', 1)
        paginator = Paginator(records, 10)  # 10 records per page
        page_obj = paginator.get_page(page_number)
        
        return JsonResponse({
            'status': 'success',
            'records': [{
                'member': str(record.member),
                'action': record.get_action_display(),
                'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            } for record in page_obj],
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
        
def finance(request):
    allowed_users = ['FastcardioAdmin',]  # Add your allowed usernames
    if request.user.username not in allowed_users:
        messages.error(request, 'Access denied.')
        return redirect('Dashboard')
    return render(request, "finance.html")

class RevenueAndMembershipView(View):
    
    def get_monthly_revenue_data(self, start_date=None, end_date=None):
        if not end_date:
            end_date = datetime.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=365)

    # Get monthly revenue data
        monthly_revenue = PaymentDetails.objects.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date
            ).annotate(
                month=TruncMonth('payment_date')
            ).values('month').annotate(
                total_revenue=Sum('amount'),
                total_subscriptions=Count('id')
            ).order_by('month')
            
        return monthly_revenue

    def get(self, request):
        # Get date range from request parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Filter payments by date range if provided
        filters = {}
        expense_filters = {}
        if start_date:
            filters['payment_date__gte'] = parse_date(start_date)
            expense_filters['date__gte'] = parse_date(start_date)
        if end_date:
            filters['payment_date__lte'] = parse_date(end_date)
            expense_filters['date__lte'] = parse_date(end_date)
        
        # Query payments with optional filters
        payments = PaymentDetails.objects.filter(**filters)
        
        # Calculate total revenue and payment count
        total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0.00
        result = payments.aggregate(count=Count('id'))
        payment_count = result['count'] if result['count'] is not None else 0
        
        # Count memberships and sum amounts by payment plan
        membership_types = payments.values('plan').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Query expenses with date filters
        expenses = Expense.objects.filter(**expense_filters)
        
        # Group expenses by type and calculate totals
        expense_summary = expenses.values('expense_type').annotate(
            total_amount=Sum('amount')
        ).order_by('expense_type')
        
        
        # Convert expense summary to a dictionary with expense types as keys
        expense_data = {
            expense['expense_type'].lower(): float(expense['total_amount'])
            for expense in expense_summary
        }
        
        # Ensure all expense types are present in the response
        expense_types = ['rent', 'salary', 'water', 'cleaners', 'food', 'other','capital','electricity','maintenance']
        formatted_expenses = {
            expense_type: expense_data.get(expense_type, 0)
            for expense_type in expense_types
        }
        #Total expenses
        total_expenses = sum(formatted_expenses.values())
        
        # Get monthly revenue data
        monthly_revenue = self.get_monthly_revenue_data(
            start_date=parse_date(start_date) if start_date else None,
            end_date=parse_date(end_date) if end_date else None
        )
        
        # Format monthly data for the response
        monthly_data = [
            {
                'month': item['month'].strftime('%B %Y'),
                'revenue': float(item['total_revenue']),
                'subscriptions': item['total_subscriptions']
                }
            for item in monthly_revenue
        ]
        print(formatted_expenses)
        
        # Create the response data
        response_data = {
            'total_revenue': total_revenue,
            'total_subscribers': payment_count,
            'membership_types': [
                {
                    'plan': membership['plan'],
                    'count': membership['count'],
                    'total_amount': membership['total_amount']
                }
                for membership in membership_types
            ],
            'expenses': formatted_expenses,
            'total_expenses': total_expenses,
            'monthly_revenue': monthly_data
        }
        print(response_data)
        return JsonResponse(response_data)



def calculate_expiry_dates(payment):
    plan_durations = {
        'daily': 1,
        'monthly': 30,
        'quarterly': 90,
        'biannually': 182,
        'annually': 365,
        'student': 30  # Assuming student package is monthly
    }
    days = plan_durations.get(payment.plan)
    return payment.payment_date + timedelta(days=days)
def reminders(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        reminder_type = request.GET.get('type', 'all')
        current_date = timezone.now().date()
        
        if reminder_type == 'sent':
            sent_reminders = gym_reminder.objects.filter(
                is_sent=True
            ).select_related('member')
            
            reminders_data = [{
                'member_id': reminder.member.id,
                'name': f"{reminder.member.first_name} {reminder.member.last_name}",
                'phone': reminder.member.phone_number,
                'reminder': reminder.reminder,
                'sent_date': reminder.created_at.strftime('%Y-%m-%d'),
                'category': reminder.get_category_display(),
            } for reminder in sent_reminders]
            return JsonResponse({'reminders': reminders_data})
        
        elif reminder_type == 'attendance':
            seven_days_ago = timezone.now() - timedelta(days=5)
            
            # Get members who haven't checked in for 5 days
            inactive_members = Member.objects.filter(
                is_active=True,
                is_frozen=False
            ).prefetch_related(
                'CheckinOut',
                'reminders'
            ).exclude(
                reminders__category='attendance',
                reminders__is_sent=True
            )
            
            reminders_data = []
            for member in inactive_members:
                last_checkin = member.CheckinOut.filter(
                    action='check_in'
                ).order_by('-timestamp').first()
                
                if not last_checkin or last_checkin.timestamp < seven_days_ago:
                    days_absent = (timezone.now() - last_checkin.timestamp).days if last_checkin else None
                    reminders_data.append({
                        'member_id': member.id,
                        'name': f"{member.first_name} {member.last_name}",
                        'phone': member.phone_number,
                        'type': 'attendance',
                        'days_absent': days_absent or 'Never attended',
                        'message': f"Hi {member.first_name}, we miss seeing you at the gym! It's been {days_absent} days since your last visit."
                    })
            return JsonResponse({'reminders': reminders_data})
            
        elif reminder_type == 'subscription':
            # Get members whose subscription is expiring soon
            expiring_members = Member.objects.filter(
                is_active=True,
                is_frozen=False
            ).prefetch_related(
                'payments',
                'CheckinOut',
                'reminders'
            ).exclude(
                reminders__category='expiry',
                reminders__is_sent=True
            )
            
            reminders_data = []
            for member in expiring_members:
                latest_payment = member.payments.order_by('-payment_date').first()
                
                if latest_payment:
                    expiry_date = calculate_expiry_dates(latest_payment)
                    days_until_expiry = (expiry_date - current_date).days
                    
                    # Check for either 3 days before expiry or day of expiry
                    if days_until_expiry == 3 or days_until_expiry == 0:
                        last_checkin = member.CheckinOut.filter(
                            action='check_in'
                        ).order_by('-timestamp').first()
                        
                        # Create appropriate message based on days until expiry
                        if days_until_expiry == 3:
                            message = (
                                f"Hi {member.first_name}, your gym membership expires in 3 days "
                                f"on {expiry_date.strftime('%B %d, %Y')}. "
                                "Please renew your membership to continue enjoying our facilities."
                            )
                        else:  # days_until_expiry == 0
                            message = (
                                f"Hi {member.first_name}, your gym membership expires today. "
                                "Please visit the reception to renew your membership and "
                                "continue your fitness journey with us."
                            )
                        
                        reminders_data.append({
                            'member_id': member.id,
                            'name': f"{member.first_name} {member.last_name}",
                            'phone': member.phone_number,
                            'type': 'subscription',
                            'days_until_expiry': days_until_expiry,
                            'last_attended': last_checkin.timestamp if last_checkin else None,
                            'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                            'message': message
                        })
            
            return JsonResponse({'reminders': reminders_data})
            
        else:  # all reminders
            # Get attendance reminders
            seven_days_ago = timezone.now() - timedelta(days=7)
            inactive_members = Member.objects.filter(
                is_active=True,
                is_frozen=False
            ).prefetch_related(
                'CheckinOut',
                'reminders'
            ).exclude(
                reminders__category='attendance',
                reminders__is_sent=True
            )
            
            attendance_data = []
            for member in inactive_members:
                last_checkin = member.CheckinOut.filter(
                    action='check_in'
                ).order_by('-timestamp').first()
                
                if not last_checkin or last_checkin.timestamp < seven_days_ago:
                    days_absent = (timezone.now() - last_checkin.timestamp).days if last_checkin else None
                    attendance_data.append({
                        'member_id': member.id,
                        'name': f"{member.first_name} {member.last_name}",
                        'phone': member.phone_number,
                        'type': 'attendance',
                        'days_absent': days_absent or 'Never attended',
                        'message': f"Hi {member.first_name}, we miss seeing you at the gym! It's been {days_absent} days since your last visit."
                    })
            
            # Get subscription reminders
            expiring_members = Member.objects.filter(
                is_active=True,
                is_frozen=False
            ).prefetch_related(
                'payments',
                'CheckinOut',
                'reminders'
            ).exclude(
                reminders__category='expiry',
                reminders__is_sent=True
            )
            
            subscription_data = []
            for member in expiring_members:
                latest_payment = member.payments.order_by('-payment_date').first()
                
                if latest_payment:
                    expiry_date = calculate_expiry_dates(latest_payment)
                    days_until_expiry = (expiry_date - current_date).days
                    
                    # Check for either 3 days before expiry or day of expiry
                    if days_until_expiry == 3 or days_until_expiry == 0:
                        last_checkin = member.CheckinOut.filter(
                            action='check_in'
                        ).order_by('-timestamp').first()
                        
                        # Create appropriate message based on days until expiry
                        if days_until_expiry == 3:
                            message = (
                                f"Hi {member.first_name}, your gym membership expires in 3 days "
                                f"on {expiry_date.strftime('%B %d, %Y')}. "
                                "Please renew your membership to continue enjoying our facilities."
                            )
                        else:  # days_until_expiry == 0
                            message = (
                                f"Hi {member.first_name}, your gym membership expires today. "
                                "Please visit the reception to renew your membership and "
                                "continue your fitness journey with us."
                            )
                        
                        subscription_data.append({
                            'member_id': member.id,
                            'name': f"{member.first_name} {member.last_name}",
                            'phone': member.phone_number,
                            'type': 'subscription',
                            'days_until_expiry': days_until_expiry,
                            'last_attended': last_checkin.timestamp if last_checkin else None,
                            'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                            'message': message
                        })
            
            return JsonResponse({
                'attendance_reminders': attendance_data,
                'subscription_reminders': subscription_data
            })
            
    return render(request, 'reminders.html')
def send_reminder(request):
    return JsonResponse({'status': 'success', 'message': 'Reminder sent successfully!'})

@csrf_exempt
@require_http_methods(["POST"])
def mark_reminder_sent(request):
    try:
        data = json.loads(request.body)
        member_id = data.get('member_id')
        
        if not member_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Member ID is required'
            }, status=400)

        member = Member.objects.get(id=member_id)
        
        # First check if there's an existing pending reminder
        existing_reminder = gym_reminder.objects.filter(
            member=member,
            is_sent=False
        ).first()
        
        if existing_reminder:
            # Mark the existing reminder as sent
            existing_reminder.is_sent = True
            existing_reminder.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Existing reminder marked as sent'
            })
        
        # If no existing reminder, create a new one based on the member's status
        # Check for subscription expiry
        latest_payment = member.payments.order_by('-payment_date').first()
        if latest_payment:
            expiry_date = calculate_expiry_dates(latest_payment)
            days_until_expiry = (expiry_date - timezone.now().date()).days
            if 0 <= days_until_expiry <= 7:
                reminder = gym_reminder.objects.create(
                    member=member,
                    category='expiry',
                    reminder=f"Your membership expires in {days_until_expiry} days. Please renew to continue accessing our facilities.",
                    is_sent=True
                )
                return JsonResponse({
                    'status': 'success',
                    'message': 'Subscription reminder marked as sent'
                })

        # Check for attendance
        last_checkin = member.CheckinOut.filter(
            action='check_in'
        ).order_by('-timestamp').first()
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        if not last_checkin or last_checkin.timestamp < seven_days_ago:
            days_absent = (timezone.now() - last_checkin.timestamp).days if last_checkin else 'Never attended'
            reminder = gym_reminder.objects.create(
                member=member,
                category='attendance',
                reminder=f"We miss seeing you at the gym! It's been {days_absent} days since your last visit.",
                is_sent=True
            )
            return JsonResponse({
                'status': 'success',
                'message': 'Attendance reminder marked as sent'
            })

        return JsonResponse({
            'status': 'error',
            'message': 'No valid reminder criteria found for this member'
        }, status=400)

    except Member.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Member not found'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while processing your request'
        }, status=500)
        
def freeze_member(request, member_id):

    # Freeze the membership
    member = get_object_or_404(Member, id=member_id)
    member.is_frozen = True
    member.save()
    
    # Add member to freeze model
    Freeze_member.objects.create(
        member=member
    )
    
    messages.success(request, f'Membership for {member} has been frozen')
    return redirect('Members')

def unfreeze_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    
    # Get the freeze record for this member
    freeze_record = Freeze_member.objects.filter(
        member=member,
        unfrozen_date__isnull=True  # Get the active freeze record
    ).first()
    
    if freeze_record:
        # Calculate the number of frozen days
        frozen_days = (timezone.now().date() - freeze_record.frozen_date).days
        
        # Update the freeze record with unfreeze date
        freeze_record.unfrozen_date = timezone.now()
        freeze_record.freeze_time = frozen_days
        freeze_record.save()
        
        # Extend membership expiry by the frozen duration
        if member.membership_expiry:
            member.membership_expiry += timedelta(days=frozen_days)
            
        # Unfreeze the member
        member.is_frozen = False
        member.save()
        
        messages.success(
            request, 
            f'Membership for {member} has been unfrozen. '
            f'Membership expiry extended by {frozen_days} days to {member.membership_expiry.strftime("%Y-%m-%d")}'
        )
    else:
        messages.warning(request, f'No freeze record found for {member}')
        member.is_frozen = False
        member.save()
    
    return redirect('Members')
    

@allowed_users_only
def expenses(request): 
    return render(request, 'view_expenses.html')


def new_expense(request):
    if request.method == "POST":
        expense = request.POST.get('expense')
        amount = request.POST.get('amount')
        details = request.POST.get('details')
        
        try:
            Expense.objects.create(
                expense_type=expense,
                amount=amount,
                details = details
            )
            messages.success(request, 'Expense saved successfully!')
            return redirect('Expenses')
        except Exception as e:
            print(e)
            messages.error(request, 'Error saving expense.')
    return render(request, 'expenses.html')


def members(request):
    # Retrieve members with their total payments
    members_with_payments = []
    today = timezone.now().date()
    
    for member in Member.objects.all():
        # Get all payment details for this member
        payments = PaymentDetails.objects.filter(member=member)
        
        # Calculate total amount paid
        total_amount_paid = payments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Get the latest payment details
        latest_payment = payments.order_by('-payment_date').first()
        
        # Calculate membership status based on expiry date
        membership_status = 'Expired'
        days_until_expiry = None
        
        if member.membership_expiry:
            days_until_expiry = (member.membership_expiry - today).days
            
            if member.is_frozen:
                membership_status = 'Frozen'
            elif days_until_expiry > 7:
                membership_status = 'Active'
            elif days_until_expiry > 0:
                membership_status = 'Expiring Soon'
            else:
                membership_status = 'Expired'
                member.is_active = False
                member.save()
        
        # Prepare member data
        member_data = {
            'id': member.id,
            'full_name': str(member),
            'first_name': member.first_name,
            'last_name': member.last_name,
            'phone_number': member.phone_number,
            'date_joined': member.date_joined,
            'additional_info': member.additional_info or '',
            'total_amount_paid': total_amount_paid,
            'latest_plan': latest_payment.plan if latest_payment else 'No Plan',
            'latest_payment_date': latest_payment.payment_date if latest_payment else None,
            'expiry_date': member.membership_expiry,
            'membership_status': membership_status,
            'days_until_expiry': days_until_expiry,
            'is_frozen': member.is_frozen
        }
        
        members_with_payments.append(member_data)
    
    members_with_payments.reverse()
    
    return render(request, 'allmembers.html', {
        'members': members_with_payments,
        'today': today
    })


def member_progress(request, member_id):
    """View for displaying member progress dashboard"""
    member = get_object_or_404(Member, id=member_id)
    
    # Get latest progress record
    latest_progress = MemberProgress.objects.filter(member=member).first()
    
    # Calculate workouts this month
    first_day = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    workouts_count = CheckInOutRecord.objects.filter(
        member=member,
        action='check_in',
        timestamp__gte=first_day
    ).count()
    
    # Get historical progress data for charts
    progress_data = MemberProgress.objects.filter(member=member).order_by('date')
    
    # Prepare data for charts
    weight_data = {
        'labels': [p.date.strftime('%Y-%m-%d') for p in progress_data],
        'values': [float(p.weight) for p in progress_data]
    }
    
    measurements_data = {
        'labels': [p.date.strftime('%Y-%m-%d') for p in progress_data],
        'chest': [float(p.chest) if p.chest else None for p in progress_data],
        'waist': [float(p.waist) if p.waist else None for p in progress_data]
    }
    
    context = {
        'member': member,
        'latest_progress': latest_progress,
        'workouts_this_month': workouts_count,
        'weight_data': json.dumps(weight_data),
        'measurements_data': json.dumps(measurements_data)
    }
    
    return render(request, 'member_progress.html', context)

def add_progress(request, member_id):
    """View for adding new progress data"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
    try:
        member = get_object_or_404(Member, id=member_id)
        data = json.loads(request.body)
        print(data)
        
        progress = MemberProgress.objects.create(
            member=member,
            weight=Decimal(data.get('weight', 0)) if data.get('weight') else None,
            body_fat=Decimal(data.get('body_fat', 0)) if data.get('body_fat') else None,
            muscle_mass=Decimal(data.get('muscle_mass', 0)) if data.get('muscle_mass') else None,
            chest=Decimal(data.get('chest', 0)) if data.get('chest') else None,
            waist=Decimal(data.get('waist', 0)) if data.get('waist') else None,
            notes=data.get('notes', '')
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': progress.id,
                'date': progress.date.strftime('%Y-%m-%d'),
                'weight': float(progress.weight),
                'body_fat': float(progress.body_fat) if progress.body_fat else None,
                'muscle_mass': float(progress.muscle_mass) if progress.muscle_mass else None
            }
        })
        
    except (ValueError, KeyError) as e:
        return JsonResponse({'error': str(e)}, status=400)

def get_progress_history(request, member_id):
    """API endpoint for fetching progress history"""
    member = get_object_or_404(Member, id=member_id)
    timeframe = request.GET.get('timeframe', 'all')  # all, year, month, week
    
    # Calculate date range based on timeframe
    end_date = timezone.now()
    if timeframe == 'year':
        start_date = end_date - timedelta(days=365)
    elif timeframe == 'month':
        start_date = end_date - timedelta(days=30)
    elif timeframe == 'week':
        start_date = end_date - timedelta(days=7)
    else:
        start_date = None
    
    # Query progress records
    progress_query = MemberProgress.objects.filter(member=member)
    if start_date:
        progress_query = progress_query.filter(date__gte=start_date)
    
    progress_records = progress_query.order_by('date')
    
    # Prepare data for response
    data = {
        'dates': [p.date.strftime('%Y-%m-%d') for p in progress_records],
        'weight': [float(p.weight) for p in progress_records],
        'body_fat': [float(p.body_fat) if p.body_fat else None for p in progress_records],
        'muscle_mass': [float(p.muscle_mass) if p.muscle_mass else None for p in progress_records],
        'measurements': {
            'chest': [float(p.chest) if p.chest else None for p in progress_records],
            'waist': [float(p.waist) if p.waist else None for p in progress_records]
        }
    }
    
    return JsonResponse(data)


def create_reports(start_date, end_date):

    # Basic member statistics with proper date range
    total_members = Member.objects.filter(
        date_joined__date__range=[start_date, end_date]
    ).count()

    new_members_this_month = Member.objects.filter(
        date_joined__date__range=[start_date, end_date]
    ).count()

    active_members = Member.objects.filter(
        date_joined__date__range=[start_date, end_date],
        is_active=True,
        is_frozen=False
    ).count()

    frozen_members = Member.objects.filter(
        date_joined__date__range=[start_date, end_date],
        is_frozen=True
    ).count()

    inactive_members = Member.objects.filter(
        date_joined__date__range=[start_date, end_date],
        is_active=False,
        is_frozen=False
    ).count()

    # Calculate percentages
    total_period_members = total_members or 1  # Avoid division by zero
    active_percentage = round((active_members / total_period_members * 100), 1)
    inactive_percentage = round((inactive_members / total_period_members * 100), 1)

    # Enhanced Member Analysis
    membership_duration = Member.objects.filter(
        date_joined__date__range=[start_date, end_date],
        is_active=True
    ).annotate(
        duration=ExpressionWrapper(
            end_date - F('date_joined__date'),
            output_field=FloatField()
        )
    ).aggregate(
        avg_duration=Avg('duration'),
        max_duration=Max('duration')
    )

    avg_membership_days = round(membership_duration['avg_duration'] or 0)
    longest_membership_days = round(membership_duration['max_duration'] or 0)

    # Attendance Analysis
    checkins = CheckInOutRecord.objects.filter(
        action='check_in',
        timestamp__date__range=[start_date, end_date]
    )
    
    total_days = (end_date - start_date).days + 1
    avg_daily_checkins = round(checkins.count() / total_days if total_days > 0 else 0)

    # Peak hours analysis
    checkins_by_hour = checkins.annotate(
        hour=ExtractHour('timestamp')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('-count')
    
    if checkins_by_hour:
        peak_hour = checkins_by_hour[0]['hour']
        peak_hour_start = f"{peak_hour:02d}:00"
        peak_hour_end = f"{(peak_hour + 1):02d}:00"
        peak_hour_percentage = round(checkins_by_hour[0]['count'] / checkins.count() * 100 if checkins.count() > 0 else 0)
    else:
        peak_hour_start = "00:00"
        peak_hour_end = "00:00"
        peak_hour_percentage = 0

    # Busiest days analysis
    weekday_distribution = checkins.annotate(
        weekday=ExtractWeekDay('timestamp')
    ).values('weekday').annotate(
        count=Count('id')
    ).order_by('-count')
    
    busiest_day = weekday_distribution.first()

    # Not attending calculation - modified to consider date range
    attending_member_ids = checkins.values_list('member_id', flat=True).distinct()
    
    not_attending = Member.objects.filter(
        date_joined__date__range=[start_date, end_date],
        is_active=True
    ).exclude(
        id__in=attending_member_ids
    ).count()

    # Retention rate calculation
    previous_period_start = start_date - timedelta(days=total_days)
    previous_period_members = Member.objects.filter(
        date_joined__date__range=[previous_period_start, start_date],
        is_active=True
    ).count()
    
    still_active_members = Member.objects.filter(
        date_joined__date__range=[previous_period_start, start_date],
        is_active=True
    ).filter(
        is_active=True
    ).count()
    
    retention_rate = round((still_active_members / previous_period_members * 100) if previous_period_members > 0 else 0, 1)

    # Gender distribution - modified to consider date range
    gender_stats = Member.objects.filter(
        date_joined__date__range=[start_date, end_date]
    ).values('gender').annotate(
        count=Count('id')
    )
    
    total_with_gender = sum(stat['count'] for stat in gender_stats)
    male_percentage = round(next((stat['count'] for stat in gender_stats if stat['gender'].lower() == 'male'), 0) / total_with_gender * 100 if total_with_gender > 0 else 0, 1)
    female_percentage = round(next((stat['count'] for stat in gender_stats if stat['gender'].lower() == 'female'), 0) / total_with_gender * 100 if total_with_gender > 0 else 0, 1)

    # Progress Analytics
    progress_stats = MemberProgress.objects.filter(
        date__range=[start_date, end_date]
    ).aggregate(
        avg_weight=Avg('weight'),
        avg_body_fat=Avg('body_fat'),
        avg_muscle_mass=Avg('muscle_mass'),
        avg_chest=Avg('chest'),
        avg_waist=Avg('waist')
    )

    # Progress Tracking Engagement
    progress_tracking = MemberProgress.objects.filter(
        date__range=[start_date, end_date]
    ).values('member').annotate(
        measurements=Count('id'),
        weight_change=Max('weight') - Min('weight'),
        body_fat_change=Max('body_fat') - Min('body_fat')
    ).aggregate(
        avg_measurements=Avg('measurements'),
        positive_weight_change=Count('weight_change', filter=Q(weight_change__lt=0)),
        positive_body_fat_change=Count('body_fat_change', filter=Q(body_fat_change__lt=0))
    )

    # Member balance analysis - modified to consider date range
    balance_stats = Member.objects.filter(
        date_joined__date__range=[start_date, end_date]
    ).aggregate(
        total_credit=Sum('balance', filter=Q(balance__gt=0)),
        total_debt=Sum('balance', filter=Q(balance__lt=0)),
        avg_balance=Avg('balance')
    )

    # Freeze patterns
    freeze_analysis = Freeze_member.objects.filter(
        frozen_date__range=[start_date, end_date]
    ).values('member').annotate(
        total_freezes=Count('id'),
        total_freeze_time=Sum('freeze_time')
    ).aggregate(
        avg_freezes_per_member=Avg('total_freezes'),
        avg_freeze_time=Avg('total_freeze_time'),
        max_freeze_time=Max('total_freeze_time')
    )

    # Revenue Analysis
    revenue_data = PaymentDetails.objects.filter(
        payment_date__range=[start_date, end_date]
    ).aggregate(
        total_revenue=Sum('amount'),
        total_subscriptions=Count('id'),
        avg_payment=Avg('amount'),
        max_payment=Max('amount')
    )

    # Payment Plan Distribution
    plan_distribution = {}
    for plan_code, plan_name in PaymentDetails.PLAN_CHOICES:
        plan_data = PaymentDetails.objects.filter(
            plan=plan_code,
            payment_date__range=[start_date, end_date]
        ).aggregate(
            amount=Sum('amount'),
            subscribers=Count('id')
        )
        plan_distribution[plan_code] = {
            'amount': plan_data['amount'] or 0,
            'subscribers': plan_data['subscribers']
        }

    context = {
        # Member Statistics
        'total_members': total_members,
        'new_members_this_month': new_members_this_month,
        'active_members': active_members,
        'active_percentage': active_percentage,
        'frozen_members': frozen_members,
        'inactive_members': inactive_members,
        'inactive_percentage': inactive_percentage,
        'avg_membership_days': avg_membership_days,
        'longest_membership_days': longest_membership_days,
        
        # Attendance Stats
        'avg_daily_checkins': avg_daily_checkins,
        'peak_hour_start': peak_hour_start,
        'peak_hour_end': peak_hour_end,
        'peak_hour_percentage': peak_hour_percentage,
        'busiest_weekday': busiest_day['weekday'] if busiest_day else None,
        'not_attending': not_attending,
        'retention_rate': retention_rate,
        
        # Demographics
        'male_percentage': male_percentage,
        'female_percentage': female_percentage,
        
        # Progress Metrics
        'avg_weight': round(progress_stats['avg_weight'] or 0, 1),
        'avg_body_fat': round(progress_stats['avg_body_fat'] or 0, 1),
        'avg_muscle_mass': round(progress_stats['avg_muscle_mass'] or 0, 1),
        'avg_chest': round(progress_stats['avg_chest'] or 0, 1),
        'avg_waist': round(progress_stats['avg_waist'] or 0, 1),
        
        # Progress Engagement
        'avg_measurements_per_member': round(progress_tracking['avg_measurements'] or 0, 1),
        'members_with_weight_loss': progress_tracking['positive_weight_change'],
        'members_with_fat_loss': progress_tracking['positive_body_fat_change'],
        
        # Financial Stats
        'total_member_credit': round(balance_stats['total_credit'] or 0, 2),
        'total_member_debt': round(abs(balance_stats['total_debt'] or 0), 2),
        'avg_member_balance': round(balance_stats['avg_balance'] or 0, 2),
        
        # Freeze Stats
        'avg_freezes_per_member': round(freeze_analysis['avg_freezes_per_member'] or 0, 1),
        'avg_freeze_duration': round(freeze_analysis['avg_freeze_time'] or 0),
        'max_freeze_duration': round(freeze_analysis['max_freeze_time'] or 0),
        
        # Revenue Stats
        'total_revenue': revenue_data['total_revenue'] or 0,
        'total_subscriptions': revenue_data['total_subscriptions'],
        'avg_payment_amount': round(revenue_data['avg_payment'] or 0, 2),
        'max_payment_amount': round(revenue_data['max_payment'] or 0, 2),
        
        # Plan Distribution
        'daily_subscription_amount': plan_distribution['daily']['amount'],
        'daily_subscribers': plan_distribution['daily']['subscribers'],
        'monthly_subscription_amount': plan_distribution['monthly']['amount'],
        'monthly_subscribers': plan_distribution['monthly']['subscribers'],
        'quarterly_subscription_amount': plan_distribution['quarterly']['amount'],
        'quarterly_subscribers': plan_distribution['quarterly']['subscribers'],
        'biannual_subscription_amount': plan_distribution['biannually']['amount'],
        'biannual_subscribers': plan_distribution['biannually']['subscribers'],
        'annual_subscription_amount': plan_distribution['annually']['amount'],
        'annual_subscribers': plan_distribution['annually']['subscribers'],
        'student_subscription_amount': plan_distribution['student']['amount'],
        'student_subscribers': plan_distribution['student']['subscribers']
    }
    
    return context

@allowed_users_only_1
def reports(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
    except:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    
    context = create_reports(start_date, end_date)
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(context)
        
    return render(request, "reports.html", context)

def download_report(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
    except:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    
    context = create_reports(start_date, end_date)
    
    report_data = {
        "Membership Overview": {
            "current": context['total_members'],
            "description": "Overview of current membership status and engagement.",
            "chart_type": "pie",
            "chart_data": {
                "labels": ["Active", "Frozen", "Inactive"],
                "values": [
                    context['active_members'],
                    context['frozen_members'],
                    context['inactive_members']
                ]
            },
            "date_range": "Current Month",
            "metrics": {
                "Active Members": f"{context['active_percentage']}%",
                "Average Membership Duration": f"{context['avg_membership_days']} days",
                "Longest Membership": f"{context['longest_membership_days']} days",
                "New Members This Month": context['new_members_this_month']
            }
        },
        "Attendance Analytics": {
            "current": context['avg_daily_checkins'],
            "description": "Daily attendance patterns and peak usage analysis.",
            "chart_type": "bar",
            "chart_data": {
                "labels": ["Peak Hours", "Off-Peak Hours"],
                "values": [
                    context['peak_hour_percentage'],
                    100 - context['peak_hour_percentage']
                ]
            },
            "date_range": "Current Month",
            "metrics": {
                "Peak Hours": f"{context['peak_hour_start']} - {context['peak_hour_end']}",
                "Busiest Day": context['busiest_weekday'],
                "Non-Attending Members": context['not_attending'],
                "Retention Rate": f"{context['retention_rate']}%"
            }
        },
        "Member Demographics": {
            "current": context['total_members'],
            "description": "Gender distribution and progress tracking statistics.",
            "chart_type": "pie",
            "chart_data": {
                "labels": ["Male", "Female"],
                "values": [
                    context['male_percentage'],
                    context['female_percentage']
                ]
            },
            "date_range": "Current Month",
            "metrics": {
                "Average Weight": f"{context['avg_weight']} kg",
                "Average Body Fat": f"{context['avg_body_fat']}%",
                "Average Muscle Mass": f"{context['avg_muscle_mass']} kg",
                "Members with Weight Loss": context['members_with_weight_loss'],
                "Members with Fat Loss": context['members_with_fat_loss']
            }
        },
        "Financial Analysis": {
            "current": context['total_revenue'],
            "description": "Revenue breakdown and subscription distribution.",
            "chart_type": "bar",
            "chart_data": {
                "labels": ["Daily", "Monthly", "Quarterly", "Biannual", "Annual", "Student"],
                "values": [
                    context['daily_subscribers'],
                    context['monthly_subscribers'],
                    context['quarterly_subscribers'],
                    context['biannual_subscribers'],
                    context['annual_subscribers'],
                    context['student_subscribers']
                ]
            },
            "date_range": "Current Month",
            "metrics": {
                "Total Subscriptions": context['total_subscriptions'],
                "Average Payment": f"${context['avg_payment_amount']}",
                "Maximum Payment": f"${context['max_payment_amount']}",
                "Total Member Credit": f"${context['total_member_credit']}",
                "Total Member Debt": f"${context['total_member_debt']}"
            }
        },
        "Subscription Plans": {
            "current": context['total_subscriptions'],
            "description": "Detailed breakdown of subscription plans and pricing.",
            "chart_type": "bar",
            "chart_data": {
                "labels": ["Daily", "Monthly", "Quarterly", "Biannual", "Annual", "Student"],
                "values": [
                    context['daily_subscription_amount'],
                    context['monthly_subscription_amount'],
                    context['quarterly_subscription_amount'],
                    context['biannual_subscription_amount'],
                    context['annual_subscription_amount'],
                    context['student_subscription_amount']
                ]
            },
            "date_range": "Current Month",
            "metrics": {
                "Daily Plan": f"${context['daily_subscription_amount']} ({context['daily_subscribers']} members)",
                "Monthly Plan": f"${context['monthly_subscription_amount']} ({context['monthly_subscribers']} members)",
                "Quarterly Plan": f"${context['quarterly_subscription_amount']} ({context['quarterly_subscribers']} members)",
                "Biannual Plan": f"${context['biannual_subscription_amount']} ({context['biannual_subscribers']} members)",
                "Annual Plan": f"${context['annual_subscription_amount']} ({context['annual_subscribers']} members)",
                "Student Plan": f"${context['student_subscription_amount']} ({context['student_subscribers']} members)"
            }
        }
    }
    
    # Generate and upload report
    comprehensive_report = create_fastcardio_report(
        report_data, 
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
        )
    
    return JsonResponse({'download_url': comprehensive_report['firebase_url']})
    # return render(request, "reports.html", context)

def member_status(request):
    today = timezone.now().date()
    members = Member.objects.annotate(
        latest_payment_date=Max('payments__payment_date')
    )
    
    active_members = []
    inactive_members = []
    expired_members = []
    
    for member in members:
        member_data = {
            'name': f"{member.first_name} {member.last_name}",
            'phone': member.phone_number,
            'joined': member.date_joined.strftime('%Y-%m-%d'),
            'gender': member.gender,
        }
        
        latest_payment = PaymentDetails.objects.filter(member=member).order_by('-payment_date').first()
        
        if latest_payment:
            plan_duration = {
                'daily': 1, 'monthly': 30, 'quarterly': 90,
                'biannually': 180, 'annually': 365, 'student': 30
            }
            
            expiry_date = latest_payment.payment_date + timedelta(days=plan_duration[latest_payment.plan])
            member_data.update({
                'plan': latest_payment.plan,
                'last_payment': latest_payment.payment_date.strftime('%Y-%m-%d'),
                'expiry_date': expiry_date.strftime('%Y-%m-%d')
            })
            
            if member.is_frozen:
                inactive_members.append(member_data)
            elif expiry_date < today:
                expired_members.append(member_data)
            elif member.is_active:
                active_members.append(member_data)
            else:
                inactive_members.append(member_data)
        else:
            member_data.update({
                'plan': 'No plan',
                'last_payment': 'Never',
                'expiry_date': 'N/A'
            })
            inactive_members.append(member_data)
    
    context = {
        'active_members': active_members,
        'inactive_members': inactive_members,
        'expired_members': expired_members,
        'stats': {
            'total_active': len(active_members),
            'total_inactive': len(inactive_members),
            'total_expired': len(expired_members)
        }
    }
    return render(request, 'status.html', context)

def tasks(request):
    tasks = Task.objects.all()
    members = Member.objects.all()
    # payment_id = get_object_or_404(PaymentDetails,member = member)
    return render(request,'tasks.html',{'tasks':tasks,'members':members})

def add_task(request):
    
    if request.method == 'POST':
        member = request.POST.get('member')
        member = get_object_or_404(Member, id=member)
        
        title = request.POST.get('title')
        
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date')
        
        task = Task.objects.create(
            member = member,
            title= title,
            description= description,
            priority=priority,
            due_date=due_date
        )
        
        task.save()
        messages.success(request, "Task added successfully")
    
    return redirect('Tasks')
    
    
def update_task(request, task_id):
    if request.method == 'POST':
        task = Task.objects.get(id=task_id)
        task.status = 'completed' if task.status == 'pending' else 'pending'
        task.save()
    return redirect('Tasks')

def delete_task(request, task_id):
    if request.method == 'POST':
        Task.objects.filter(id=task_id).delete()
    return redirect('Tasks')