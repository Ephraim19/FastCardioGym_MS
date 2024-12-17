# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from .models import Member, PaymentDetails, CheckInOutRecord
from django.contrib import messages
from django.db.models import Sum, Count
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from datetime import timedelta
from django.views import View
from django.utils.dateparse import parse_date

def login(request):
    return render(request, 'index.html')

def authenticate(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate
        user = User.objects.get(username=username)
        
        if user.is_superuser and user.check_password(password):
            messages.success(request, 'Successfully logged in!')
            return render(request, 'sidebar.html')
        else:
            return HttpResponse("Invalid logins")

def newmember(request):
    return render(request, 'newmember.html')

def save_member(request):
    if request.method == "POST":
        f_name = request.POST.get('fname')
        l_name = request.POST.get('lname')
        phone = request.POST.get('phone')
        info = request.POST.get('info')
        
        # Create and save the member
        member = Member.objects.create(
            first_name=f_name,
            last_name=l_name,
            phone_number=phone,
            additional_info=info
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
        payment = PaymentDetails.objects.create(
            member=member,
            plan=plan,
            amount=amount,
            transaction_id=transaction_id
        )
        print(payment)
        
        return redirect("Members")
    
    # Render payment form with member context
    return render(request, 'payment.html', {'member': member})

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
        }
        
        members_with_payments.append(member_data)
        members_with_payments.reverse()
    
    return render(request, 'allmembers.html', {
        'members': members_with_payments
    })

def checkin(request):

    # Get recent check-in/out records (last 10)
    recent_records = CheckInOutRecord.objects.select_related('member').all()[:10]
    print(recent_records)
    return render(request,"Checkin.html",{'recent_records': recent_records })
    

@csrf_exempt
@require_http_methods(["POST"])
def check_in_out(request):
    """
    Handle check-in and check-out actions via AJAX
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

        # Find or create member
        member, created = Member.objects.get_or_create(
            phone_number=member_id,
            defaults={'name': f'Member {member_id}'}
        )

        # Create check-in/out record
        record = CheckInOutRecord.objects.create(
            member=member, 
            action='check_in' if action == 'Check In' else 'check_out'
        )

        return JsonResponse({
            'status': 'success', 
            'message': f'Member {member} {action.lower()} successfull!',
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
    Retrieve member check-in/out history
    """
    member_id = request.GET.get('id', '').strip()
    
    if not member_id:
        return JsonResponse({
            'status': 'error', 
            'message': 'Member ID is required'
        }, status=400)

    try:
        member = Member.objects.get(phone_number=member_id)
        records = member.CheckinOut.all()
        
        
        # Pagination
        page_number = request.GET.get('page', 1)
        paginator = Paginator(records, 10)  # 10 records per page
        page_obj = paginator.get_page(page_number)

        return JsonResponse({
            'status': 'success',
            'records': [
                {
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
        print(response_data)
        return JsonResponse(response_data)

