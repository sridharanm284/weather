import json
import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
import psycopg2, psycopg2.extras
from json import JSONEncoder
from datetime import datetime
from api.models import Chat

from forecast_server.settings import BASE_DIR
import base64
# Date Time
class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if type(obj) == datetime:
            return obj.isoformat()
        return str(obj)
    

# Database Connection
class DBConnection:
    WEBAPPDB = {
        "database": "observation",
        "host":"localhost",
        "user":"postgres",
        "password":"123",
        "port":"5433"
    }

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_room"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        # User ID
        user_id = self.scope["url_route"]["kwargs"]["room_name"]

        # DBConnection
        connection = psycopg2.connect(**DBConnection.WEBAPPDB)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        user = self.room_name

        cursor.execute(f"SELECT * FROM api_loginusers WHERE id={user}")
        get_user = json.loads(json.dumps(cursor.fetchone()))

        if get_user.get('user_type') == "admin":
            cursor.execute("SELECT * FROM api_chatrooms")
            rooms = [json.loads(json.dumps(x)) for x in cursor.fetchall()]
            data = {
                "rooms":rooms,
                "mode":"listchats"
            }
        else:
            cursor.execute(f"SELECT * FROM api_chatrooms WHERE user_id={user}")
            room = json.loads(json.dumps(cursor.fetchone()))
            chat_id = room.get('chat_id')
            cursor.execute(f"SELECT * FROM api_chat WHERE chat_id='{room.get('chat_id')}'")
            rooms = [json.loads(json.dumps(x, cls=DateTimeEncoder)) for x in cursor.fetchall()]
            print("CONDITION:", get_user.get('user_type'))
            if get_user.get('user_type') == "user":
                cursor.execute(f'UPDATE api_chatrooms SET read_user = false, read_admin = true , unread_user=0 WHERE chat_id=\'{chat_id}\'')
                connection.commit()
            

            data = {
                    'rooms': room.get('chat_id'),
                    'chats': rooms,
                    'mode': 'receivemsg',
                }

        await self.send(json.dumps(data))


    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data): 
        text_data_json = json.loads(text_data)
        data = {}  # Initialize data as an empty dictionary

        if text_data_json["mode"] == "createchat":
            user_id = text_data_json["user_id"]
            user_type = text_data_json["user_type"]
            connection = psycopg2.connect(**DBConnection.WEBAPPDB)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(f"SELECT * FROM api_loginusers WHERE id={user_id}")
            userdata = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
            if user_type == "admin" and text_data_json["select"] == "true":
                cursor.execute(f"UPDATE api_chatrooms SET unread_admin=0 WHERE user_id={user_id}")
                connection.commit()
            try:
                cursor.execute(f"SELECT * FROM api_chatrooms WHERE user_id={user_id}")
                room = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
                cursor.execute(f"SELECT * FROM api_chat WHERE chat_id='{room.get('chat_id')}'")
                chats = [json.loads(json.dumps(x, cls=DateTimeEncoder)) for x in cursor.fetchall()]
 
                data = {
                    'rooms': room,
                    'chats': chats,
                    'userdata': userdata,
                    'mode': 'createchat',
                    'user_type': user_type
                }
                
                # Send message to room group
            except:
                connection = psycopg2.connect(**DBConnection.WEBAPPDB)
                cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(f'INSERT INTO api_chatrooms (user_id, chat_id, user_name, operation) VALUES ({user_id}, "{text_data_json["token"]}", "{userdata.get("name")}", "{userdata.get("operation")}")')
                cursor.commit()
                cursor.execute(f"SELECT * FROM api_chatrooms WHERE user_id={user_id}")
                rooms = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
                data = {'status': 'Room Created', 'message': rooms, 'mode': 'createchat', "user_type":user_type}

        elif text_data_json["mode"] == "sidebar":
            user_type = text_data_json["user_type"]
            user_id = text_data_json["user_id"]
            connection = psycopg2.connect(**DBConnection.WEBAPPDB)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            Count = 0
            if user_type == 'admin':
                cursor.execute(f"SELECT unread_admin FROM api_chatrooms")
                count = [ json.loads(json.dumps(x)) for x in cursor.fetchall()]
                for i in count:
                    Count += i["unread_admin"]
            elif user_type == "user":
                cursor.execute(f"SELECT unread_user FROM api_chatrooms WHERE user_id={user_id}")
                count = [ json.loads(json.dumps(x)) for x in cursor.fetchall()]
                for i in count:
                    Count += i["unread_user"]

            for j in text_data_json:
                if ( j == "select"):
                    chat_id = text_data_json["chat_id"]
                    cursor.execute(f"UPDATE api_chatrooms SET read_user = false, read_admin = true, unread_user=0 WHERE chat_id=\'{chat_id}\'")
                    connection.commit()
                    data = {'status':'Message Sent', 'mode':'sendmsg', "user_type":user_type, "send_by":send_by, "user_id": user_id, "chat_id":chat_id}
            else:
                data = {
                'mode':'sidebar',
                'count':Count,
                'user_type':user_type,
                'user_id':user_id,
                }

        elif text_data_json["mode"] == "sendmessage":
            chat_id = text_data_json["chat_id"]
            message = text_data_json["message"]
            user = text_data_json["user_type"]
            user_id = text_data_json["user_id"]
            send_by = text_data_json["send_by"]
            user_type = text_data_json["user_type"]
            # send_to = text_data_json["send_to"]
            connection = psycopg2.connect(**DBConnection.WEBAPPDB)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                

            # Insert a new record into api_chat
            cursor.execute('INSERT INTO api_chat (chat_id, date_time, message, user_type, file) VALUES (%s, %s, %s, %s, %s)', (chat_id, datetime.now(), message, user, ''))

            # Commit the transaction
            connection.commit()

            # Select a record from api_chatrooms based on chat_id
            cursor.execute(f'SELECT * FROM api_chatrooms WHERE user_id ={user_id}')
            room = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
            if user=="user":
                cursor.execute(f'UPDATE api_chatrooms SET read_user = false, read_admin = true, unread_admin={room.get("unread_admin")+1}, unread_user=0 WHERE chat_id=\'{chat_id}\'')
            else:
                cursor.execute(f'UPDATE api_chatrooms SET read_user = true, read_admin = false, unread_user={room.get("unread_user")+1}, unread_admin=0 WHERE chat_id=\'{chat_id}\'')
            connection.commit()
            cursor.execute(f"SELECT * FROM api_loginusers WHERE id={user_id}")
            userdata = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
            cursor.execute(f"SELECT * FROM api_chatrooms WHERE user_id={user_id}")
            room = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
            cursor.execute(f"SELECT * FROM api_chat WHERE chat_id='{chat_id}'")
            chats = [ json.loads(json.dumps(x, cls=DateTimeEncoder)) for x in cursor.fetchall()]
            data = {
                    'rooms': room,
                    'chats': chats,
                    'userdata': userdata,
                    'mode': 'latest',
                    'user_type': user_type,
                    'send_by':send_by,
                    'user_id':user_id
            }
            # data = {'mode':'createchat', 'rooms':chat_id,'chats':chats,'user_type':user, 'send_by':send_by}            
            # data = {'status':'Message Sent', 'mode':'sendmsg', "user_type":user, "send_by":send_by, "user_id": user_id, "chat_id":chat_id}

        elif text_data_json["mode"] == "saveImg":
            print("Trigger")
            chat_id = text_data_json["chat_id"]
            files = text_data_json["file"]
            user = text_data_json["user_type"]
            user_id = text_data_json["user_id"]
            send_by = text_data_json["send_by"]
            print(files)
            data = {'status':'Message Sent', 'mode':'sendmsg', "user_type":user, "send_by":send_by, "user_id": user_id, "chat_id":chat_id}

        elif text_data_json["mode"] == "listchats":
                self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
                self.room_group_name = f"chat_room"


                    # User ID
                user_id = self.scope["url_route"]["kwargs"]["room_name"]

                    # DBConnection
                connection = psycopg2.connect(**DBConnection.WEBAPPDB)
                cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                user = self.room_name

                cursor.execute(f"SELECT * FROM api_loginusers WHERE id={user}")
                get_user = json.loads(json.dumps(cursor.fetchone()))

                if get_user.get('user_type') == "admin":
                    cursor.execute("SELECT * FROM api_chatrooms")
                    rooms = [json.loads(json.dumps(x)) for x in cursor.fetchall()]
                    data = {
                            "rooms":rooms,
                            "mode":"listchats"
                        }
                else:
                    cursor.execute(f"SELECT * FROM api_chatrooms WHERE user_id={user}")
                    room = json.loads(json.dumps(cursor.fetchone()))
                    cursor.execute(f"SELECT * FROM api_chat WHERE chat_id='{room.get('chat_id')}'")
                    rooms = [json.loads(json.dumps(x, cls=DateTimeEncoder)) for x in cursor.fetchall()]
                    data = {
                            "rooms":room.get('chat_id'),
                            "chats":rooms,
                            "mode":"receivemsg"
                        }


        elif text_data_json["mode"] == "latest":
            user_id = text_data_json["user_id"]
            user_type = text_data_json["user_type"]
            connection = psycopg2.connect(**DBConnection.WEBAPPDB)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(f"SELECT * FROM api_loginusers WHERE id={user_id}")
            userdata = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
            if user_type == "admin" and text_data_json["select"] == "true":
                cursor.execute(f"UPDATE api_chatrooms SET unread_admin=0 WHERE user_id={user_id}")
                connection.commit()
            try:
                cursor.execute(f"SELECT * FROM api_chatrooms WHERE user_id={user_id}")
                room = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
                cursor.execute(f"SELECT * FROM api_chat WHERE chat_id='{room.get('chat_id')}'")
                chats = [ json.loads(json.dumps(x, cls=DateTimeEncoder)) for x in cursor.fetchall()]
                
                data = {
                    'rooms': room,
                    'chats': chats,
                    'userdata': userdata,
                    'mode': 'latest',
                    'user_type': user_type
                }   
            except:
                connection = psycopg2.connect(**DBConnection.WEBAPPDB)
                cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(f'INSERT INTO api_chatrooms (user_id, chat_id, user_name, operation) VALUES ({user_id}, "{text_data_json["token"]}", "{userdata.get("name")}", "{userdata.get("operation")}")')
                cursor.commit()
                cursor.execute(f"SELECT * FROM api_chatrooms WHERE user_id={user_id}")
                rooms = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
                data = {'status': 'Room Created', 'message': rooms, 'mode': 'latest', "user_type":user_type}


        elif text_data_json["mode"] == "userchat":
            user_type = text_data_json["user_type"]
            user_id = text_data_json["user_id"]
            connection = psycopg2.connect(**DBConnection.WEBAPPDB)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            Count = 0
            if user_type == "user":
                cursor.execute(f"SELECT unread_user FROM api_chatrooms WHERE user_id={user_id}")
                count = [ json.loads(json.dumps(x)) for x in cursor.fetchall()]
                chat_id = text_data_json["chat_id"]
                cursor.execute(f"UPDATE api_chatrooms SET read_user = false, read_admin = true, unread_user=0 WHERE chat_id=\'{chat_id}\'")
                connection.commit()
                for i in count:
                    Count += i["unread_user"]
            
            data = {
                'mode':'sidebar',
                'count':Count,
                'user_type':user_type,
                'user_id':user_id,
                }

        # Send message to room group
        await self.channel_layer.group_send(
                        self.room_group_name, {"type": "chat.message", "message":data }
                    )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event["message"]))