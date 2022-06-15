from dotenv import load_dotenv
import smtplib
import os
from email.message import EmailMessage

def send_message(subject, body, to):
    load_dotenv()

    emailUser = os.environ.get("EMAIL_USER")
    emailPsswd = os.environ.get("EMAIL_PASSWORD")

    msg = EmailMessage()
    msg.set_content(body)

    msg['subject'] = subject
    msg['to'] = to
    msg['from'] = emailUser

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(emailUser, emailPsswd)
    server.send_message(msg)

    server.quit()


if __name__ == '__main__':
    emailUser = os.environ.get("EMAIL_USER")
    emailPsswd = os.environ.get("EMAIL_PASSWORD")
    alertEmail = os.environ.get("ALERT_EMAIL")

    print('Sending test message')
    send_message("hey", "hello world", alertEmail)
