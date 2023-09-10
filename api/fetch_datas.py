import psycopg2, psycopg2.extras, datetime, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class DBConnection:
    FETCHDB = {
        "database": "forecast",
        "host": "localhost",
        "user": "postgres",
        "password": "123",
        "port": "5433"
    }    
    WEBAPPDB = {
        "database": "observation",
        "host": "localhost",
        "user": "postgres",
        "password": "123",
        "port": "5433"
    }

class Forecast:
    def __init__(self, forecast_id: int):
        self.datas: list = []
        self.forecast_datas: list = []
        self.forecast_id = forecast_id
        self.connection = psycopg2.connect(**DBConnection.FETCHDB)
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.dutylisttaskid = set()
        self.total_headers = [{'name': 'forecastid', 'caption': 'ForecastID'}, {'name': 'dutylisttaskid', 'caption': 'DutyListTasKid'}, {'name': 'datetimeutc', 'caption': 'Time'}]
        self.cursor.execute(f'SELECT name, caption, field_id FROM tbl_field')
        headers = self.cursor.fetchall()
        self.cursor.execute(f'SELECT field_id FROM tbl_forecast_inclusion_field WHERE forecast_id={self.forecast_id}')
        self.total_headers_order = tuple([list(x.values())[0] for x in self.cursor.fetchall()])
        self.cursor.execute(f'SELECT * FROM tbl_data_load_detail WHERE forecastid={self.forecast_id}')
        self.data_header = tuple([x for x in self.cursor.fetchone()])        
        total_header_cont = [{x:y for x, y in z.items()} for z in headers if (([x for x in z.values()][0] in self.data_header) and ([x for x in z.values()][2] in self.total_headers_order))]
        total_header_cont = [tuple for x in self.total_headers_order for tuple in total_header_cont if tuple.get('field_id') == x]
        self.total_headers.extend(total_header_cont)
        newheaders = []
        for l in self.total_headers:
            if 'field_id' in l:
                field_id=l['field_id']
                m = self.cursor.execute(f'SELECT output_unit_id FROM tbl_forecast_inclusion_field WHERE field_id={field_id}')
                rows = self.cursor.fetchall()
                # o = rows[0][0]
                # print(o)
                x = rows[0]['output_unit_id']
                try:
                    ll = self.cursor.execute(f'SELECT output_unit_name FROM tbl_output_unit WHERE output_unit_id={x}')
                    rows = self.cursor.fetchall()
                    x = rows[0]['output_unit_name']
                    print(str(x))
                    l['output_unit_name']=str(x)
                    print(l)
                except:
                    l['output_unit_name']=""
                newheaders.append(l)
        self.cursor.execute(f'SELECT interval FROM tbl_forecast_time_table_step WHERE forecast_id={self.forecast_id}')
        try: self.interval = list(self.cursor.fetchone().values())[0]
        except: self.interval = 3
        self.ReadDatas()
    def ReadDatas(self):
        self.cursor.execute(f'SELECT {", ".join([x.get("name") for x in self.total_headers])} FROM tbl_data_load_detail WHERE forecastid={self.forecast_id}')
        datas = self.cursor.fetchall()
        self.connection.close()
        self.datas = [{x:y for x, y in z.items()} for z in datas]
        self.datas = sorted(self.datas, key=lambda data: data.get('datetimeutc'))
        for data in self.datas: self.dutylisttaskid.add(data['dutylisttaskid'])
        self.dutylisttaskid = max(self.dutylisttaskid)
        return self.datas
    def ScrapeDatas(self):
        last_date: str = None
        day_data: list = []
        for data in self.datas:
            if self.dutylisttaskid != data.get('dutylisttaskid'): continue
            data.pop('forecastid')
            data.pop('dutylisttaskid')
            if last_date == None:
                last_date = data.get('datetimeutc')
            if (last_date.day == data.get('datetimeutc').day) and (last_date.month == data.get('datetimeutc').month) and (last_date.year == data.get('datetimeutc').year):
                if data.get('datetimeutc').hour == 0:
                    data['datetimeutc'] = f"{data.get('datetimeutc').strftime('%m/%d/%Y')} 00:00"
                else:
                    data['datetimeutc'] = data.get('datetimeutc').strftime('%m/%d/%Y %H:%M')
                day_data.append(data)
            else:
                day_data = sorted(day_data, key=lambda data: data.get('datetimeutc'))
                self.forecast_datas.append(day_data)
                dataa = dict(data)
                if dataa.get('datetimeutc').hour == 0:
                    dataa['datetimeutc'] = f"{data.get('datetimeutc').strftime('%m/%d/%Y')} 00:00"
                else:
                    dataa['datetimeutc'] = data.get('datetimeutc').strftime('%m/%d/%Y %H:%M')
                day_data = [dataa]
                last_date = data.get('datetimeutc')
        day_data = sorted(day_data, key=lambda data: data.get('datetimeutc'))
        self.forecast_datas.append(day_data)
        #self.forecast_datas.reverse()
        self.connection.close()
        return self.forecast_datas

