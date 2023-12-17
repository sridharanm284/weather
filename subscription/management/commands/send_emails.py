from django.core.management.base import BaseCommand
import psycopg2, psycopg2.extras
import threading, os, smtplib, time, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dateutil.parser import parse

class DBConnection:
    WEBAPPDB = {
        "database": "observation",
        "host": "localhost",
        "user": "postgres",
        "password": "123",
        "port": "5433"
    }

class Command(BaseCommand):
    help = 'Description of your custom command'

    def handle(self, *args, **kwargs):
        print("Send Subscription Running on background")
        connection = psycopg2.connect(**DBConnection.WEBAPPDB)
        cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
            sender_email = "sridharandeveloper06@outlook.com"
            password = "Project@1234"
            server.starttls()
            server.login(sender_email, password)
            while True:
                try:
                    cursor.execute("SELECT * FROM api_loginusers")
                    loginusers = cursor.fetchall()
                    for user in loginusers:
                        if (not user.get('mail_sent', False)):
                            expected_date_str = user.get('expected_date')  # Assuming it's in ISO 8601 format
                            expected_date = parse(expected_date_str)
                            thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
                            if expected_date < thirty_days_ago:
                                message = MIMEMultipart()
                                message["Subject"] = "Observation Form Submission"
                                message["From"] = sender_email
                                message["To"] = user.get("email_address")
                                mail_data = "Your Subscription Pack is getting Expired."
                                message.attach(MIMEText(mail_data, "plain"))
                                server.sendmail(sender_email, user.get("email_address"), message.as_string())
                                print("Email sent successfully!")
                                
                                cursor.execute("UPDATE api_loginusers SET mail_sent = true WHERE id = %s", (user.get('id'),))
                                connection.commit()
                except Exception as e:
                    print("Cannot send email to the server:", str(e))
                    break
        self.stdout.write(self.style.SUCCESS('Emails sent successfully!'))
