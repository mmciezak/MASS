from django.shortcuts import render, redirect

from django.contrib.auth.forms import UserCreationForm #do logowania
from django.contrib.auth import authenticate,login, logout #^

# Create your views here.
from django.http import HttpResponse
from .models import Medication

def index(request):
    #return HttpResponse("Hello world.")
    #medications = Medication.objects.all()
    #context = {"medications" : medications}
    return render(request, 'index.html')

def products(request): # przekierowanie do strony z lista produktow
    medications = Medication.objects.all()
    context = {"medications" : medications}
    return render(request, 'products.html', context)

def loginPage(request):
    form = UserCreationForm()

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request,user)
            return redirect('index')

    context = {"form":form}
    return render(request, 'login.html', context)



def registerPage(request):
    form = UserCreationForm()


    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            #login(request, user)  # Automatyczne logowanie po rejestracji
            #return redirect('loginPage')
    else:
        form = UserCreationForm()

    context = {"form":form}
    return render(request, 'register.html', context)
