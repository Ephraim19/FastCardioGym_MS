from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from .models import Member, PaymentDetails, CheckInOutRecord, gym_reminder, Freeze_member, Expense, MemberProgress
from django.contrib import messages
from django.db.models import Sum, Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.views import View
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import timedelta,datetime
from django.db.models.functions import TruncMonth
from django.db.models import Count, Q, Max, Subquery, OuterRef
from django.contrib.auth.decorators import login_required
import json
from decimal import Decimal
from .fastcardio_report import create_fastcardio_report


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
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if username or password is empty
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'index.html')
        
        try:
            # First, attempt to get the user
            user = User.objects.get(username=username)
            
            # Verify the password
            if user.is_superuser and user.check_password(password):
                # Use Django's built-in authentication
                auth_user = authenticate(request, username=username, password=password)
                
                if auth_user is not None:
                    login(request, auth_user)
                    # messages.success(request, 'Successfully logged in!')
                    return redirect('Dashboards')  
                else:
                    messages.error(request, 'Authentication failed.')
            else:
                messages.error(request, 'Invalid login credentials or insufficient permissions.')
        
        except User.DoesNotExist:
            messages.error(request, 'User does not exist.')
        
        # If login fails, return to the login page with error messages
        return render(request, 'index.html')
    
    # If not a POST request, just render the login page
    return render(request, 'index.html')


def custom_logout(request):
    logout(request)
    return redirect('login') 



