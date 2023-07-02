import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header


def generate_email_code():
    code = ""
    for i in range(4):
        code += str(random.randint(0, 9))

    return code


def send_verify_email(email, code):
    con = smtplib.SMTP_SSL('smtp.gmail.com', 465)

    con.login('aistormy2049@gmail.com', 'spnjosyxgljlrthi')

    msg = MIMEMultipart()
    subject = Header('AIStormy verify code', 'utf-8').encode()
    msg['Subject'] = subject
    msg['From'] = 'aistormy2049@gmail.com <aistormy2049@gmail.com>'
    msg['To'] = email
    text = MIMEText('verify code: {}'.format(code), 'plain', 'utf-8')
    msg.attach(text)

    con.sendmail('aistormy2049@gmail.com', 'lishundong2009@163.com', msg.as_string())
    con.quit()
