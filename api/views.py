from . import fetch_datas
from rest_framework import generics
from rest_framework import status
from django.db import connections
from .serializers import * 
import os, traceback

import psycopg2, psycopg2.extras, datetime, smtplib
from rest_framework.decorators import parser_classes

import json
from .models import LoginUsers, Tokens, Chat, ChatRooms
import secrets
from .serializers import FileSerializer
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
import string

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'Forecast': reverse('forecast', request=request, format=format),
        'Overview': reverse('overview', request=request, format=format),
        'Weather': reverse('weather', request=request, format=format),
        'Observation': reverse('observation', request=request, format=format),
        'Chat Rooms': reverse('listchats', request=request, format=format),
    })
class ForecastAPI(generics.ListCreateAPIView):
    serializer_class = ForecastSerializer
    def post(self, request):
        if request.data.get('forecast_id') == None:
            return Response({'interval': [],'headers': [], 'datas': []})
        try:
            datas = fetch_datas.Forecast(request.data.get('forecast_id'))
            for _ in range(2): datas.total_headers.pop(0)
            return Response({'headers': datas.total_headers, 'datas': datas.ScrapeDatas(),'interval': datas.interval, 'discussion':datas.ReadDiscussion()})
        except:
            return Response({'interval': [],'headers': [], 'datas': []})
    def get_queryset(self):
        pass         

class OverviewAPI(generics.ListCreateAPIView):
    serializer_class = ForecastSerializer
    def post(self, request):
        if request.data.get('forecast_id') == None:
            return Response({})
        datas = fetch_datas.Overview(request.data.get('forecast_id'))
        return Response({'criteria_datas': datas.criteria_datas, 'criteria_detail_datas': datas.criteria_detail_datas, 'datas': datas.ScrapeDatas()})
    def get_queryset(self):
        pass         

class WeatherAPI(generics.ListCreateAPIView):
    serializer_class = ForecastSerializer
    def post(self, request):
        if request.data.get('forecast_id') == None:
            return Response({})
        try:
            datas = fetch_datas.Weather(request.data.get('forecast_id'))
            return Response({'criteria_datas': datas.criteria_datas, 'criteria_detail_datas': datas.criteria_detail_datas, 'datas': datas.ScrapeDatas()})
        except:
            return Response({})
    def get_queryset(self):
        pass         

class ObservationAPI(generics.ListCreateAPIView):
    serializer_class = ObservationSerializer
    def post(self, request):
        datas = {x: y for x, y in request.data.copy().items()}
        # try: datas.pop('csrfmiddlewaretoken')
        # except: pass
        fetch_datas.Observation(**datas)
        return Response(datas)
    def get_queryset(self):
        pass         

