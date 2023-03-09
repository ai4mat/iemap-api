import aiofiles
import aiosmtplib


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from core.config import Config

MAIL_PARAMS = {
    "TLS": True,
    "host": Config.smtp_server,
    "password": Config.smtp_pwd,
    "user": Config.smtp_from,
    "port": 587,
}


async def send_mail_async(to, subject, text, **params):
    """Send an outgoing email with the given parameters.

    :param sender: From whom the email is being sent
    :type sender: str

    :param to: A list of recipient email addresses.
    :type to: list

    :param subject: The subject of the email.
    :type subject: str

    :param text: The text of the email.
    :type text: str

    :param textType: Mime subtype of text, defaults to 'plain' (can be 'html').
    :type text: str

    :param params: An optional set of parameters. (See below)
    :type params; dict

    Optional Parameters:
    :cc: A list of Cc email addresses.
    :bcc: A list of Bcc email addresses.
    """

    # Default Parameters
    cc = params.get("cc", [])
    bcc = params.get("bcc", [])
    mail_params = params.get("mail_params", MAIL_PARAMS)

    # Prepare Message
    msg = MIMEMultipart()
    msg.preamble = subject
    msg["Subject"] = subject
    msg["From"] = MAIL_PARAMS["user"]
    msg["To"] = ", ".join(to)
    if len(cc):
        msg["Cc"] = ", ".join(cc)
    if len(bcc):
        msg["Bcc"] = ", ".join(bcc)

    msg.attach(MIMEText(text, "html"))

    # Contact SMTP server and send Message
    # sender=MAIL_PARAMS["user"]
    host = mail_params.get("host", Config.smtp_server)
    isSSL = mail_params.get("SSL", False)
    isTLS = mail_params.get("TLS", False)
    port = mail_params.get("port", 465 if isSSL else 25)

    smtp = aiosmtplib.SMTP(
        hostname=host,
        port=587,
        start_tls=False,
        use_tls=False,
        # port=port,
        # use_tls=isSSL,
    )
    await smtp.connect()
    if isTLS:
        await smtp.starttls()
    if "user" in mail_params:
        await smtp.login(mail_params["user"], mail_params["password"])
    await smtp.send_message(msg)
    await smtp.quit()


async def readVerifyMailTemplate(filename, linkToVerifyEndpoint):
    async with aiofiles.open(filename, mode="r") as f:
        contents = await f.read()
        link = f'href="{linkToVerifyEndpoint}"'
        contents = contents.replace('href="{{}}"', link)
        return contents


# read mail template for reset password
# template in path /templates/reset_pwd_template.html
# use href="{{}}" to replace with linkToResetPasswordEndpoint
async def readResetPasswordMailTemplate(filename, linkToResetPasswordEndpoint):
    async with aiofiles.open(filename, mode="r") as f:
        contents = await f.read()
        link = f'href="{linkToResetPasswordEndpoint}"'
        contents = contents.replace('href="{{}}"', link)
        return contents


# https://stackoverflow.com/questions/60224850/send-mail-python-asyncio#60226128
