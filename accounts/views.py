from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import SignUpForm
from django.http import HttpResponse
from django.contrib.auth.models import User



def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully!")
            return redirect('login')
    else:
        form = SignUpForm() 
    return render(request, "signup.html", {"form": form})



def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, "login.html")


def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        new_password = request.POST.get("password")
        if not username or not new_password:
            messages.error(request, "Please fill all fields")
            return render(request, 'forgot_password.html')
        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)  
            user.save()
            messages.success(
                request,
                "Password updated successfully! Please login."
            )
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "Username does not exist")
    return render(request, 'forgot_password.html')

def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("login")
