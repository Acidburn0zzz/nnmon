from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from bt.models import Violation, COUNTRIES, RESOURCES, TYPES, MEDIA
from operator import itemgetter

class AdvancedEditor(forms.Textarea):
	class Media:
		js = (settings.MEDIA_URL+'/js/tinymce/tiny_mce.js',)

	def __init__(self, language=None, attrs=None):
		self.language = language or settings.LANGUAGE_CODE[:2]
		self.attrs = {'class': 'advancededitor'}
		if attrs: self.attrs.update(attrs)
		super(AdvancedEditor, self).__init__(attrs)

class AddViolation(forms.Form):
   country = forms.ChoiceField(required=True, choices=(('',''),)+tuple(sorted(COUNTRIES,key=itemgetter(1))), help_text=_('EU member state where the restriction is reported.'))
   operator = forms.CharField(required=True, max_length=256, help_text=_('The ISP or operator providing the Internet service.'))
   contract = forms.CharField(required=True, max_length=256, help_text=_('The specific contract at the ISP provider. (please be as specific as possible)'))
   comment = forms.CharField(required=True, widget=AdvancedEditor(), help_text=_('Please describe the symptoms you are experiencing. What service or site, or person is unavailable or seems artificially slowed down.'))
   resource = forms.ChoiceField(required=False, choices=(('',''),)+tuple(sorted(RESOURCES,key=itemgetter(1))), help_text=_('The what is the affected resource.'))
   resource_name = forms.CharField(required=False, max_length=4096, help_text=_('Please specify the name of the affected resource.'))
   type = forms.ChoiceField(required=False, choices=(('',''),)+tuple(sorted(TYPES,key=itemgetter(1))), help_text=_('Is the Resource Blocked or otherwise discrimated?'))
   media = forms.ChoiceField(required=False, choices=(('',''),)+tuple(sorted(MEDIA,key=itemgetter(1))), help_text=_('Is the Internet connection over mobile or fixed line?'))
   temporary = forms.BooleanField(required=False, help_text=_('Is the restriction only temporary, e.g. due to network overload?'))
   contractual = forms.BooleanField(required=False, help_text=_('Is the restriction described in the users contract?'))
   contract_excerpt = forms.CharField(required=False, widget=AdvancedEditor(), help_text=_('Please copy the relevant section describing the restriction from the user contract.'))
   loophole = forms.BooleanField(required=False, help_text=_('Is there another offer provided by this Operator which removes this restriction?'))
