# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# from snippets.models import Snippet
# from snippets.serializers import SnippetSerializer
from rest_framework import generics, status
from django.contrib.auth.models import User
from travel_with_friends.serializers import UserSerializer, FullTripSearchSerializer, \
    OutsideTripSearchSerializer,CityStateSearchSerializer, FullTripSuggestDeleteSerializer, \
    FullTripAddSearchSerializer, FullTripAddEventSerializer, FullTripSuggestConfirmSerializer, \
    IPGeoLocationSerializer, OutsideTripAddSearchSerializer, FullTripAutoAddEventSerializer,\
    FullTripSuggestPopSearchSerializer, NightlifeCitySearchSerializer, NewPOISeasonalSerializer,\
    SendEmailFullTripSerializer, UpdatePOIAddressSerializer, NewPOIDetailSerializer
from rest_framework import permissions
from travel_with_friends.permissions import IsOwnerOrReadOnly, IsStaffOrTargetUser
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework import renderers
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.views import APIView
from city_trip import *
from helpers import *
from outside_trip import outside_trip_poi, outside_one_day_trip
from outside_helpers import *
from rest_framework.permissions import AllowAny
# from django.contrib.auth import get_user_model # If used custom user model
from django.views.decorators.csrf import csrf_exempt
import trip_update
import night_trip
from send_trip_email import send_email_full_trip
from new_edit_poi import new_poi_seasonal, udpate_poi_address
'''
Get Token:
http post http://127.0.0.1:8000/account/get_auth_token/ username=test password=test1234

Get outside Trip:
http get 'http://127.0.0.1:8000/outside_trip_search/?city=San_Diego&state=California&direction=N&n_days=1'
'''
@api_view(['GET'])
def api_root(request, format=None):
    return Response({   
        'full-trips': reverse('full-trip-list', request=request, format=format),
        'users': reverse('user-list', request=request, format=format)
    })

@api_view(['POST'])
def create_auth(request):
    '''
    http post http://127.0.0.1:8000/account/register password=test1234 username=test3 email=''
    '''
    serialized = UserSerializer(data=request.data)
    permission_classes = [AllowAny]
    if serialized.is_valid():
        User.objects.create_user(
            email=serialized.data['email'], username=serialized.data['username'], password=serialized.data['password']
        )
        return Response(serialized.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)

class FullTripDetail(APIView):
    def get(self, request, full_trip_id):
        valid_full_trip = check_full_trip_id_city(full_trip_id)
        if not valid_full_trip:
            return Response({
            "error_trip_id": '%s is not a valid full trip id.' % (full_trip_id),
        }, status=400)
        full_trip_id, full_trip_details, trip_location_ids = get_exisiting_full_trip_details_city(full_trip_id)
        return Response({
            "full_trip_id": full_trip_id,
            "full_trip_details": full_trip_details,
            "trip_location_ids": trip_location_ids,
        })


class OutsideTripDetail(APIView):
    def get(self, request, outside_trip_id):
        valid_outside_trip = check_outside_trip_id(outside_trip_id)
        if not valid_outside_trip:
            return Response({
            "error_trip_id": '%s is not a valid full trip id.' % (outside_trip_id),
        }, status=400)
        outside_trip_id, outside_trip_details, trip_location_ids = get_exisiting_outside_trip_details(outside_trip_id)
        return Response({
            "outside_trip_id": outside_trip_id,
            "outside_trip_details": outside_trip_details,
            "trip_location_ids": trip_location_ids,
        })

