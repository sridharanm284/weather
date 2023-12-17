from rest_framework import serializers
from .models import *

class ForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastID
        fields = ('__all__')

class ObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObservationForm
        fields = ('__all__')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginUsers
        fields = ('__all__')

class FileSerializer(serializers.ModelSerializer):
    imgfile = serializers.SerializerMethodField('get_image_url')
    file_name = serializers.SerializerMethodField('file_type1')

    class Meta:
        model = Chat
        fields = ('message','date_time','user_type','chat_id','imgfile','file_name')
        
    def get_image_url(self, obj):
        if obj.file:  
            l=f'http://localhost:8000{obj.file.url}'
            return l
        else:
            return None
        
    def file_type1(self, obj):
        if obj.file:  # Check if 'file' attribute exists and has a value
            return obj.file.name[8:]
        else:
            return None


class LoginUsersSerializers(serializers.ModelSerializer):
    class Meta:
        model = LoginUsers
        fields = '__all__'