import abc
from .mail_template_render import RenderJinjaMailTemplate
from .sendgrid_mailer import SendGridMailer

class AbstractMailer(abc.ABC):
    '''
    required
        email render
        mailer
    '''
    pass


class Mailer(AbstractMailer):

    def __init__(self):
        self.mail_renderer = RenderJinjaMailTemplate()
        self.mailer  = SendGridMailer()

    def send_email(self, subject,from_email, to_emails, template, context, text=False):
        '''
        Params:
            subject, from_email, to_emailsm template, context, text=False
        '''
        html_content =  self.mail_renderer.parse_mail_html_mail_template(template, context)
        self.mailer.send(from_email,to_emails, subject, html_content, message_type="html")

