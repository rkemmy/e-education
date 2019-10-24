import abc
from django.template import Context
from django.template.loader import get_template, render_to_string

class AbstractRenderJinjaMailTemplate(abc.ABC):
    @abc.abstractmethod
    def parse_mail_html_mail_template(self, template, context):
        raise NotImplementedError("Not Implemented")
    
    @abc.abstractmethod
    def parse_mail_text_mail_template(self, template, context):
        raise NotImplementedError("Not Implemented")

class RenderJinjaMailTemplate(AbstractRenderJinjaMailTemplate):
    def __init__(self, *args, **kwargs):
        pass

    def parse_mail_html_mail_template(self, template, context):
        html_template =  get_template(template)
        html_content = render_to_string(template,context)
        return html_content
    
    def parse_mail_text_mail_template(self, template, context):
        text_template =  get_template(template)
        text_content = render_to_string(text_content,context)
        return text_content
