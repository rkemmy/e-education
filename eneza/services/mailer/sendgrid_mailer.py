from sendgrid import  SendGridAPIClient
from sendgrid.helpers.mail import Mail 
from django.conf import settings

class SendGridMailer:
    def __init__(self, *args, **kwargs):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)

    def send(self, from_email, to_emails, subject, message, message_type="html"):
        # if type(to_emails) == list:
        #     to_emails = ",".join(to_emails)
        context = {"from_email":from_email, "to_emails":to_emails,"subject":subject}
        if message_type=="html":
            context["html_content"] = message
        elif message_type=="text":
            context["plain_text_content"] = message
        message = Mail(**context)
        response=self.client.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)