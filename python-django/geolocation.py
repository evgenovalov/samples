import requests
import json

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api_v0.serializers.maps_2gis_serializers import GeoObjectSerializer, CoordsSerializer
from symphony.settings import MAPS_2GIS_API_URL, MAPS_2GIS_API_KEY


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_coords(request):
    serializer = GeoObjectSerializer(data=request.data)

    if serializer.is_valid():
        payload = {
            'key': MAPS_2GIS_API_KEY,
            'q': serializer.validated_data.get('query'),
            'page_size': 15,
            'fields': 'items.geometry.selection',
            'region_id': 18,
            'type': 'building',
            'locale': 'ru_RU'
        }

        request = requests.get(MAPS_2GIS_API_URL, params=payload)
        if request.status_code == requests.codes.ok:
            return Response(data=json.loads(request.text), status=status.HTTP_200_OK)
        else:
            return Response(data=json.loads(request.text), status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_address(request):
    serializer = CoordsSerializer(data=request.data)

    if serializer.is_valid():
        coords = '%f%s%f' % (serializer.validated_data.get('lon'), ', ', serializer.validated_data.get('lat'))

        payload = {
            'key': MAPS_2GIS_API_KEY,
            'point': coords,
            'page_size': 15,
            'fields': 'items.geometry.selection',
            'type': 'building',
            'locale': 'ru_RU'
        }

        request = requests.get(MAPS_2GIS_API_URL, params=payload)
        if request.status_code == requests.codes.ok:
            return Response(data=json.loads(request.text), status=status.HTTP_200_OK)
        else:
            return Response(data=json.loads(request.text), status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
