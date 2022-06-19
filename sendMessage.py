from dotenv import load_dotenv
import smtplib
import os
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def send_message(subject, body, to):
    load_dotenv()

    emailUser = os.environ.get("EMAIL_USER")
    emailPsswd = os.environ.get("EMAIL_PASSWORD")


    msg = MIMEMultipart('alternative')
    msg['subject'] = subject
    msg['to'] = to
    msg['from'] = emailUser

    text = MIMEText('<img src="cid:image1">' + '<br>'+body, 'html')
    msg.attach(text)

    image = MIMEImage(open('/home/akendrick/Dropbox/Personal/Arduino/weatherAlmanac/todayTemp.png', 'rb').read())

    # Define the image's ID as referenced in the HTML body above
    image.add_header('Content-ID', '<image1>')
    msg.attach(image)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(emailUser, emailPsswd)
    server.sendmail(emailUser,to,msg.as_string())

    server.quit()

if __name__ == '__main__':
    emailUser = os.environ.get("EMAIL_USER")
    emailPsswd = os.environ.get("EMAIL_PASSWORD")
    alertEmail = os.environ.get("ALERT_EMAIL")

    print('Sending test message')
    send_message("hey", "hello world", alertEmail)
