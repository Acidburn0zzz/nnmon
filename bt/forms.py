from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from bt.models import Violation, COUNTRIES, RESOURCES, TYPES, MEDIA
from bt.multifile import MultiFileField
from operator import itemgetter
from captcha.fields import CaptchaField

class AdvancedEditor(forms.Textarea):
	class Media:
		js = (settings.MEDIA_URL+'/js/tinymce/tiny_mce.js',)

	def __init__(self, language=None, attrs=None):
		self.language = language or settings.LANGUAGE_CODE[:2]
		self.attrs = {'class': 'advancededitor'}
		if attrs: self.attrs.update(attrs)
		super(AdvancedEditor, self).__init__(attrs)

class AddViolation(forms.Form):
   resource_name = forms.CharField(required=True, max_length=4096, label=_('Please specify the affected resource'), help_text=_("What service or site, or person is unavailable or seems artificially slowed down. e.g. VoIP, p2p, filesharing, specific websites, etc."))
   country = forms.ChoiceField(required=True, choices=(('',''),)+tuple(sorted(COUNTRIES,key=itemgetter(1))), label=_("Country"), help_text=_('EU member state where the restriction is reported.'))
   operator = forms.CharField(required=True, max_length=256, label=_("Operator"), help_text=_('The ISP or operator providing the Internet service.'))
   contract = forms.CharField(required=True, max_length=256, label=_("Contract"), help_text=_('The specific contract at the ISP provider. (please be as specific as possible)'))
   media = forms.ChoiceField(required=True, choices=(('',''),)+tuple(sorted(MEDIA,key=itemgetter(1))), label=_('Is the Internet connection over mobile or fixed line?'))
   comment = forms.CharField(required=True, widget=AdvancedEditor(), label=_('Please describe the symptoms you are experiencing.'))
   email = forms.EmailField(required=True, label=_('Email (set this to enable saving)'), help_text=_("We need your email to validate your report. Your email address is obligatory, but we will never use your personal data for anything else than checking the submission. (see next for an optional exception)"))
   consent = forms.BooleanField(required=False, label=_("I want to help further"), help_text=_("We need your consent to contact you for clarifications regarding your report. This is optional, but helps us improve the quality of the reports. Thanks!"))
   nick = forms.CharField(required=False, label=_("Name or nickname"), help_text=_("We need some name to display that instead of an email address."))
   attachments = MultiFileField(required=False, label=_("Attach screenshot, document or any other relevant information."))
   resource = forms.ChoiceField(required=False, choices=(('',''),)+tuple(sorted(RESOURCES,key=itemgetter(1))), label=_('What is the affected resource type. (optional)'))
   type = forms.ChoiceField(required=False, choices=(('',''),)+tuple(sorted(TYPES,key=itemgetter(1))), label=_('Is the Resource Blocked or otherwise discrimated? (optional)'))
   temporary = forms.BooleanField(required=False, label=_('Is the restriction only temporary, e.g. due to network overload? (optional)'))
   loophole = forms.BooleanField(required=False, label=_('Is there another offer provided by this Operator which removes this restriction? (optional)'))
   contractual = forms.BooleanField(required=False, label=_('Is the restriction described in the subscribers contract? (optional)'))
   contract_excerpt = forms.CharField(required=False, widget=AdvancedEditor(), label=_('Please copy the relevant section describing the restriction from the user contract. (optional)'))
   captcha = CaptchaField(label=_("In order to protect against spam, please fill in the result of the following calculation. (note the + and the * are somewhat confusing)"))

class SearchViolation(forms.Form):
   country = forms.ChoiceField(required=True, choices=(('',''),)+tuple(sorted(COUNTRIES,key=itemgetter(1))), label=_("Country"), help_text=_('EU member state where the restriction is reported.'))
   operator = forms.CharField(required=True, max_length=256, label=_("Operator"), help_text=_('The ISP or operator providing the Internet service.'))
   contract = forms.CharField(required=True, max_length=256, label=_("Contract"), help_text=_('The specific contract at the ISP provider. (please be as specific as possible)'))
   media = forms.ChoiceField(required=True, choices=(('',''),)+tuple(sorted(MEDIA,key=itemgetter(1))), label=_('Is the Internet connection over mobile or fixed line?'))
