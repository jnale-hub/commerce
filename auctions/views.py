from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from markdown2 import Markdown
from datetime import datetime


from .models import User, Category, Listing, Comment, Bid

# For rendering paragraphs
markdowner = Markdown()

def listing (request, id):
    listing = Listing.objects.get(pk=id)
    if request.user.is_authenticated:
        count = len(request.user.listingWatchlist.all())
    else:
        count = None
    
    return render(request, "auctions\listing.html", {
        "listing": listing,
        "isListingInWatchlist": request.user in listing.watchlist.all(),
        "allComments": Comment.objects.filter(listing=listing),
        "isOwner": request.user.username == listing.owner.username,
        "watchlistCount": count
    })

def close_auction(request, id):
    listing = Listing.objects.get(pk=id)
    listing.isActive = False
    listing.save()

    return render(request, "auctions\listing.html", {
        "listing": listing,
        "isListingInWatchlist": request.user in listing.watchlist.all(),
        "description": markdowner.convert(listing.description),
        "allComments": Comment.objects.filter(listing=listing),
        "isOwner": request.user.username == listing.owner.username,
        "watchlistCount": len(request.user.listingWatchlist.all())
    })

def add_bid(request,id):
    newBid = request.POST['newBid']
    listing = Listing.objects.get(pk=id)

    if int(newBid) > listing.price.bid:
        updateBid = Bid(user=request.user, bid=newBid)
        updateBid.save()

        listing.price = updateBid
        listing.bidCount = listing.bidCount + 1
        listing.save()
        return render(request, "auctions/listing.html", {
            "listing": listing,
            "message": "Bid successful",
            "update": True,
            "description": markdowner.convert(listing.description),
            "allComments": Comment.objects.filter(listing=listing),
            "watchlistCount": len(request.user.listingWatchlist.all())
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing": listing,
            "message": "Bid Failed", 
            "update": False,
            "description": markdowner.convert(listing.description),
            "allComments": Comment.objects.filter(listing=listing),
            "watchlistCount": len(request.user.listingWatchlist.all())
        })


def add_comment(request, id):

    newComment = Comment(
        author=request.user,
        listing=Listing.objects.get(pk=id),
        message=request.POST['comment'],
        date=datetime.now()
    )
    newComment.save()
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def remove_watchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    listingData.watchlist.remove(request.user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))
 
def add_watchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    listingData.watchlist.add(request.user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def display_watchlist(request):
    return render(request, "auctions/watchlist.html", {
        "listings": request.user.listingWatchlist.all(),
        "watchlistCount": len(request.user.listingWatchlist.all())
    })

def index(request):
    if request.user.is_authenticated:
        count = len(request.user.listingWatchlist.all())
    else:
        count = None

    return render(request, "auctions/index.html", {
        "listings": Listing.objects.filter(isActive=True),
        "categories": Category.objects.all(),
        "watchlistCount": count,
    })

def categories(request):
    return render(request, "auctions/categories.html", {
        "listings": Listing.objects.filter(isActive=True),
        "categories": Category.objects.all(),
        "watchlistCount": len(request.user.listingWatchlist.all())
    })
 
def display_category(request):
    if request.method == 'POST':
        category = Category.objects.get(categoryName=request.POST['category'])
        categoryListings = Listing.objects.filter(isActive=True, category=category)
        return render(request, "auctions/categories.html", {
            "listings": categoryListings,
            "categories": Category.objects.all(),
            "category": category,
            "watchlistCount": len(request.user.listingWatchlist.all())
        })

def create_listing(request):
    if request.method == "GET":
        return render(request, "auctions/create.html", {
            "categories": Category.objects.all(),
            "watchlistCount": len(request.user.listingWatchlist.all())
        })
    
    else:
        price = request.POST["price"]
        category = request.POST["category"]
        currentUser = request.user
        bid = Bid(bid=price, user=currentUser)
        bid.save()

        f = Listing(
            title=request.POST["title"],
            description=markdowner.convert(request.POST["description"]),
            imageUrl=request.POST["imgUrl"],
            initialPrice=price,
            price=bid,
            category=Category.objects.get(categoryName=category),
            owner=currentUser,
            date=datetime.now()
        )
        f.save()
        return HttpResponseRedirect(reverse(index))


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
 
        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