class FullTripSearch(APIView):
    def get_permissions(self):
        '''
        myurl = 'http://127.0.0.1:8000/full_trip_search/?state=California&city=San_Francisco&n_days=1'
        response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
        response.json()
        '''

        # return (permissions.IsAuthenticated()),
        return (AllowAny() if self.request.method == 'GET'
            else permissions.IsAuthenticated()),

    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        serializer = FullTripSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        city = data["city"]
        state = data["state"]
        n_days = data["n_days"]
        # state = abb_to_full_state(state)
        checked_state = check_state(state)
        if not checked_state:
            return Response({
            "error_location": '%s is not a valid state name' % (state),
        }, status=400)

        valid_city = check_valid_city(city, checked_state)
        if not valid_city:
            return Response({
            "error_location": '%s is not valid city name for state %s' % (city, checked_state),
        }, status=400)
        full_trip_id, full_trip_details, trip_location_ids = get_city_trip_data(state=checked_state, city=city, n_days=n_days)
        
        return Response({
            "full_trip_id": full_trip_id,
            "full_trip_details": full_trip_details,
            "trip_location_ids": trip_location_ids,
        })

class OutsideTripSearch(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        serializer = OutsideTripSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        city = data["city"].replace('_',' ').title()
        state = data["state"].replace('_',' ').title()
        direction = data["direction"].upper()
        checked_state = check_state(state)
        if not checked_state:
            return Response({
            "error_location": '%s is not a valid state name' %(state),
        }, status=400)
        valid_city = check_valid_city(city, checked_state)
        if not valid_city:
            return Response({
            "error_location": '%s is not valid city name for state %s' %(city, checked_state),
        }, status=400)
        # print 'outsdie trip: ', city, state, direction
        outside_trip_id, outside_trip_details, outside_route_ids_list = outside_one_day_trip(origin_city=city, origin_state=checked_state, target_direction=direction, regular=True, username_id=1)
        if not outside_trip_details or not outside_route_ids_list:
            return Response({
            "error_no_poi": 'direction %s of  %s has no interesting place to go, please choose another direction' % (direction ,city),
        }, status=400)   
        return Response({
            "outside_trip_id": outside_trip_id,
            "outside_trip_details": outside_trip_details,
            "outside_route_ids_list": outside_route_ids_list
        })

class CityStateSearch(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        serializer = CityStateSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        city_state = data["city_state"]
        city_state = serach_city_state(city_state)
        city = [i[0] for i in city_state]
        state = [i[1] for i in city_state]
        city_and_state = [i[2] for i in city_state]

        return Response({
            "city_state": city_and_state,
            "city": city,
            "state": state
        })

class FullTripDeleteEvent(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        serializer = FullTripSuggestDeleteSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        full_trip_id=data["full_trip_id"]
        event_id = data["event_id"]
        trip_location_id = data["trip_location_id"]
        username_id = 1
        new_full_trip_id, new_full_trip_details, new_trip_location_ids, current_trip_location_id = trip_update.remove_event(full_trip_id, trip_location_id, event_id, username_id)
        return Response({
            "full_trip_id": new_full_trip_id,
            "full_trip_details": new_full_trip_details,
            "trip_location_ids": new_trip_location_ids,
            "current_trip_location_id": current_trip_location_id
        })

class FullTripAddSearch(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        serializer = FullTripAddSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        full_trip_id=data["full_trip_id"]
        poi_name = data["poi_name"]
        trip_location_id = data["trip_location_id"]
        poi_dict, poi_names = trip_update.add_search_event(poi_name, trip_location_id)
        return Response({
            "poi_dict": poi_dict,
            "poi_names": poi_names,
        })

class FullTripSuggestPopSearch(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        serializer = FullTripSuggestPopSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        trip_location_id = data["trip_location_id"]
        poi_dict_list = trip_update.suggest_search_pop_events(trip_location_id)
        return Response({
            "poi_dict_list": poi_dict_list
        })


class FullTripAddEvent(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        
        serializer = FullTripAddEventSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        full_trip_id=data["full_trip_id"]
        poi_name = data["poi_name"]
        poi_id = data["poi_id"] if data["poi_id"] != 'undefined' else None
        trip_location_id = data["trip_location_id"]
        old_trip_location_id,new_trip_location_id, new_day_details = trip_update.add_event_day_trip(poi_id, poi_name, trip_location_id, full_trip_id)
        full_trip_id, trip_location_ids, full_trip_details = trip_update.add_event_full_trip(full_trip_id, old_trip_location_id, new_trip_location_id, new_day_details)
        return Response({
            "full_trip_details": full_trip_details,
            "full_trip_id": full_trip_id,
            "trip_location_ids": trip_location_ids,
            "current_trip_location_id": new_trip_location_id,
        })


class FullTripAutoAddEvent(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        
        serializer = FullTripAutoAddEventSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        full_trip_id=data["full_trip_id"]
        trip_location_id = data["trip_location_id"]
        full_trip_id, trip_location_ids, full_trip_details,trip_location_id = trip_update.auto_add_events_full_trip(trip_location_id, full_trip_id)
        return Response({
            "full_trip_details": full_trip_details,
            "full_trip_id": full_trip_id,
            "trip_location_ids": trip_location_ids,
            "current_trip_location_id": trip_location_id,
        })

class FullTripSuggestArray(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        serializer = FullTripSuggestDeleteSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        full_trip_id=data["full_trip_id"]
        event_id = data["event_id"]
        trip_location_id = data["trip_location_id"]
        username_id = 1
        suggest_event_array = trip_update.suggest_event_array(full_trip_id, trip_location_id, event_id, username_id)
        if not suggest_event_array:
            return Response({
            "error_no_suggestion": 'No other place in the near area as good as this place'
        }, status=400)

        return Response({
            "suggest_event_array": suggest_event_array,
        })

class FullTripSuggestConfirm(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def post(self, request):
        # Validate the incoming input (provided through query parameters)
        # serializer = FullTripSuggestConfirmSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # Get the model input
        data = request.data
        full_trip_id=data["fullTripId"]
        update_suggest_event = data["updateSuggestEvent"]
        update_trip_location_id = data["updateTripLocationId"]
        username_id = 1

        new_full_trip_id, new_full_trip_details, full_trip_trip_locations_id, new_update_trip_location_id = trip_update.switch_suggest_event(full_trip_id, update_trip_location_id, update_suggest_event, username_id)
        return Response({
            "full_trip_id": new_full_trip_id,
            "full_trip_details": new_full_trip_details,
            "trip_location_ids": full_trip_trip_locations_id,
            "current_trip_location_id": new_update_trip_location_id,
        })

class FullTripCreate(APIView):
    def get_permissions(self):
        '''
        response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
        '''
        return (permissions.IsAuthenticated()),
    def post(self, request):
        # Validate the incoming input (provided through query parameters)
        # serializer = FullTripSuggestConfirmSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # Get the model input
        data = request.data
        username = request.user.username
        username_id = User.objects.get(username=username).pk
        full_trip_id= data["fullTripId"]
        response = trip_update.create_full_trip(full_trip_id, username_id)
        return Response({
            "response": response,
        })

class OutsideTripAddSearch(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        serializer = OutsideTripAddSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        outside_trip_id = data["outside_trip_id"]
        poi_name = data["poi_name"]
        outside_route_id = data["outside_route_id"]

        # poi_dict, poi_names = trip_update.outside_add_search_event(poi_name, outside_route_id)
        poi_names, poi_dict = trip_update.outside_add_search_event(poi_name, outside_route_id)

        return Response({
            "poi_dict": poi_dict,
            "poi_names": poi_names,
        })

class OutsideTripAddEvent(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
        # return (AllowAny() if self.request.method == 'POST'
        #         else permissions.IsAuthenticated()),
    def get(self, request):
        # Validate the incoming input (provided through query parameters)
        
        serializer = FullTripAddEventSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        full_trip_id=data["full_trip_id"]
        poi_name = data["poi_name"]
        poi_id = data["poi_id"] if data["poi_id"] != 'undefined' else None
        trip_location_id = data["trip_location_id"]
        old_trip_location_id,new_trip_location_id, new_day_details = trip_update.add_event_day_trip(poi_id, poi_name, trip_location_id, full_trip_id)
        full_trip_id, trip_location_ids, full_trip_details = trip_update.add_event_full_trip(full_trip_id, old_trip_location_id, new_trip_location_id, new_day_details)
        return Response({
            "full_trip_details": full_trip_details,
            "full_trip_id": full_trip_id,
            "trip_location_ids": trip_location_ids,
            "current_trip_location_id": new_trip_location_id,
        })

class NightlifeCitySearch(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
    def post(self, request):
        data = request.data
        serializer = NightlifeCitySearchSerializer(data=data)
        if serializer.is_valid():
            city = data['city']
            state = data['state']
            hotel_address=data["hotel_address"]
            full_trip_id = data["full_trip_id"]
            username_id = 1
            # username = request.user.username
            # username_id = User.objects.get(username=username).pk
            night_life_events_details, night_life_events_ids = night_trip.nightlife_city_search(hotel_address, city, state,full_trip_id)
            return Response({
                "night_life_events_details": night_life_events_details,
                "night_life_events_ids": night_life_events_ids
            })
        else:
            return Response({"error": serializer.errors}) 

class NewPOISeasonal(APIView):
    #Admin append new seasonal poi to database table
    def post(self, request):
        data = request.data
        serializer = NewPOISeasonalSerializer(data=data)
        if serializer.is_valid():
            poi_name = data['poi_name']
            result = new_poi_seasonal(data)
            if result: 
                return Response({
                    "ok": poi_name + " inserted."
                },200)
            else: 
                return Response({"error": 'data not complete'},404) 
        else:
            return Response({"error": serializer.errors},404) 

class UpdatePOIAddress(APIView):
    #Admin update poi address in database table
    def post(self, request):
        data = request.data
        serializer = UpdatePOIAddressSerializer(data=data)
        if serializer.is_valid():
            result = udpate_poi_address(data)
            if result: 
                return Response({
                    "ok": "updated poi address."
                },200)
            else: 
                return Response({"error": 'data not complete'},404) 
        else:
            return Response({"error": serializer.errors},404) 

class NewPOIDetail(APIView):
    #Admin update poi address in database table
    def post(self, request):
        data = request.data
        serializer = NewPOIDetailSerializer(data=data)
        if serializer.is_valid():
            result = new_poi_detail(data)
            if result: 
                return Response({
                    "ok": "Added new poi detail."
                },200)
            else: 
                return Response({"error": 'data not complete'},404) 
        else:
            return Response({"error": serializer.errors},404) 

class SendEmailFullTrip(APIView):
    def post(self, request):
        data = request.data
        serializer = SendEmailFullTripSerializer(data=data)
        if serializer.is_valid():
            email_address = data['email']
            full_trip_id = data['full_trip_id']
            send_email_full_trip(email_address,full_trip_id)
            return Response({
                "ok": 'sending trip %s to %s'%(email_address,full_trip_id)
            })
        else:
            return Response({"error": serializer.errors}) 


class IPGeoLocation(APIView):
    # def get_permissions(self):
    #     '''
    #     response = requests.get(myurl, headers={'Authorization': 'Token {}'.format(mytoken)})
    #     '''
    #     return (permissions.IsAuthenticated()),
    def get(self,request):
        # Validate the incoming input (provided through query parameters)
        # serializer = FullTripSuggestConfirmSerializer(data=request.data)
        # serializer.is_valid(raise_exception=True)
        # Get the model input
        serializer = IPGeoLocationSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        # Get the model input
        data = serializer.validated_data
        country_code, country_name, region_name, city_name = find_ip_geo_location(data['ip'])
        return Response({
            "country_code": country_code,
            "country_name": country_name,
            "region_name": region_name,
            "city_name": city_name
        })

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


# class UserView(viewsets.ModelViewSet):
#     serializer_class = UserSerializer
#     model = User    
#     def get_permissions(self):
#         # allow non-authenticated user to create via POST
#         return (AllowAny() if self.request.method == 'POST'
#                 else IsStaffOrTargetUser()),


# @api_view(['POST'])
# @csrf_exempt
# class CreateUserView(generics.CreateAPIView):

#     model = User
#     permission_classes = [
#         AllowAny # Or anon users can't register
#     ]
#     serializer_class = UserSerializer
