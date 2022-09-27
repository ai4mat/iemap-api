# Import modules
from os import link
import smtplib, ssl
from datetime import date, datetime

## email.mime subclasses
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from core.config import Config

# Connect to the Gmail SMTP server and Send Email
context = ssl.SSLContext(ssl.PROTOCOL_TLS)
# ssl.create_default_context()

# date_str = datetime.now().strftime("%Y-%m-%d %H:%M")


class Email:

    # Create a MIMEMultipart class,
    # and set up the From, To, Subject fields
    email_message = MIMEMultipart()
    # Convert it as a string
    email_text = email_message.as_string()
    email_message["Subject"] = f"Activate your account"
    email_from = Config.smtp_from
    password = Config.smtp_pwd
    email_message["From"] = email_from

    # defining constructor
    def __init__(self):
        pass

    def send(self, list_to_email):
        with smtplib.SMTP(Config.smtp_server, 587) as server:
            server.starttls()
            server.login(self.email_from, self.password)
            server.sendmail(
                self.email_from, list_to_email, self.email_message.as_string()
            )

    def send_verify_email(self, list_to_email: list, base_url: str, token: str):

        # Define the HTML document
        html_template_verify_account = f"""
            <html>
                <body>
                    <h1>Please verify your account</h1>
                    <p> Click the following <a href="{base_url}{token}"> link </a> to verify your account.</p>
                    
                </body>
            </html>
            """

        # self.email_message["To"] = ",".join(list_to_email)
        self.email_message["Subject"] = "Activate your account"
        # Attach the html doc defined earlier, as a MIMEText html content type to the MIME message
        self.email_message.attach(MIMEText(html_template_verify_account, "html"))
        self.send(list_to_email)