class Overview:
    def __init__(self, forecast_id: int, data_size: int = 5):
        self.data_size = data_size
        self.datas: list = []
        self.forecast_datas: list = []
        self.dutylisttaskid = set()
        self.forecast_id = forecast_id
        self.connection = psycopg2.connect(**DBConnection.FETCHDB)
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.cursor.execute(f'SELECT forecast_osf_criteria_id, forecast_id, criteria_name FROM tbl_forecast_osf_criteria WHERE forecast_id={forecast_id}')
        self.criteria_datas = [{x:y for x, y in z.items()} for z in self.cursor.fetchall()]
        forecast_osf_criteria_ids = [str(x.get("forecast_osf_criteria_id")) for x in self.criteria_datas]
        if forecast_osf_criteria_ids:
            query = f"SELECT forecast_osf_criteria_id, field_id, value, margin_value FROM tbl_forecast_osf_criteria_detail WHERE forecast_osf_criteria_id IN ({', '.join(forecast_osf_criteria_ids)})"
            self.cursor.execute(query)
            print(query)
        else:
            pass
        self.criteria_detail_datas = [{x:y for x, y in z.items()} for z in self.cursor.fetchall() if (z.get('field_id') != None)]
        self.ReadDatas()
    def ReadDatas(self):
        fields = [1]
        fields.extend([x.get('field_id') for x in self.criteria_detail_datas])
        self.cursor.execute(f'SELECT field_id, name, caption from tbl_field WHERE field_id IN ({", ".join([str(x) for x in tuple(set(fields))])});')
        tbl_field = [{x:y for x, y in z.items()} for z in self.cursor.fetchall()]
        tbl_field_names = ['forecastid', 'datetimeutc', 'dutylisttaskid']
        tbl_field_names.extend([x.get('name') for x in tbl_field])
        self.cursor.execute(f'SELECT {", ".join(tbl_field_names)} FROM tbl_data_load_detail WHERE forecastid={self.forecast_id}')
        datas = self.cursor.fetchall()
        self.connection.close()
        self.datas = [{x:y for x, y in z.items()} for z in datas]
        self.datas = sorted(self.datas, key=lambda data: data.get('datetimeutc'))
        for data in self.datas: self.dutylisttaskid.add(data['dutylisttaskid'])
        self.dutylisttaskid = max(self.dutylisttaskid)
        return self.datas
    def ScrapeDatas(self):  
        last_date: str = None
        day_data: list = []
        for data in self.datas:
            if self.dutylisttaskid != data.get('dutylisttaskid'): continue
            data.pop('forecastid')
            data.pop('dutylisttaskid')
            if last_date == None:
                last_date = data.get('datetimeutc')
            if (last_date.day == data.get('datetimeutc').day) and (last_date.month == data.get('datetimeutc').month) and (last_date.year == data.get('datetimeutc').year):
                if data.get('datetimeutc').hour == 0:
                    data['datetimeutc'] = f"{data.get('datetimeutc').strftime('%m/%d/%Y')} 24:00"
                else:
                    data['datetimeutc'] = data.get('datetimeutc').strftime('%m/%d/%Y %H:%M')
                day_data.append(data)
            else:
                day_data = sorted(day_data, key=lambda data: data.get('datetimeutc'))
                self.forecast_datas.append(day_data)
                dataa = dict(data)
                if dataa.get('datetimeutc').hour == 0:
                    dataa['datetimeutc'] = f"{data.get('datetimeutc').strftime('%m/%d/%Y')} 24:00"
                else:
                    dataa['datetimeutc'] = data.get('datetimeutc').strftime('%m/%d/%Y %H:%M')
                day_data = [dataa]
                last_date = data.get('datetimeutc')
        day_data = sorted(day_data, key=lambda data: data.get('datetimeutc'))
        self.forecast_datas.append(day_data)
        self.forecast_datas.reverse()
        self.connection.close()
        return self.forecast_datas[-self.data_size:]

class Weather(Overview):
    def __init__(self, forecast_id: int):
        super().__init__(forecast_id, 15)

class Observation:
    def __init__(self, date_time,wind_direction, wind_speed, combined, swell_ht, swell_period, swell_direction, vis, present, **kwargs):
        self.connection = psycopg2.connect(**DBConnection.WEBAPPDB)
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.cursor.execute('INSERT INTO tbl_data_observation (datetimeutc, wind_direction, wind_speed, combined, swell_ht, sell_period, swell_direction, vis, present) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)', (datetime.datetime.strptime(date_time, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S') if date_time != '' else None, self.parsefloat(wind_direction), self.parsefloat(wind_speed), self.parsefloat(combined), self.parsefloat(swell_ht), self.parsefloat(swell_period), self.parsefloat(swell_direction), self.parsefloat(vis), self.parsefloat(present)))
        self.connection.commit()
        self.connection.close()
        self.mail_data = "Datetime: {0}\nWind Direction: {1}\nWindSpeed: {2}\nCombined: {3}\nSwell Height: {4}\nSwell Direction: {5}\nVIS: {6}\nPresent: {7}".format(datetime.datetime.strptime(date_time, '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S') if date_time != '' else None, self.parsefloat(wind_direction), self.parsefloat(wind_speed), self.parsefloat(combined), self.parsefloat(swell_ht), self.parsefloat(swell_period), self.parsefloat(swell_direction), self.parsefloat(vis), self.parsefloat(present))
        self.SendMail()
    def parsefloat(self, data):
        if data == '':
            return None
        try: return float(data)
        except: return None
    def SendMail(self):
        try:
            sender_email = "sridharandeveloper06@outlook.com"
            password = "Project@24"
            message = MIMEMultipart()
            message["Subject"] = "Observation Form Submission"
            message["From"] = sender_email
            message["To"] = sender_email  
            message.attach(MIMEText(self.mail_data, "plain"))
            with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, sender_email, message.as_string())
            print("Email sent successfully!")
        except Exception as e:
            print("Cannot send email to the server:", str(e))
        