from rest_framework.decorators import api_view
from rest_framework.response import Response
from base.models import Room
from .serializers import RoomSerializer


@api_view(['GET'])
def get_routes(request):
    routes = [
        'GET /api',
        'GET /api/rooms',
        'GET /api/rooms/:id'
    ]
    return Response(routes)


@api_view(['GET'])
def get_rooms(request):
    rooms = Room.objects.all()
    serializer = RoomSerializer(rooms, many=True)  # to check if there are multiple objects we need to serialize
    return Response(serializer.data)


@api_view(['GET'])
def get_room(request, key):
    rooms = Room.objects.get(id=key)
    serializer = RoomSerializer(rooms, many=False)  # to check if there are multiple objects we need to serialize
    return Response(serializer.data)
