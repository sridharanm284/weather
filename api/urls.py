from django.urls import path
from .views import *

urlpatterns = [
    path('', api_root),
    path('forecast/', ForecastAPI.as_view(), name='forecast'),
    path('overview/', OverviewAPI.as_view(), name='overview'),
    path('weather/', WeatherAPI.as_view(), name='weather'),
    path('observation/', ObservationAPI.as_view(), name='observation'),
    path('login/', login, name='login'),
    path('setoperation/',setOperation, name='setOperation'),
    path('chatroom/<str:abc>/', createChat, name='chat'),
    path('sendmessage/',sendMessage, name='sendMessage'),
    path('readmessages/',readMessages, name='readMessages'),
    path('listchats/',ChatsList, name='listchats'),
    path('operations/<str:daa>/',getDataForecast, name='sd'),
    path('user/save/',saveuserData, name='sd'),
    path('user/get/',getUsers, name='getusers'),
    path('user/get/<str:id>/',detailsUsers, name='getusers'),
    path('getclients/',getClientNames,name="ddf"),
    path('getfiles/<str:fid>/',getFilesDasta,name="sdsd"),
    path('getlatlon/<str:forecast_id>/',getLatLonRequest,name="latlon"),
    path('typhoon/<str:forecast_id>/',typhoonDatas,name="typhoon"),
    path('stormdatas/',stormDatas,name="stormdatas"),
    path('lastedited/<str:forecast_id>/',getLastEdited,name="lastedited"),  
    path('getplaceholder/<str:forecast_id>', getPlaceHolder, name="getPlaceHolder"),
    path('send-email/', send_email, name='send-email'),
]