from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import Room, Topic, Message, User
from .forms import RoomForm, MessageForm, UserForm, MyUserCreationForm, PinForm
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
            messages.error(request, form.errors)
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


def room_auth(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        form = PinForm()
        room_data = Room.objects.get(id=kwargs.get("key"))
        if (args[0].user in room_data.participants.all()
                or room_data.access == "public"
                or args[0].user == room_data.host):
            return function(*args, **kwargs)
        if args[0].method == 'POST':
            pin = args[0].POST.get("pin")
            if pin == room_data.pin:
                args[0].method = 'GET'
                if args[0].user.is_authenticated:
                    room_data.participants.add(args[0].user)
                return function(*args, **kwargs)
            else:
                messages.error(*args, "incorrect pin")
        return render(*args, "base/pin_input.html", {"form": form})

    return wrapper


@room_auth
def room(request, key):
    room = Room.objects.get(id=key)
    room_messages = room.message_set.all().order_by('-created')  # querying the child table
    participants = room.participants.all()

    context = {"room": room, "room_messages": room_messages, "participants": participants}
    return render(request, "base/room.html", context)


def add_comments(request, key):
    room = Room.objects.get(id=key)

    Message.objects.create(
        user=request.user,
        room=room,
        body=request.POST.get("body")
    )
    room.participants.add(request.user)
    return redirect('room', room.id)


@login_required(login_url='/login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == "POST":
        topic_name = request.POST.get("topic")
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room = Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get("name"),
            description=request.POST.get("description"),
            access=request.POST.get("access"),
            pin=request.POST.get("pin")
        )

        room.participants.set([request.user])
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
        room.pin = request.POST.get("pin")
        room.description = request.POST.get("description")
        room.access = request.POST.get("access")
        room.topic = topic
        room.save()
        return redirect('home')
    context = {"form": form, "topics": topics, "room": room, "page": "update"}
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


@login_required(login_url='/login')
def join_room(request, key):
    room = Room.objects.get(id=key)
    room.participants.add(request.user)
    return redirect('room', room.id)


@login_required(login_url='/login')
def leave_room(request, key):
    room = Room.objects.get(id=key)
    room.participants.remove(request.user)
    return redirect('home')
