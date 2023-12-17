import psycopg2, psycopg2.extras
import threading, os, smtplib, time, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class DBConnection:
    WEBAPPDB = {
        "database": "observation",
        "host": "localhost",
        "user": "postgres",
        "password": "123",
        "port": "5433"
    }

def django():
    os.system("python manage.py runserver")

def Subscritption():
    connection = psycopg2.connect(**DBConnection.WEBAPPDB)
    cursor = connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
        sender_email = "sridharandeveloper06@outlook.com"
        password = "Project@24"
        server.starttls()
        server.login(sender_email, password)
        while True:
            try:
                cursor.execute("SELECT * FROM api_loginusers")
                loginusers = cursor.fetchall()
                for user in loginusers:
                    if (not user.get('mail_sent', False)) and (datetime.datetime.now() > (datetime.datetime.strftime(user.get('expected_date'), '"%Y-%m-%dT%H:%M"') - datetime.timedelta(days=30))):
                        message = MIMEMultipart()
                        message["Subject"] = "Observation Form Submission"
                        message["From"] = sender_email
                        message["To"] = user.get('email_address')
                        mail_data = "Your Subscription Pack is getting Expired."
                        message.attach(MIMEText(mail_data, "plain"))
                        server.sendmail(sender_email, user.get('email_address'), message.as_string())
                        print("Email sent successfully!")
                        cursor.execute("UPDATE TABLE api_loginusers api_loginusers SET mail_sent = true WHERE id = %s", (user.get('id')))
                        connection.commit()
            except Exception as e:
                print("Cannot send email to the server:", str(e))
        
threading.Thread(target=django).start()
threading.Thread(target=Subscritption).start()