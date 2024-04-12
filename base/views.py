from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Room, Topic, Message, User
from .forms import RoomForm, MessageForm, UserForm, MyUserCreationForm
from django.db.models import Q


# Create your views here.

def login_page(request):
    page = "login"
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        body = request.POST
        email = body.get("email").lower()
        password = body.get("password")
        try:
            User.objects.get(username=email)
        except:
            messages.error(request, "User does not exist.")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Incorrect credentials")

    context = {"page": page}
    return render(request, 'base/login_register.html', context)


def register_page(request):
    form = MyUserCreationForm()
    if request.method == "POST":
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            print(form.error_messages)
            print("--------")
            print(form.errors)
            messages.error(request, 'error occurred during validation')
    context = {"form": form}

    return render(request, 'base/login_register.html', context)


def log_out(request):
    logout(request)
    return redirect('home')


def home(request):
    q = request.GET.get("q", '')
    # query to parent
    rooms = Room.objects.filter(Q(topic__name__icontains=q) |
                                Q(name__icontains=q) |
                                Q(description__icontains=q)
                                )
    # topics = Topic.objects.all()
    topics = Topic.objects.all()[0:5]
    room_messages = Message.objects.filter(Q(room__name__icontains=q) | Q(room__topic__name__icontains=q))
    # room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {'rooms': rooms, "topics": topics, "room_messages": room_messages}
    return render(request, "base/home.html", context)


def room(request, key):
    room = Room.objects.get(id=key)
    room_messages = room.message_set.all().order_by('-created')  # querying the child table
    participants = room.participants.all()
    if request.method == "POST":
        Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get("body")
        )
        room.participants.add(request.user)
        return redirect('room', room.id)
    context = {"room": room, "room_messages": room_messages, "participants": participants}
    return render(request, "base/room.html", context)


@login_required(login_url='/login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == "POST":
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name)
        # form = RoomForm(request.POST)
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get("name"),
            description=request.POST.get("description"),

        )
        # if form.is_valid():
        #     room = form.save(commit=False)
        #     room.host = request.user
        #     room.save()
        return redirect('home')
    context = {"form": form, "topics": topics}
    return render(request, "base/room_form.html", context)


@login_required(login_url='/login')
def update_room(request, key):
    room = Room.objects.get(id=key)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse('you are not allowed to do it')
    if request.method == "POST":
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get("name")
        room.topic = topic
        room.description = request.POST.get("description")
        room.save()
        # form = RoomForm(request.POST, instance=room)
        # if form.is_valid():
        #     form.save()
        return redirect('home')
    context = {"form": form, "topics": topics, "room": room}
    return render(request, "base/room_form.html", context)


@login_required(login_url='/login')
def delete_room(request, key):
    room = Room.objects.get(id=key)
    if request.user != room.host:
        return HttpResponse('you are not allowed to do it')
    if request.method == "POST":
        room.delete()
        return redirect('home')
    return render(request, "base/delete.html", {'obj': room})


@login_required(login_url="/login")
def delete_message(request, key):
    message = Message.objects.get(id=key)
    room_id = message.room.id
    if request.user != message.user:
        return HttpResponse('you are not allowed to do it')
    if request.method == "POST":
        message.delete()
        return redirect('room', room_id)
    return render(request, "base/delete.html", {'obj': message})


@login_required(login_url='/login')
def update_message(request, key):
    message = Message.objects.get(id=key)
    form = MessageForm(instance=message)
    if request.user != message.user:
        return HttpResponse('you are not allowed to do it')
    if request.method == "POST":
        form = MessageForm(request.POST, instance=message)
        room_id = message.room.id
        if form.is_valid():
            form.save()
            return redirect('room', room_id)
    context = {"form": form}
    return render(request, "base/message_form.html", context)


def user_profile(request, key):
    user = User.objects.get(id=key)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {"user": user, "rooms": rooms, "room_messages": room_messages, "topics": topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url="/login")
def update_user(request):
    user = request.user
    form = UserForm(instance=user)
    context = {
        "form": form
    }
    if request.method == "POST":
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect("user_profile", key=user.id)
    return render(request, "base/update_user.html", context)


def topics_page(request):
    q = request.GET.get("q", '')
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, "base/topics.html", {"topics": topics})


def activities_page(request):
    room_messages = Message.objects.all()
    return render(request, "base/activity.html", {"room_messages": room_messages})
