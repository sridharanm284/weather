from django.db import models
from django.db.models.base import ModelBase

class ForecastID(models.Model):
    forecast_id = models.IntegerField()

class ObservationForm(models.Model):
    date_time = models.DateTimeField()
    wind_speed = models.IntegerField()
    combined = models.IntegerField()
    swell_ht = models.IntegerField()
    swell_period = models.IntegerField()
    swell_direction = models.IntegerField()
    vis = models.IntegerField()
    present = models.IntegerField()

class LoginUsers(models.Model):
    name=models.CharField(max_length=100)
    password=models.CharField(max_length=100)
    user_type=models.CharField(max_length=100, default="user")
    client=models.CharField(max_length=100,blank=True)
    operation=models.CharField(max_length=100,blank=True)
    email_address=models.CharField(max_length=100,blank=True)
    telephone=models.CharField(max_length=100,blank=True)
    contract_no=models.CharField(max_length=100,blank=True)
    region=models.CharField(max_length=100,blank=True)
    vessel=models.CharField(max_length=100,blank=True)
    lat=models.CharField(max_length=100,blank=True)
    lon=models.CharField(max_length=100,blank=True)
    site_route=models.CharField(max_length=100,blank=True)
    start_date=models.CharField(max_length=100,blank=True)
    end_date=models.CharField(max_length=100,blank=True)
    expected_date=models.CharField(max_length=100,blank=True)
    metsys_name=models.CharField(max_length=100,blank=True)
    service_types=models.CharField(max_length=100,blank=True)
    day_shift=models.CharField(max_length=100,blank=True)
    night_shift=models.CharField(max_length=100,blank=True)
    last_bill_update=models.CharField(max_length=100,blank=True)
    wind=models.CharField(max_length=500,blank=True)
    wave=models.CharField(max_length=500,blank=True)
    current=models.CharField(max_length=500,blank=True)
    satpic=models.CharField(max_length=500,blank=True)
    client_id=models.CharField(max_length=100, blank=True)
    forecast_id=models.CharField(max_length=100,blank=True)


class Tokens(models.Model):
    user_id=models.IntegerField()
    user_name=models.CharField(max_length=100)
    token=models.CharField(max_length=200)

class Chat(models.Model):
    message=models.TextField()
    date_time=models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='uploads/',blank=True)
    chat_id=models.CharField(max_length=100)
    user_name=models.CharField(max_length=100,default="user")
    
class ChatRooms(models.Model):
    user_id=models.IntegerField()
    chat_id=models.CharField(max_length=100)
    operation=models.CharField(max_length=100,blank=True)
    user_name=models.CharField(max_length=100,blank=True)
    read_user=models.CharField(max_length=100,default="false")
    read_admin=models.CharField(max_length=100,default="false")
    unread_user=models.IntegerField(default=0)
    unread_admin=models.IntegerField(default=0)