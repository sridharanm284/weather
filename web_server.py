import asyncio, json, secrets, traceback, datetime
from websockets.server import serve
import psycopg2, psycopg2.extras
from json import JSONEncoder

class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if type(obj) == datetime:
            return obj.isoformat()
        return str(obj)

class DBConnection:
    WEBAPPDB = {
        "database": "observation",
        "host": "localhost",
        "user": "postgres",
        "password": "123",
        "port": "5433"
    }

def createChat(request):
    user_id = request.get("user_id")
    print(request)
    connection = psycopg2.connect(**DBConnection.WEBAPPDB)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(f"SELECT * FROM api_loginusers WHERE id={user_id}")
    userdata = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
    print(userdata)
    try:
        cursor.execute(f"SELECT * FROM api_chatrooms WHERE user_id={user_id}")
        room = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
        print(room)
        cursor.execute(f"SELECT * FROM api_chat WHERE chat_id='{room.get('chat_id')}'")
        chats = [json.loads(json.dumps(x, cls=DateTimeEncoder)) for x in cursor.fetchall()]
        #serializer = FileSerializer(chats, many=True)  
        
        #for chat in serializer.data:
        #    if chat.get('file'):
        #        data['chats'].append(chat)
        data = {
            'rooms': room,
            'chats':chats,
            'userdata': userdata,
            'mode': 'createchat'
        }
        return data
    except:
        connection = psycopg2.connect(**DBConnection.WEBAPPDB)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f'INSERT INTO api_chatrooms (user_id, chat_id, user_name, operation) VALUES ({user_id}, "{secrets.token_hex(16)}", "{userdata.get("name")}", "{userdata.get("operation")}")')
        cursor.commit()
        connection.commit()
        cursor.execute(f"SELECT * FROM api_chatrooms WHERE user_id={user_id}")
        rooms = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
        return {'status':'Room Created','message':rooms, 'mode': 'createchat'}

def sendMessage(request):
    chat_id=request.get('id')
    message=request.get('message')
    user=request.get("user")
    #files=request.FILES.getlist('file')
    #print(chat_id,user,message,files)
    #if files:
    #    for file in files:
    #        msg=Chat(chat_id=chat_id, message=message, user=user, file=file)
    #        msg.save(using="observation")
    #else:
    connection = psycopg2.connect(**DBConnection.WEBAPPDB)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(f'INSERT INTO api_chat (id, message, user_name) VALUES ({chat_id}, {message}, {user})')
    cursor.commit()
    connection.commit()
    cursor.execute("SELECT * FROM api_chatrooms WHERE id = %i", (chat_id,))
    room = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
    if user=="user":
        cursor.execute(f'UPDATE api_chatrooms SET read_user = false, read_admin = true, unread_admin={room.get("unread_admin")+1} WHERE chat_id="{chat_id}"')
    else:
        cursor.execute(f'UPDATE api_chatrooms SET read_user = true, read_admin = false, unread_user={room.get("unread_user")+1} WHERE chat_id="{chat_id}"')
    return {'status':'Message Sent'}
    
def readMessages(request):
    connection = psycopg2.connect(**DBConnection.WEBAPPDB)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    print(request)
    chat_id=request.get('chat_id')
    user=request.get("user")
    if user=="user":
        cursor.execute(f'UPDATE api_chatrooms SET read_user = false, read_admin = true, unread_user = 0 WHERE chat_id={chat_id}')
    else:
        cursor.execute(f'UPDATE api_chatrooms SET read_user = true, read_admin = false, unread_admin = 0 WHERE chat_id={chat_id}')
    return {'status':'Message Read'}

def ChatsList(request):
    connection = psycopg2.connect(**DBConnection.WEBAPPDB)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    user=request.get("user")
    cursor.execute(f"SELECT * FROM api_tokens WHERE user='{user}'")
    get_user_id = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
    cursor.execute(f"SELECT * FROM api_loginusers WHERE id={get_user_id.get('user_id')}")
    get_user = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
    if get_user.get('user_type') == "admin":
        cursor.execute("SELECT * FROM api_chatrooms")
        rooms = [json.loads(json.dumps(x), cls=DateTimeEncoder) for x in cursor.fetchall()]
        return rooms
    else:
        return {'status':'only admin can access this page'}

def parseInt(i: str):
    if i == None:
        return i
    if not i.isalnum():
        return int(i)
    return i

class ChatServer:
    def __init__(self):
        self.clients: dict = {}
        self.messages: dict = {}
    async def ClientHandler(self, websocket, path: str):
        print(websocket, path, path.split('/')[path.split('/').index('chat') + 1])
        if not path.split('/')[path.split('/').index('chat') + 1].isalnum():
            return
        chat_id = int(path.split('/')[-2])
        self.clients[chat_id] = websocket
        try:
            async for message in websocket:
                print(message)
                message = json.loads(message)
                for value in message:
                    message[value] = parseInt(message[value])
                print(message)
                if message['mode'] == 'sendmessage':
                    print("send", chat_id, message)
                    await websocket.send(json.dumps(sendMessage(message)))
                elif message['mode'] == 'readmessages':
                    print("read", chat_id, message)
                    await websocket.send(json.dumps(readMessages(message)))
                elif message['mode'] == 'createchat':
                    print("create", chat_id, message)
                    await websocket.send(json.dumps(createChat(message)))
                elif message['mode'] == 'listchats':
                    print("list", chat_id, message)
                    await websocket.send(json.dumps(ChatsList(message)))
        except:
            print(traceback.format_exc())
            self.clients.pop(chat_id)
    async def Server(self):
        async with serve(self.ClientHandler, "localhost", 8001):
            await asyncio.Future()

asyncio.run(ChatServer().Server())