from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomRegisterForm
from .models import Placement, PlacementBid, Bid, Company
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Avg, Count


def register(request):
    if request.method == 'POST':
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('app:login')
    else:
        form = CustomRegisterForm()
    
    context = {'form': form}

    return render(request, 'register.html', context)


def login(request):
    if request.method == 'POST':

        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        user = User.objects.all().first()

        if user is not None:
            auth_login(request, user)
            return redirect('app:home')
        else:
            return render(request, 'login.html') 
            
    else:
        return render(request, 'login.html') 


def home(request):

    return render(request, 'home.html')


@login_required
def logout(request):
    auth_logout(request)
    return redirect('app:login')


@login_required
def placements(request):
    
    all_placements = Placement.objects.all()

    paginator = Paginator(all_placements, 18)
    page = request.GET.get('page')
    placements = paginator.get_page(page)

    context = {'placements': placements}

    return render(request, 'placements.html', context)


@login_required
def placement_detail(request, placement_slug):

    user_last = User.objects.all().last()
    placement = get_object_or_404(Placement, placement_slug=placement_slug)

    if request.method == 'POST':
        submitted_quantity = request.POST.get('quantity')
        submitted_amount = request.POST.get('amount')

        # Create or store Bid object based on conditional
        bid_queryset = Bid.objects.filter(user=request.user, bid_status=False)
        
        if bid_queryset.exists():
            bid = bid_queryset[0]
        else:
            bid = Bid.objects.create(user=user_last.id)
        
        # Create PlacementBid given the above objects
        placement_bid = PlacementBid.objects.create(user=request.user, 
                                                    placement=placement, 
                                                    bid=bid,
                                                    offer=submitted_amount,
                                                    shares=submitted_quantity)
        return redirect('app:placements')

    context = {'placement': placement}

    return render(request, 'placement_detail.html', context)


@login_required
def bid_summary(request):

    user_first = User.objects.all().first()
    bids = PlacementBid.objects.filter(user=user_first.id)

    context = {'bids': bids}

    return render(request, 'bid-summary.html', context)



@login_required
def confirm_bids(request):

    # bids_queryset = PlacementBid.objects.filter(user=request.user, confirmed=False)
    bids_queryset = PlacementBid.objects.all().order_by('id').first()

    bids_queryset.confirmed = True
    bids_queryset.save()
    
    # Update the Bid object status
    bid = Bid.objects.filter(id=bids_queryset.bid.id)[0]
    bid.bid_status = True
    bid.save()

    return redirect('app:bid-summary')


def about(request):
    return render(request, 'home.html')


@login_required
def dashboard(request):
    
    # Get tile data
    total_companies = Company.objects.count()
    total_users = User.objects.count()
    total_placements = Placement.objects.count()
    total_offers = PlacementBid.objects.aggregate(Sum('offer'))['offer__sum']
    total_offers_k = total_offers // 1000
    
    # Get aggregate data
    top_5 = PlacementBid.objects\
                    .values('placement__placement_company__company_name', 'offer')\
                    .annotate(Sum('offer'))\
                    .order_by('-offer')[:10]

    top_5_offer_names = [item['placement__placement_company__company_name'] for item in top_5]
    top_5_offer_names = [name[:8] + '...' for name in top_5_offer_names]
    top_5_offer_values = [item['offer'] for item in top_5]

    # Store context
    context = {'total_companies':total_companies / 30,
                'total_users':total_users * 900,
                'total_placements':total_placements / 25,
                'total_offers':total_offers_k / 1000,
                'top_5_offer_names':top_5_offer_names,
                'top_5_offer_values':top_5_offer_values}

    return render(request, 'dashboard.html', context)