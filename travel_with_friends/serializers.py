from rest_framework import serializers
from travel_with_friends.models import AuthUser, FullTripTable
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from rest_auth.serializers import UserDetailsSerializer

class FullTripSearchSerializer(serializers.Serializer):
    city = serializers.CharField()
    state = serializers.CharField()
    n_days = serializers.CharField()

class OutsideTripSearchSerializer(serializers.Serializer):
    city = serializers.CharField()
    state = serializers.CharField()
    direction = serializers.CharField()

class CityStateSearchSerializer(serializers.Serializer):
    city_state = serializers.CharField()
    
class FullTripSuggestDeleteSerializer(serializers.Serializer):
    full_trip_id = serializers.CharField()
    event_id = serializers.CharField()
    trip_location_id = serializers.CharField()

class FullTripSuggestConfirmSerializer(serializers.Serializer):
    full_trip_id = serializers.CharField()
    event_id = serializers.CharField()
    trip_location_id = serializers.CharField()

class FullTripAddSearchSerializer(serializers.Serializer):
    full_trip_id = serializers.CharField()
    poi_name = serializers.CharField(allow_blank=True)
    trip_location_id = serializers.CharField()

class FullTripSuggestPopSearchSerializer(serializers.Serializer):
    trip_location_id = serializers.CharField()

class FullTripAddEventSerializer(serializers.Serializer):
    poi_id = serializers.CharField(allow_blank=True)
    poi_name = serializers.CharField(allow_blank=True)
    trip_location_id = serializers.CharField()
    full_trip_id = serializers.CharField()

class FullTripAutoAddEventSerializer(serializers.Serializer):
    trip_location_id = serializers.CharField()
    full_trip_id = serializers.CharField()

class OutsideTripAddSearchSerializer(serializers.Serializer):
    outside_trip_id = serializers.CharField()
    poi_name = serializers.CharField(allow_blank=True)
    outside_route_id = serializers.CharField()

class NightlifeCitySearchSerializer(serializers.Serializer):
    city = serializers.CharField()
    state = serializers.CharField()
    hotel_address= serializers.CharField()
    full_trip_id = serializers.CharField()

class NewPOISeasonalSerializer(serializers.Serializer):
    poi_name = serializers.CharField()
    season= serializers.CharField()

class UpdatePOIAddressSerializer(serializers.Serializer):
    address= serializers.CharField()

class NewPOIDetailSerializer(serializers.Serializer):
    poi_name = serializers.CharField()
    address = serializers.CharField()
    desc = serializers.CharField()
    photo_src = serializers.CharField()
    desc = serializers.CharField()
    poi_type = serializers.CharField()
    visit_length = serializers.CharField()
    rating = serializers.CharField()
    num_review = serializers.CharField()

class SendEmailFullTripSerializer(serializers.Serializer):
    email = serializers.CharField()
    full_trip_id = serializers.CharField()
    
class IPGeoLocationSerializer(serializers.Serializer):
    ip = serializers.CharField()
# class UserSerializer(serializers.ModelSerializer):
#     snippets = serializers.PrimaryKeyRelatedField(many=True, queryset=FullTripTable.objects.all())
#     class Meta:
#         model = AuthUser
#         fields = ('id', 'username', 'snippets')
# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = get_user_model()
#         fields = ('password', 'username', 'email',)
#         write_only_fields = ('password',)
#         read_only_fields = ('is_staff', 'is_superuser', 'is_active', 'date_joined',)

class FullTripTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = FullTripTable
        fields = ('index','full_trip_id', 'details')

class UserSerializer(UserDetailsSerializer):
    # full_trips = FullTripTableSerializer()
    full_trips = serializers.SlugRelatedField(many=True,read_only=True,slug_field='full_trip_id')
    outside_trips = serializers.SlugRelatedField(many=True,read_only=True,slug_field='outside_trip_id')
    # full_trip_id = serializers.CharField(source='full_trips')
    # outside_trips = serializers.PrimaryKeyRelatedField(many=True,read_only=True)
    # snippets = serializers.PrimaryKeyRelatedField(many=True, queryset=FullTripTable.objects.all())
    class Meta:
        model = User
        fields = UserDetailsSerializer.Meta.fields + ('full_trips','outside_trips')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