def dashboard(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    one_weeks_ago = today - timedelta(days=7)

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
            'value': expired_count,
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
    # Option 1: Use session to get member ID
    if member_id is None:
        member_id = request.session.get('new_member_id')
    
    # Get the member
    try:
        member = get_object_or_404(Member, id=member_id)
    except:
        return HttpResponse("Member not found")
        
    if request.method == "POST":
        # Remove session variable after use
        if 'new_member_id' in request.session:
            del request.session['new_member_id']
        
        plan = request.POST.get('plan')
        amount = Decimal(request.POST.get('amount'))
        transaction_id = request.POST.get('code')
        
        # Get expected amount for the chosen plan
        expected_amount = PLAN_PRICES.get(plan)
        
        if expected_amount is None and plan != 'complete':
            messages.error(request, 'Invalid plan selected!')
            return redirect("Members")
        
        # Create payment record
        PaymentDetails.objects.create(
            member=member,
            plan=plan,
            amount=amount,
            transaction_id=transaction_id
        )
        
        # Calculate difference between paid and expected amount
        print(member.balance)
        if plan == 'complete':
            difference = amount + member.balance
            print(difference,amount, member.balance)
            member.balance = difference
            member.save()
        else:
            difference = amount - expected_amount
            member.balance = difference
            member.save()
        
        # Update member status based on payment and balance
        if plan != 'complete':
         if amount >= expected_amount or (amount + member.balance >= expected_amount) :
            member.is_active = True
            if difference > 0:
                messages.success(request, 
                    f'Overpayment of {difference:.2f} recorded. Current balance: {member.balance:.2f}')
         else:
            member.is_active = False
            messages.warning(request, 
                f'Underpayment of {abs(difference):.2f}. Current balance: {member.balance:.2f}.')
        else:
            member.is_active = True
            messages.success(request, f'Complete payment of {amount:.2f} recorded.Your balance is {member.balance:.2f} Membership activated.')
        member.save()
        
        # Determine appropriate success message
        if member.is_active:
            messages.success(request, 
                f'Payment saved successfully for {member}! Membership has been activated.')
        else:
            messages.success(request, 
                f'Payment saved successfully for {member}, but membership is inactive due to incomplete payment.')
        
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

def members(request):
    # Retrieve members with their total payments
    members_with_payments = []
    
    for member in Member.objects.all():
        # Get all payment details for this member
        payments = PaymentDetails.objects.filter(member=member)
        
        # Calculate total amount paid
        total_amount_paid = payments.aggregate(total=Sum('amount'))['total'] or 0
        
        # Get the latest payment details
        latest_payment = payments.order_by('-payment_date').first()
        
        # Calculate expiry date
        expiry_date = None
        membership_status = 'Expired'
        
        if latest_payment:
            expiry_date = calculate_expiry_date(latest_payment.payment_date, latest_payment.plan)
            
            if expiry_date:
                today = timezone.now().date()
                days_until_expiry = (expiry_date - today).days
                
                if days_until_expiry > 7:
                    membership_status = 'Active'
                elif days_until_expiry > 0:
                    membership_status = 'Expiring Soon'
                else:
                    membership_status = 'Expired'
        
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
            'expiry_date': expiry_date,
            'membership_status': membership_status,
            'days_until_expiry': (expiry_date - timezone.now().date()).days if expiry_date else None
        }
        
        members_with_payments.append(member_data)
    
    members_with_payments.reverse()
    
    return render(request, 'allmembers.html', {
        'members': members_with_payments,
        'today': timezone.now().date()
    })
    

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
    # Get member or return 404
    member = get_object_or_404(Member, pk=member_id)
    
    # Get all payments
    recent_payments = PaymentDetails.objects.filter(member=member).order_by('-payment_date')[:3]
    
    # Get latest payment and calculate expiry
    latest_payment = PaymentDetails.objects.filter(member=member).order_by('-payment_date').first()
    
    if latest_payment:
        expiry_date = calculate_expiry_date(latest_payment.payment_date, latest_payment.plan)
        days_left = (expiry_date - timezone.now().date()).days if expiry_date else 0
        membership_status = "Active" if days_left > 0 and member.is_active else "Expired"
    else:
        expiry_date = None
        days_left = 0
        membership_status = "Inactive"

    # Get check-in statistics
    total_checkins = CheckInOutRecord.objects.filter(
        member=member, 
        action='check_in'
    ).count()

    # Get recent check-ins
    recent_checkins = CheckInOutRecord.objects.filter(
        member=member,
        action='check_in'
    ).order_by('-timestamp')[:5]

    # Calculate check-ins this month
    first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    checkins_this_month = CheckInOutRecord.objects.filter(
        member=member,
        action='check_in',
        timestamp__gte=first_day_of_month
    ).count()

    # Get last check-in date
    last_checkin = CheckInOutRecord.objects.filter(
        member=member,
        action='check_in'
    ).order_by('-timestamp').first()

    # Get balance status message
    if member.balance > 0:
        balance_status = "Credit"
    elif member.balance < 0:
        balance_status = "Debt"
    else:
        balance_status = "Neutral"

    context = {
        'member': member,
        'recent_payments': recent_payments,
        'recent_checkins': recent_checkins,
        'latest_payment': latest_payment,
        'membership_status': membership_status,
        'expiry_date': expiry_date,
        'days_left': days_left,
        'total_checkins': total_checkins,
        'checkins_this_month': checkins_this_month,
        'last_checkin': last_checkin,
        'current_plan': latest_payment.plan if latest_payment else "No active plan",
        'balance': member.balance,
        'balance_status': balance_status,
    }
    
    return render(request, 'member_details.html', context)


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
    Retrieve member check-in/out history. If no member ID is provided,
    return all recent records.
    """
    member_id = request.GET.get('id', '').strip()
    
    try:
        if member_id:
            # Get specific member's records
            member = Member.objects.get(phone_number=member_id)
            records = member.CheckinOut.all().order_by('-timestamp')
        else:
            # Get all records
            records = CheckInOutRecord.objects.all().order_by('-timestamp')
        
        # Pagination
        page_number = request.GET.get('page', 1)
        paginator = Paginator(records, 10)  # 10 records per page
        page_obj = paginator.get_page(page_number)

        return JsonResponse({
            'status': 'success',
            'records': [
                {
                    'member': str(record.member),
                    'action': record.get_action_display(),
                    'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                } for record in page_obj
            ],
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number
        })

    except Member.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'Member not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


def finance(request):
    return render(request,"finance.html")


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
        expense_types = ['rent', 'salary', 'water', 'cleaners', 'food', 'other']
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
        
        return JsonResponse(response_data)

from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max, Q
from .models import Member, PaymentDetails, CheckInOutRecord, gym_reminder

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
            sent_reminders = gym_reminder.objects.filter(is_sent=True).select_related('member')
            reminders_data = [{
                'member_id': reminder.member.id,
                'name': f"{reminder.member.first_name} {reminder.member.last_name}",
                'phone': reminder.member.phone_number,  # Added phone number
                'reminder': reminder.reminder,
                'sent_date': reminder.created_at.strftime('%Y-%m-%d'),
                'category': reminder.get_category_display()
            } for reminder in sent_reminders]
            return JsonResponse({'reminders': reminders_data})
        
        elif reminder_type == 'attendance':
            seven_days_ago = timezone.now() - timedelta(days=7)
            inactive_members = Member.objects.filter(
                is_active=True,
                is_frozen=False
            ).prefetch_related('CheckinOut')
            
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
                        'phone': member.phone_number,  # Added phone number
                        'type': 'attendance',
                        'days_absent': days_absent or 'Never attended'
                    })
            return JsonResponse({'reminders': reminders_data})
            
        elif reminder_type == 'subscription':
            expiring_members = Member.objects.filter(
                is_active=True,
                is_frozen=False
            ).prefetch_related('payments', 'CheckinOut')
            
            reminders_data = []
            for member in expiring_members:
                latest_payment = member.payments.order_by('-payment_date').first()
                
                if latest_payment:
                    expiry_date = calculate_expiry_dates(latest_payment)
                    days_until_expiry = (expiry_date - current_date).days
                    
                    if 0 <= days_until_expiry <= 7:
                        last_checkin = member.CheckinOut.filter(
                            action='check_in'
                        ).order_by('-timestamp').first()
                        
                        reminders_data.append({
                            'member_id': member.id,
                            'name': f"{member.first_name} {member.last_name}",
                            'phone': member.phone_number,  # Added phone number
                            'type': 'subscription',
                            'days_until_expiry': days_until_expiry,
                            'last_attended': last_checkin.timestamp if last_checkin else None,
                            'expiry_date': expiry_date.strftime('%Y-%m-%d')
                        })
            return JsonResponse({'reminders': reminders_data})
            
        else:  # all reminders
            attendance_data = []
            subscription_data = []
            
            # Get attendance reminders
            seven_days_ago = timezone.now() - timedelta(days=7)
            inactive_members = Member.objects.filter(
                is_active=True,
                is_frozen=False
            ).prefetch_related('CheckinOut')
            
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
                        'days_absent': days_absent or 'Never attended'
                    })
            
            # Get subscription reminders
            expiring_members = Member.objects.filter(
                is_active=True,
                is_frozen=False
            ).prefetch_related('payments', 'CheckinOut')
            
            for member in expiring_members:
                latest_payment = member.payments.order_by('-payment_date').first()
                
                if latest_payment:
                    expiry_date = calculate_expiry_dates(latest_payment)
                    days_until_expiry = (expiry_date - current_date).days
                    
                    if 0 <= days_until_expiry <= 7:
                        last_checkin = member.CheckinOut.filter(
                            action='check_in'
                        ).order_by('-timestamp').first()
                        
                        subscription_data.append({
                            'member_id': member.id,
                            'name': f"{member.first_name} {member.last_name}",
                            'phone': member.phone_number, 
                            'type': 'subscription',
                            'days_until_expiry': days_until_expiry,
                            'last_attended': last_checkin.timestamp if last_checkin else None,
                            'expiry_date': expiry_date.strftime('%Y-%m-%d')
                        })
            
            return JsonResponse({
                'attendance_reminders': attendance_data,
                'subscription_reminders': subscription_data
            })
            
    return render(request, 'reminders.html')


def send_reminder(request):
    return JsonResponse({'status': 'success', 'message': 'Reminder sent successfully!'})
def freeze_member(request,member_id):
    
    if request.method == "POST":
        freeze_time = request.POST.get('freezeTime')
        member = get_object_or_404(Member, id=member_id)
        
        
        # Freeze the membership
        member.is_frozen = True
        # member.is_active = False
        member.save()
        
        # Add member to freeze model
        Freeze_member.objects.create(
            member = member,
            freeze_time = freeze_time,
        )
        
        messages.success(request, f'Membership for {member} has been frozen for {freeze_time} days.')
        return redirect('Members')
    
    return render(request, 'freeze.html')

def unfreeze_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    member.is_frozen = False
    member.save()
    
    messages.success(request, f'Membership for {member} has been unfrozen')
    return redirect('Members')
    


def expenses(request):
    return render(request, 'view_expenses.html')


def new_expense(request):
    if request.method == "POST":
        expense = request.POST.get('expense')
        amount = request.POST.get('amount')
        
        try:
            Expense.objects.create(
                expense_type=expense,
                amount=amount
            )
            messages.success(request, 'Expense saved successfully!')
            return redirect('Expenses')
        except Exception as e:
            print(e)
            messages.error(request, 'Error saving expense.')
    return render(request, 'expenses.html')


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


def reports(request):
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    
    # Get basic member statistics with date filtering
    total_members = Member.objects.filter(
        date_joined__date__lte=end_date
    ).count()

    active_members = Member.objects.filter(
        date_joined__date__lte=end_date,
        is_active=True,
        is_frozen=False
    ).count()

    new_members_this_month = Member.objects.filter(
        date_joined__date__gte=start_date,
        date_joined__date__lte=end_date
    ).count()

    new_active_this_month = Member.objects.filter(
        date_joined__date__gte=start_date,
        date_joined__date__lte=end_date,
        is_active=True
    ).count()
    
    # Get check-in statistics for the selected date range
    active_checkins = CheckInOutRecord.objects.filter(
        action='check_in',
        timestamp__date=end_date
    ).count()
    
    # Calculate members not attending based on the date range
    one_week_ago = end_date - timedelta(days=7)
    attending_member_ids = CheckInOutRecord.objects.filter(
        action='check_in',
        timestamp__date__gte=one_week_ago,
        timestamp__date__lte=end_date
    ).values_list('member_id', flat=True).distinct()
    
    not_attending = Member.objects.filter(
        date_joined__date__lte=end_date,
        is_active=True
    ).exclude(
        id__in=attending_member_ids
    ).count()
    
    # Get revenue statistics for the date range
    revenue_data = PaymentDetails.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date
    ).aggregate(
        total_revenue=Sum('amount'),
        total_subscriptions=Count('id')
    )
    
    # Get subscription breakdowns for the date range
    subscription_data = {}
    for plan in PaymentDetails.PLAN_CHOICES:
        plan_data = PaymentDetails.objects.filter(
            plan=plan[0],
            payment_date__gte=start_date,
            payment_date__lte=end_date
        ).aggregate(
            amount=Sum('amount'),
            subscribers=Count('id')
        )
        subscription_data[plan[0]] = {
            'amount': plan_data['amount'] or 0,
            'subscribers': plan_data['subscribers']
        }
    
    context = {
        # Member statistics
        'total_members': total_members,
        'active_members': active_members,
        'new_members_this_month': new_members_this_month,
        'new_active_this_month': new_active_this_month,
        'active_checkins': active_checkins,
        'not_attending': not_attending,
        
        # Revenue statistics
        'total_revenue': revenue_data['total_revenue'] or 0,
        'total_subscriptions': revenue_data['total_subscriptions'] or 0,
        
        # Subscription breakdowns
        'daily_subscription_amount': subscription_data['daily']['amount'],
        'daily_subscribers': subscription_data['daily']['subscribers'],
        'monthly_subscription_amount': subscription_data['monthly']['amount'],
        'monthly_subscribers': subscription_data['monthly']['subscribers'],
        'quarterly_subscription_amount': subscription_data['quarterly']['amount'],
        'quarterly_subscribers': subscription_data['quarterly']['subscribers'],
        'biannual_subscription_amount': subscription_data['biannually']['amount'],
        'biannual_subscribers': subscription_data['biannually']['subscribers'],
        'annual_subscription_amount': subscription_data['annually']['amount'],
        'annual_subscribers': subscription_data['annually']['subscribers'],
        'student_subscription_amount': subscription_data['student']['amount'],
        'student_subscribers': subscription_data['student']['subscribers'],
    }
    
    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(context)
    
    return render(request, "reports.html", context)

def get_historical_data(model, date_field, value_field=None, months=6, filters=None):
    """
    Get monthly historical data for the specified model and fields
    
    Args:
        model: Django model class
        date_field: String name of the date field to query
        value_field: Optional field to sum values from
        months: Number of months of history to return
        filters: Optional dictionary of additional filter conditions
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30 * months)
    
    months_data = []
    current_date = start_date
    
    # Initialize base query filters
    base_filters = {
        f'{date_field}__date__gte': current_date,
        f'{date_field}__date__lte': None  # Will be set in the loop
    }
    
    # Add any additional filters
    if filters:
        base_filters.update(filters)
    
    while current_date <= end_date:
        month_end = (current_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Update the date range filter
        query_filters = base_filters.copy()
        query_filters[f'{date_field}__date__lte'] = month_end
        
        if value_field:
            count = model.objects.filter(**query_filters).aggregate(
                total=Sum(value_field))['total'] or 0
        else:
            count = model.objects.filter(**query_filters).count()
            
        months_data.append({
            'label': current_date.strftime('%b'),
            'value': float(count) if isinstance(count, Decimal) else count
        })
        current_date = (current_date + timedelta(days=32)).replace(day=1)
    
    return {
        'labels': [m['label'] for m in months_data],
        'values': [m['value'] for m in months_data]
    }

def get_daily_checkins_distribution():
    """Get check-in distribution by time slots"""
    today = timezone.now().date()
    time_slots = [
        ('6-9am', 6, 9),
        ('9-12pm', 9, 12),
        ('12-3pm', 12, 15),
        ('3-6pm', 15, 18),
        ('6-9pm', 18, 21),
        ('9-11pm', 21, 23)
    ]
    
    distribution = []
    for slot_name, start_hour, end_hour in time_slots:
        count = CheckInOutRecord.objects.filter(
            action='check_in',
            timestamp__hour__gte=start_hour,
            timestamp__hour__lt=end_hour
        ).count()
        distribution.append(count)
    
    return {
        'labels': [slot[0] for slot in time_slots],
        'values': distribution
    }

def get_revenue_breakdown():
    """Get revenue breakdown by plan type"""
    total_by_plan = PaymentDetails.objects.values('plan').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    return {
        'labels': [item['plan'].title() for item in total_by_plan],
        'values': [float(item['total']) for item in total_by_plan]
    }

def download_report(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    
    # Get all required metrics
    total_members = Member.objects.count()
    active_members = Member.objects.filter(is_active=True, is_frozen=False).count()
    new_members = Member.objects.filter(date_joined__date__gte=thirty_days_ago).count()
    active_checkins = CheckInOutRecord.objects.filter(
        action='check_in',
        timestamp__date=today
    ).count()
    
    # Calculate gender distribution
    gender_stats = Member.objects.values('gender').annotate(
        count=Count('id')
    )
    male_percent = next((item['count'] / total_members * 100 
                        for item in gender_stats if item['gender'].lower() == 'male'), 0)
    female_percent = next((item['count'] / total_members * 100 
                         for item in gender_stats if item['gender'].lower() == 'female'), 0)
    
    # Get revenue data
    total_revenue = PaymentDetails.objects.filter(
        payment_date__gte=thirty_days_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # First prepare expense data
    expense_types = list(Expense.objects.values_list('expense_type', flat=True).distinct())
    expense_data = {
        "labels": expense_types,
        "values": [
            float(Expense.objects.filter(expense_type=exp_type).aggregate(
                total=Sum('amount'))['total'] or 0) 
            for exp_type in expense_types
        ]
    }
    
    # Prepare data dictionary for report
    report_data = {
        "All Members": {
            "current": total_members,
            "description": f"Total registered members: {total_members} (↑{new_members} this month). "
                         f"Demographics show {male_percent:.1f}% male, {female_percent:.1f}% female.",
            "chart_type": "line",
            "chart_data": get_historical_data(Member, 'date_joined')
        },
        "Active Members": {
            "current": active_members,
            "description": f"{active_members} active members "
                         f"({(active_members/total_members*100):.1f}% engagement rate).",
            "chart_type": "line",
            "chart_data": get_historical_data(Member, 'date_joined', None, 6)
        },
        "Active Check-ins": {
            "current": active_checkins,
            "description": "Daily check-ins distribution across different times.",
            "chart_type": "bar",
            "chart_data": get_daily_checkins_distribution()
        },
        "Not Attending": {
            "current": Member.objects.filter(is_active=False).count(),
            "description": "Inactive member trends and reactivation rates.",
            "chart_type": "line",
            "chart_data": get_historical_data(Member, 'date_joined', filters={'is_active': False})
        },
        "Total Revenue": {
            "current": f"${float(total_revenue):,.2f}",
            "description": "Revenue breakdown by subscription type",
            "chart_type": "pie",
            "chart_data": get_revenue_breakdown()
        },
        "Subscription Distribution": {
            "current": f"{PaymentDetails.objects.count()} total",
            "description": "Distribution of subscription types",
            "chart_type": "pie",
            "chart_data": {
                "labels": [plan[1] for plan in PaymentDetails.PLAN_CHOICES],
                "values": [PaymentDetails.objects.filter(plan=plan[0]).count() 
                          for plan in PaymentDetails.PLAN_CHOICES]
            }
        },
        "Expenses": {
            "current": f"${sum(expense_data['values']):,.2f}",
            "description": "Breakdown of expenses by category",
            "chart_type": "pie",
            "chart_data": expense_data
        }
    }
    
    # Generate and upload report
    comprehensive_report = create_fastcardio_report(report_data, expense_data)
    
    return JsonResponse({'download_url': comprehensive_report['firebase_url']})


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