@api_view(['POST'])
def login(request):
    name=request.data.get('name')
    password=request.data.get('password')
    try:
        userdata=LoginUsers.objects.using("observation").values().get(name=name)
        if userdata['password'] == password:
            id1=userdata['id']
            token = createtoken(id1,name,userdata)
            expiry = str(userdata["expected_date"])
            if(len(expiry)==19):
                expiry = expiry[:-3:]
            expiry_datetime = datetime.datetime.strptime(expiry, "%Y-%m-%dT%H:%M")
            current_datetime = datetime.datetime.now()
            if(expiry_datetime < current_datetime and userdata["user_type"] == "user"):
                return Response({'data':'Your subscription expired.'}, status=status.HTTP_402_PAYMENT_REQUIRED)
            return Response(token, status=status.HTTP_200_OK)
        else:
            return Response({'data':'Invalid Password'},status=status.HTTP_401_UNAUTHORIZED)
    except LoginUsers.DoesNotExist:
        return Response({'data':'User not found'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def setOperation(request):
    name=request.data.get('name')
    fd=request.data.get('fd')
    try:
        userdata=LoginUsers.objects.using("observation").get(name=name)
        userdata.operation=fd
        userdata.save(using="observation")
        userdata=LoginUsers.objects.using("observation").values().get(name=name)
        return Response({'status':'success'}, status=status.HTTP_200_OK)
    except LoginUsers.DoesNotExist:
        return Response({'data':'User not found'}, status=status.HTTP_401_UNAUTHORIZED)

def createtoken(user_id,name,data):
    t=secrets.token_hex(16)
    token=Tokens(user_id=user_id,user_name=name,token=t)
    token.save(using="observation")
    usercreds = getLATLON(data['forecast_id'])
    data = {'user':name,'token':t,'user_id':user_id,'user_type':data['user_type'],'client_id':data['client_id'],'forecast_id':data['forecast_id'],'lat':usercreds['lat'],'lon':usercreds['lon'],"other":data}
    print(usercreds, data)
    return data


@api_view(['GET'])
def createChat(request,abc):
    
    user_id=abc
    userdata1 = LoginUsers.objects.using("observation").get(id=abc)
    userdata = LoginUsers.objects.using("observation").values().get(id=abc)
    try:
        room1 = ChatRooms.objects.using("observation").get(user_id=abc)
        room1.save(using="observation")
        room = ChatRooms.objects.using("observation").values().get(user_id=abc)
        chats = Chat.objects.using("observation").filter(chat_id=room['chat_id'])
        serializer = FileSerializer(chats, many=True)  
        
        for chat in serializer.data:
            if chat.get('file'):
                data['chats'].append(chat)
        
        data = {
            'rooms': room,
            'chats':serializer.data,
            'userdata': userdata,
        }
        return Response(data, status=status.HTTP_200_OK)
    except ChatRooms.DoesNotExist:
        chat=ChatRooms(user_id=user_id,chat_id=secrets.token_hex(16),user_name=userdata['name'],operation=userdata['operation'])
        chat.save(using="observation")
        rooms=ChatRooms.objects.using("observation").values().get(user_id=user_id)
        return Response({'status':'Room Created','message':rooms},status=status.HTTP_200_OK)
        

@api_view(['POST'])
@parser_classes([MultiPartParser])
def sendMessage(request):
    chat_id=request.data.get('id')
    message=request.data.get('message')
    user_type=request.data.get('user')
    msg=None
    files=request.FILES.getlist('file')
    print(chat_id,user_type,message,files)
    if files:
        for file in files:
            msg=Chat(chat_id=chat_id, message=message, user_type=user_type, file=file)
            msg.save(using="observation")
    else:
        msg=Chat(chat_id=chat_id,message=message,user_type=user_type)
        msg.save(using="observation")
    if user_type=="user":
        room=ChatRooms.objects.using("observation").get(chat_id=chat_id)
        room.read_user="false"
        room.read_admin="true"
        room.unread_admin=room.unread_admin+1
        room.save(using="observation")
    else:
        room=ChatRooms.objects.using("observation").get(chat_id=chat_id)
        room.read_user="true"
        room.read_admin="false"
        room.unread_user=room.unread_user+1
        room.save(using="observation")
    return Response({'status':'Message Sent'},status=status.HTTP_201_CREATED)
    
@api_view(['POST'])
def readMessages(request):
    chat_id=request.data.get('id')
    user_type=request.data.get('user')
    if user_type=="user":
        room=ChatRooms.objects.using("observation").get(chat_id=chat_id)
        room.read_user="false"
        room.read_admin="true"
        room.unread_user=0
        room.save(using="observation")
    else:
        room=ChatRooms.objects.using("observation").get(chat_id=chat_id)
        room.read_user="true"
        room.read_admin="false"
        room.unread_admin=0
        room.save(using="observation")
    return Response({'status':'Message Read'},status=status.HTTP_200_OK)

@api_view(['POST'])
def ChatsList(request):
    user_type=request.data.get('user')
    get_user_id=Tokens.objects.using("observation").values().get(token=user_type)
    get_user=LoginUsers.objects.using("observation").values().get(id=get_user_id['user_id'])
    if get_user['user_type']=="admin":
        rooms=ChatRooms.objects.all().using('observation').values()
        return Response(rooms,status=status.HTTP_200_OK)
    else:
        return Response({'status':'only admin can access this page'},status=status.HTTP_401_UNAUTHORIZED)

def getRoute(data):
    conn = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT route_name FROM tbl_route WHERE route_id='{data}'")
        new1=cur.fetchall()
        return new1[0][0]
    except:
        pass
    
def getRegion(data):
    conn = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT region_name FROM tbl_region WHERE region_id='{data}'")
        new1=cur.fetchall()
        return new1[0][0]
    except:
        pass
    
@api_view(['GET'])
def getDataForecast(request,daa):
    conn = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    cur1 = conn1.cursor()
    cur = conn.cursor()
    cur1.execute(f"SELECT client_id FROM tbl_client WHERE client_id='{daa}'")
    d=cur1.fetchall()
    xy=None
    for l in d:
        xy=l[0]
    cur.execute(f"SELECT forecast_id,forecast_description,client_id,contract_number,latitude,longitude,region_id,route_id,vessel_rig_platform_name,start_date,expected_end_date, is_deleted FROM tbl_forecast WHERE client_id='{xy}' AND is_deleted=false")
    rows = cur.fetchall()
    print(rows)
    data = []
    for row in rows:
        data.append({
            "forecast_id": row[0],
            "forecast_description": row[1],
            "client_id": row[2],
            "contract_number": row[3],
            "region_id": getRegion(row[6]),
            "vessel_rig_platform_name": row[8],
            "lat": row[4],
            "long": row[5],
            "route":getRoute(row[7]),
            "start_date": row[9],
            "expected_end_date": row[10],
            "is_deleted":row[11]
        })
    return Response(data,status=status.HTTP_200_OK)

@api_view(['POST'])
def saveuserData(request):
    serializer = LoginUsersSerializers(data=request.data)
    if serializer.is_valid():
        validated_data = serializer.validated_data
        LoginUsers.objects.using('observation').create(**validated_data) 
        latest_record = LoginUsers.objects.using('observation').latest('id')
        values={'id':latest_record.id}

        id_length = 32
        characters = string.hexdigits
        random_id = ''.join(secrets.choice(characters) for _ in range(id_length))
        if latest_record.user_type == "admin":
            message = False
            view = True
        else:
            message = True
            view = False
        chatroomCreate = ChatRooms(user_id=latest_record.id,chat_id=random_id,operation=latest_record.operation,user_name=latest_record.name,unread_user=0,unread_admin=0,read_admin=message,read_user=view)
        chatroomCreate.save(using="observation")
        return Response({'status':'saved','values':values},status=status.HTTP_200_OK)
    else:
        return Response({'status':'invalid data'},status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def getUsers(request):
    data=LoginUsers.objects.all().values().using('observation')
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET', 'UPDATE', 'DELETE', 'PUT'])
def detailsUsers(request, id):
    if request.method == 'PUT':
        try:
            login_user = LoginUsers.objects.using('observation').get(id=id)
        except LoginUsers.DoesNotExist:
            return Response({'message': 'Login user does not exist.'}, status=404)
        serializer = LoginUsersSerializers(login_user, data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            login_user.__dict__.update(**validated_data)
            login_user.save()
            return Response({'message': 'Login user updated successfully.'}, status=200)
        return Response(serializer.errors, status=400)
    elif request.method == 'GET':
        newData = LoginUsers.objects.using('observation').values().get(id=id)
        return Response(newData, status=status.HTTP_200_OK) 
    elif request.method == 'UPDATE':
        name=request.data.get('name')
        email=request.data.get('email')
        telephone=request.data.get('tel')
        conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
        cur1 = conn1.cursor()
        cur1.execute("UPDATE api_loginusers SET name = ?, telephone = ?, email_address = ? WHERE id = ?", (name, telephone, email, id))
        conn1.commit()
        return Response({'status':'sussessfully Updated'},status=status.HTTP_200_OK)
    elif request.method == 'DELETE':
        newData = LoginUsers.objects.using('observation').values().get(id=id)
        data =  LoginUsers.objects.using('observation').get(id=id)
        data.delete()
        try:
            chat=ChatRooms.objects.using('observation').get(user_id=id)
            chat.delete()
        except:
            pass
        return Response({'status':'data deleted successfully','data':newData}, status=status.HTTP_200_OK) 

@api_view(['GET'])
def getClientNames(request):
    conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    cur1 = conn1.cursor()
    cur1.execute(f"SELECT * FROM tbl_client")
    rows=cur1.fetchall()
    data=[]
    for row in rows:
        data.append({
            "client_id": row[0],
            "client_name": row[1],
        })
    return Response(data,status=status.HTTP_200_OK)


@api_view(['GET'])
def getFilesDasta(request,fid):
    conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    cur1 = conn1.cursor()
    try:
        cur1.execute(f"SELECT forecast_id,type,file_location FROM tbl_forecast_inclusion_image_location where forecast_id={fid}")
        rows=cur1.fetchall()
        data=[]
        wind=""
        wave=""
        satpic=""
        current=""
        current_tables=""
        for row in rows:
            if row[1] == "Wave Analysis":
                wave=row[2]
            if row[1] == "Wind Analysis":
                wind=row[2]
            if row[1] == "Satellite":
                satpic=row[2]
            if row[1] == "Current Tables":
                current=row[2]
            if row[1] == "Currents":
                current_tables=row[2]
        data ={
            'wind':wind,
            'wave':wave,
            'satpic':satpic,
            'current_tables':current_tables,
            'current':current
            }
        return Response(data,status=status.HTTP_200_OK)
    except:
        return Response({'status':'Error'},status=status.HTTP_400_BAD_REQUEST)

def getLATLON(forecast_id):
    print(forecast_id)
    conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    cur1 = conn1.cursor()
    try:
        cur1.execute(f"SELECT model_data_load_id,forecast_id FROM tbl_model_data_load WHERE forecast_id={forecast_id} ORDER BY model_data_load_id DESC LIMIT 1;")
        rows=cur1.fetchall()
        data={}
        for row in rows:
            data = {
                "model_data_load_id": row[0],
                "forecast_id": row[1],
            }
        cur1.execute(f"SELECT model_data_load_detail_id, lat, long, a_10mwinddir, a_10mwindspeed, a_50mwinddir, a_50mwindspeed, a_100mwinddir, a_100mwindspeed FROM tbl_model_data_load_detail WHERE model_data_load_id={data['model_data_load_id']} ORDER BY model_data_load_detail_id DESC LIMIT 1;")
        rows=cur1.fetchall()
        data1={}
        for row in rows:
            data1 = {
                "model_data_load_id":data['model_data_load_id'],
                "forecast_id":forecast_id,
                "model_data_load_detail_id": row[0],
                "lat": row[1],
                "lon": row[2],
                "a_10mwinddir": row[3],
                "a_10mwindspeed": row[4],
                "a_50mwinddir": row[5],
                "a_50mwindspeed": row[6],
                "a_100mwinddir": row[7],
                "a_100mwindspeed": row[8]
            }
        return data1
    except:
        data1 = {
            "model_data_load_id":"",
            "forecast_id":forecast_id,
            "model_data_load_detail_id": "",
            "lat": "",
            "lon": "",
        }
        return data1

@api_view(['GET'])
def getLatLonRequest(request, forecast_id):
    data = getLATLON(forecast_id)
    return Response(data,status=status.HTTP_200_OK)

@api_view(['GET'])
def typhoonDatas(request, forecast_id):
    conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    cur1 = conn1.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur1.execute(f"SELECT model_data_load_id FROM tbl_model_data_load WHERE forecast_id={forecast_id} ORDER BY model_data_load_id DESC")
        model_data_load_id = cur1.fetchone().get('model_data_load_id')
        cur1.execute(f"SELECT model_data_load_detail_id, lat, long FROM tbl_model_data_load_detail WHERE model_data_load_id={model_data_load_id} ORDER BY model_data_load_detail_id DESC")
        data = cur1.fetchone()
        cur1.execute(f"SELECT * FROM tbl_forecast_cyclone WHERE forecast_id={forecast_id}")
        cyclone_data = cur1.fetchone()
        datas = {"model_data": data, "cyclone_data": cyclone_data}
        return Response(datas,status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({},status=status.HTTP_200_OK)

@api_view(['GET'])
def stormDatas(request):
    conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    cur1 = conn1.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur1.execute(f"SELECT * FROM tbl_storm_track")
        storm_track = cur1.fetchall()
        storm_track_datas = [x for x in storm_track if x.get('status_id') == 8]
        storm_path_ids = []
        for track in storm_track_datas:
            cur1.execute(f"SELECT MAX(storm_path_id) FROM tbl_storm_path WHERE storm_track_id = {track.get('storm_track_id')}")
            latest_storm_path_id = cur1.fetchone()['max']
            if latest_storm_path_id:
                storm_path_ids.append(latest_storm_path_id)
        storm_path_dict = {}
        for storm_path_id in storm_path_ids:
            cur1.execute(f"SELECT * FROM tbl_storm_path WHERE storm_path_id = {storm_path_id}")
            storm_path_data = cur1.fetchone()
            if storm_path_data:
                storm_path_dict[f"storm_{storm_path_data.get('storm_track_id')}"] = storm_path_data
        
        tbl_storm_path_array = []
        for x, y in storm_path_dict.items():
            cur1.execute(f"SELECT * FROM tbl_storm_path_data WHERE storm_path_id = {y.get('storm_path_id')}")
            datas = cur1.fetchall()
            if datas:
                lat = datas[0].get('lat')
                lon = datas[0].get('lon')
                if lat is not None and lon is not None:
                    storm_path_dict[x] = {"lat": lat, 'lon': lon}
                    tbl_storm_path_array.append(datas)
                else:
                    del storm_path_dict[x]
        return Response({"track_datas": storm_track_datas, "storm_datas": tbl_storm_path_array, "map_hovers": storm_path_dict}, status=status.HTTP_200_OK)
    except Exception as e:
        print(traceback.format_exc())
        return Response([], status=status.HTTP_200_OK)

    

@api_view(['GET'])
def getLastEdited(request, forecast_id):
    conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    cur1 = conn1.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        try:
            cur1.execute(f"SELECT * FROM tbl_data_load_detail WHERE forecastid={forecast_id} ORDER BY dutylisttaskid DESC")
            dutylist = cur1.fetchone()
            cur1.execute(f"SELECT * FROM tbl_data_load_detail WHERE forecastid={forecast_id} AND dutylisttaskid={dutylist.get('dutylisttaskid')} ORDER BY datetimeutc ASC")
            forecast_time = cur1.fetchone().get('datetimeutc', 0)
        except:
            forecast_time = 0
        try:
            cur1.execute(f"SELECT * FROM tbl_forecast_osf_criteria WHERE forecast_id={forecast_id}")
            quick_overview = cur1.fetchone().get('created_on', 0)
        except:
            quick_overview = 0
        try:
            cur1.execute(f"SELECT * FROM tbl_storm_track ORDER BY created_on DESC")
            typhoon = cur1.fetchone().get('created_on', 0)
        except:
            typhoon = 0
        return Response({'forecast': forecast_time, "quick_overview": quick_overview, "typhoon": typhoon}, status=status.HTTP_200_OK)
    except:
        return Response({},status=status.HTTP_200_OK)

@api_view(['GET'])
def getPlaceHolder(request, forecast_id):
    conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="forecast") 
    cur1 = conn1.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur1.execute(f"SELECT * FROM tbl_field")
        tbl_field = cur1.fetchall()
        tbl_fields = {x.get('name'): dict(x) for x in tbl_field}
        cur1.execute(f"SELECT * FROM tbl_forecast_inclusion_field WHERE forecast_id={forecast_id}")
        forecast_inclusion_field = cur1.fetchall()
        inclusion_fields = {str(x.get('field_id')): dict(x) for x in forecast_inclusion_field}
        cur1.execute(f"SELECT * FROM tbl_output_unit")
        output_unit = cur1.fetchall()
        output_units = {str(x.get('output_unit_id')): dict(x) for x in output_unit}
        for name, f_id in tbl_fields.items():
            unit_id = inclusion_fields.get(str(f_id.get('field_id')), {}).get('output_unit_id')
            tbl_fields[name]['output_unit_id'] = unit_id
            tbl_fields[name]['output_unit_name'] = output_units.get(str(unit_id), {}).get('output_unit_name')
        return Response(tbl_fields, status=status.HTTP_200_OK)
    except:
        return Response({},status=status.HTTP_200_OK)
    
@api_view(['POST'])
def updateUsers(request, id):
    if(request.data.get("id") != None and request.data.get("old_password") != None or request.data.get("password") != None):
        old = request.data.get("old_password")
        new = request.data.get("password")
        conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="observation")
        cur1 = conn1.cursor()
        newData = LoginUsers.objects.using('observation').values().get(id=id) 
        if(newData.get("password") == old):
            cur1.execute(f"UPDATE api_loginusers SET password = '{new}' WHERE id = {id}")
            conn1.commit()
            return Response({'status':'sussessfully Updated'},status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        
    if(request.data.get('name') != None or request.data.get('email') == None or request.data.get('tel') != None ):
        print(request.data)
        conn1 = psycopg2.connect(host="localhost", port="5433", user="postgres", password="123", database="observation") 
        cur1 = conn1.cursor()
        newData = LoginUsers.objects.using('observation').values().get(id=id) 
        name = newData.get('name')
        email = newData.get('email')
        telephone = newData.get('telephone')
        print(request.data)
        if request.data.get('name') != None:
            name = request.data.get('name')
        if request.data.get("email") != None:
            email=request.data.get('email')
        if request.data.get("tel") != None:
            telephone=request.data.get('tel')
        cur1.execute(f"UPDATE api_loginusers SET name = '{name}', telephone = '{telephone}', email_address = '{email}' WHERE id = {id}")
        conn1.commit()
        return Response({'status':'sussessfully Updated'},status=status.HTTP_200_OK)