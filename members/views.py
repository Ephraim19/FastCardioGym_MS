# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from .models import Member, PaymentDetails, CheckInOutRecord, gym_reminder, Freeze_member
from django.contrib import messages
from django.db.models import Sum, Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login
from django.views import View
from django.utils.dateparse import parse_date
from django.utils import timezone
from datetime import timedelta

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

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from .models import Member, CheckInOutRecord, PaymentDetails, Freeze_member

def dashboard(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)
    one_weeks_ago = today - timedelta(days=7)

    # All Members count
    all_members = Member.objects.count()
    new_members_last_month = Member.objects.filter(
        date_joined__date__gte=thirty_days_ago
    ).count()

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

    # Expired Members (those whose last payment was more than their plan period)
    daily_expiry = today - timedelta(days=1)
    monthly_expiry = today - timedelta(days=30)
    quarterly_expiry = today - timedelta(days=90)
    biannual_expiry = today - timedelta(days=182)
    yearly_expiry = today - timedelta(days=365)
    student_expiry = today - timedelta(days=30)

    # Expired members query
    expired_members = Member.objects.filter(
        Q(payments__plan='daily', payments__payment_date__lt=daily_expiry) |
        Q(payments__plan='monthly', payments__payment_date__lt=monthly_expiry) |
        Q(payments__plan='quarterly', payments__payment_date__lt=quarterly_expiry) |
        Q(payments__plan='biannually', payments__payment_date__lt=biannual_expiry) |
        Q(payments__plan='annually', payments__payment_date__lt=yearly_expiry) |
        Q(payments__plan='student', payments__payment_date__lt=student_expiry)
    ).distinct().count()

    # Frozen Members
    frozen_members = Member.objects.filter(is_frozen=True).count()

    # Not Attending (no check-ins in last 2 weeks)
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
            'value': expired_members,
            'change': 'Action needed'
        },
        'frozen_members': {
            'value': frozen_members,
            'change': 'On temporary hold'
        },
        'not_attending': {
            'value': not_attending,
            'change': '1 weeks inactive'
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
    
    print(f"Member for payment: {member}")
    
    if request.method == "POST":
        # Remove session variable after use
        if 'new_member_id' in request.session:
            del request.session['new_member_id']
        
        plan = request.POST.get('plan')
        amount = request.POST.get('amount')
        transaction_id = request.POST.get('code')

        print(plan)
        
        # Save the payment details
        PaymentDetails.objects.create(
            member=member,
            plan=plan,
            amount=amount,
            transaction_id=transaction_id
        )
        messages.success(request, f'Payment saved successfully for { member}!')
        
        return redirect("Members")
    
    # Render payment form with member context
    return render(request, 'payment.html', {'member': member})

from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import Member, PaymentDetails

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
    
    for member in Member.objects.filter(is_active=True):
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
        'current_plan': latest_payment.plan if latest_payment else "No active plan"
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
    def get(self, request):
        # Get date range from request parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Filter payments by date range if provided
        filters = {}
        if start_date:
            filters['payment_date__gte'] = parse_date(start_date)
        if end_date:
            filters['payment_date__lte'] = parse_date(end_date)
        
        # Query the database with optional filters
        payments = PaymentDetails.objects.filter(**filters)
        
        # Calculate total revenue by summing the 'amount' field
        total_revenue = payments.aggregate(total=Sum('amount'))['total'] or 0.00
        # Calculate the count of payments
        result = payments.aggregate(count=Count('id'))
        payment_count = result['count'] if result['count'] is not None else 0
        
        # Count the number of memberships and sum amounts by payment plan
        membership_types = payments.values('plan').annotate(
            count=Count('id'),
            total_amount=Sum('amount')
        )
        
        # Create a formatted response
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
            ]
        }
        return JsonResponse(response_data)

def all_reminders(request):
    # Get current time
    current_time = timezone.now()
    
    # Get last check-in records for all members
    last_checkins = CheckInOutRecord.objects.filter(
        action='check_in'
    ).order_by('member_id', '-timestamp').distinct('member_id')
    
    # Get all active members
    active_members = Member.objects.filter(is_active=True)
    
    # Get all payment details
    payment_details = PaymentDetails.objects.filter(
        member__is_active=True
    ).order_by('member_id', '-payment_date').distinct('member_id')
    
    attendance_reminders = []
    subscription_reminders = []
    
    for member in active_members:
        member_checkin = last_checkins.filter(member=member).first()
        member_payment = payment_details.filter(member=member).first()
        
        # Check for attendance reminder (7 days without check-in)
        if member_checkin and (current_time - member_checkin.timestamp).days >= 7:
            attendance_reminders.append({
                'member_id': member.id,
                'name': str(member),
                'days_absent': (current_time - member_checkin.timestamp).days,
                'type': 'attendance'
            })
        
        # Check for subscription reminder
        if member_payment:
            # Calculate expiry date based on payment plan
            if member_payment.plan == 'daily':
                expiry_date = member_payment.payment_date + timedelta(days=1)
            elif member_payment.plan == 'monthly':
                expiry_date = member_payment.payment_date + timedelta(days=30)
            elif member_payment.plan == 'quarterly':
                expiry_date = member_payment.payment_date + timedelta(days=90)
            elif member_payment.plan == 'biannually':
                expiry_date = member_payment.payment_date + timedelta(days=182)
            elif member_payment.plan == 'annually':
                expiry_date = member_payment.payment_date + timedelta(days=365)
            else:  # student package
                expiry_date = member_payment.payment_date + timedelta(days=30)
            
            days_until_expiry = (expiry_date - timezone.now().date()).days
            
            if days_until_expiry <= 3 and days_until_expiry >= 0:
                subscription_reminders.append({
                    'member_id': member.id,
                    'name': str(member),
                    'days_until_expiry': days_until_expiry,
                    'last_attended': member_checkin.timestamp if member_checkin else None,
                    'type': 'subscription'
                })
    
    # Get sent reminders
    sent_reminders = gym_reminder.objects.filter(
        is_sent=True
    ).select_related('member').order_by('-created_at')
    
    context = {
        'attendance_reminders': attendance_reminders,
        'subscription_reminders': subscription_reminders,
        'sent_reminders': sent_reminders,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # If AJAX request, return JSON
        reminder_type = request.GET.get('type', 'all')
        if reminder_type == 'attendance':
            return JsonResponse({'reminders': attendance_reminders})
        elif reminder_type == 'subscription':
            return JsonResponse({'reminders': subscription_reminders})
        elif reminder_type == 'sent':
            return JsonResponse({
                'reminders': [{
                    'member_id': reminder.member.id,
                    'name': str(reminder.member),
                    'reminder': reminder.reminder,
                    'sent_date': reminder.created_at.strftime('%Y-%m-%d %H:%M'),
                    'category': reminder.category
                } for reminder in sent_reminders]
            })
        else:
            return JsonResponse({
                'attendance_reminders': attendance_reminders,
                'subscription_reminders': subscription_reminders
            })
    
    return render(request, 'reminders.html', context)

def reminders(request):
    return render(request,"reminders.html")

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
        
        messages.success(request, f'Membership for {member} has been frozen for days.')
        return redirect('Members')
    
    return render(request, 'freeze.html')
