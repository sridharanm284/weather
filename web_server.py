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

class ChatServer:
    def __init__(self):
        self.clients: list = []
        self.messages: dict = {}
    def set_chat_clients(self, user_id, chat_id):
        for index, client in enumerate(self.clients.copy()):
            try:
                if client.get('user_id') == user_id:
                    self.clients[index]['chat_id'] = chat_id
            except: continue
    def remove_clients(self, user_id):
        for index, client in enumerate(self.clients.copy()):
            try:
                if client.get('user_id') == user_id:
                    del self.clients[index]
            except: continue
    def return_active_clients(self, chat_id):
        clients = []
        for client in self.clients.copy():
            try:
                if client.get('chat_id') == chat_id:
                    clients.append(client)
            except: continue
        return clients

    async def createChat(self, websocket, request):
        user_id = request.get("user_id")
        print(request)
        connection = psycopg2.connect(**DBConnection.WEBAPPDB)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM api_loginusers WHERE id=%s", (user_id, ))
        userdata = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
        try:
            cursor.execute("SELECT * FROM api_chatrooms WHERE user_id=%s", (user_id, ))
            room = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
            self.set_chat_clients(user_id, room.get('chat_id'))
            cursor.execute("SELECT * FROM api_chat WHERE chat_id=%s", (room.get('chat_id'),))
            chats = [json.loads(json.dumps(x, cls=DateTimeEncoder)) for x in cursor.fetchall()]
            #serializer = FileSerializer(chats, many=True)  
            #for chat in serializer.data:
            #    if chat.get('file'):
            #        data['chats'].append(chat)
            data = {
                'rooms': room,
                'chats': chats,
                'userdata': userdata,
                'mode': 'createchat'
            }
            print(user_id, chats)
            return await websocket.send(json.dumps(data))
        except:
            print(traceback.format_exc())
            print('----')
            connection = psycopg2.connect(**DBConnection.WEBAPPDB)
            cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute('INSERT INTO api_chatrooms (user_id, chat_id, user_name, operation, unread_admin, unread_user, read_admin, read_user) VALUES (%s, %s, %s, %s, %s, %s, false, false)', (user_id, secrets.token_hex(16), userdata.get("name"), userdata.get("operation"), 0, 0))
            connection.commit()
            cursor.execute("SELECT * FROM api_chatrooms WHERE user_id=%s", (user_id, ))
            rooms = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
            return await websocket.send(json.dumps({'status':'Room Created', 'rooms':rooms, 'mode': 'createchat'}))

    async def sendMessage(self, request):
        user_id = request.get("user_id")
        chat_id=request.get('chat_id')
        self.set_chat_clients(user_id, chat_id)
        message=request.get('message')
        user_type=request.get("user_type")
        datenow = datetime.datetime.now()
        #files=request.FILES.getlist('file')
        #print(chat_id,user,message,files)
        #if files:
        #    for file in files:
        #        msg=Chat(chat_id=chat_id, message=message, user=user, file=file)
        #        msg.save(using="observation")
        #else:
        connection = psycopg2.connect(**DBConnection.WEBAPPDB)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('INSERT INTO api_chat (chat_id, message, user_type, date_time, file) VALUES (%s, %s, %s, %s, %s)', (chat_id, message, user_type, datenow.strftime("%Y-%m-%d %H:%M:%S"), ""))
        connection.commit()
        cursor.execute("SELECT * FROM api_chatrooms WHERE chat_id=%s", (chat_id, ))
        room = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
        if user_type=="user":
            cursor.execute('UPDATE api_chatrooms SET read_user = false, read_admin = true, unread_admin=%s WHERE chat_id=%s', (room.get("unread_admin")+1, chat_id))
        else:
            cursor.execute('UPDATE api_chatrooms SET read_user = true, read_admin = false, unread_user=%s WHERE chat_id=%s', (room.get("unread_user")+1, chat_id))
        msg_data = {
            "message": message,
            "date_time": datenow,
            "user_type": user_type,
            "chat_id": chat_id,
            "imgfile": None,
            "file_name": None
        },
        connection.commit()
        print(self.clients)
        if user_type == "admin":
            cursor.execute("SELECT * FROM api_chatrooms")
            rooms = [json.loads(json.dumps(x, cls=DateTimeEncoder)) for x in cursor.fetchall()]
        await asyncio.gather(*[(x.get('websocket').send(json.dumps({'mode':'receivemsg', "chats": msg_data, 'rooms': rooms}, cls=DateTimeEncoder))) for x in self.return_active_clients(chat_id)])
        
    async def readMessages(self, request):
        connection = psycopg2.connect(**DBConnection.WEBAPPDB)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        print(request)
        chat_id=request.get('chat_id')
        user_id = request.get("user_id")
        self.set_chat_clients(user_id, chat_id)
        user_type=request.get("user_type")
        if user_type=="user":
            cursor.execute('UPDATE api_chatrooms SET read_user = false, read_admin = true, unread_user = 0 WHERE chat_id=%s', (chat_id, ))
        else:
            cursor.execute('UPDATE api_chatrooms SET read_user = true, read_admin = false, unread_admin = 0 WHERE chat_id=%s', (chat_id, ))
        connection.commit()
        await asyncio.gather(*[(x.get('websocket').send(json.dumps({'mode':'readmessages', 'done': True}))) for x in self.return_active_clients(chat_id)])

    async def ChatsList(self, websocket, request):
        connection = psycopg2.connect(**DBConnection.WEBAPPDB)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        token=request.get("token")
        cursor.execute("SELECT * FROM api_tokens WHERE token=%s", (token, ))
        get_user_id = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
        cursor.execute("SELECT * FROM api_loginusers WHERE id=%s", (get_user_id.get('user_id'), ))
        get_user = json.loads(json.dumps(cursor.fetchone(), cls=DateTimeEncoder))
        if get_user.get('user_type') == "admin":
            cursor.execute("SELECT * FROM api_chatrooms")
            rooms = [json.loads(json.dumps(x, cls=DateTimeEncoder)) for x in cursor.fetchall()]
            print("rooms,", rooms)
            return await websocket.send(json.dumps({'mode':'listchats', 'rooms': rooms}))
        else:
            return await websocket.send(json.dumps({'status':'only admin can access this page'}))

    def parseInt(self, i: str):
        try:
            if i == None:
                return i
            if not i.isalnum():
                return int(i)
            return i
        except:
            return i

    async def ClientHandler(self, websocket, path: str):
        if not path.split('/')[path.split('/').index('chat') + 1].isalnum():
            return
        user_id = int(path.split('/')[-2])
        self.clients.append({"user_id": user_id, "websocket": websocket})
        try:
            async for message in websocket:
                message = json.loads(message)
                if message.get('user_id') == None:
                    message['user_id'] = user_id
                for value in message:
                    message[value] = self.parseInt(message[value])
                if message['mode'] == 'sendmessage':
                    print("send", user_id, message)
                    await self.sendMessage(message)
                elif message['mode'] == 'readmessages':
                    print("read", user_id, message)
                    await self.readMessages(message)
                elif message['mode'] == 'createchat':
                    print("create", user_id, message)
                    await self.createChat(websocket, message)
                elif message['mode'] == 'listchats':
                    print("list", user_id, message)
                    await self.ChatsList(websocket, message)
        except:
            print(traceback.format_exc())
            self.remove_clients(user_id)
    async def Server(self):
        async with serve(self.ClientHandler, "localhost", 8001):
            await asyncio.Future()

asyncio.run(ChatServer().Server())