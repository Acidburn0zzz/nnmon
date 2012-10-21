from forms import AddViolation, SearchViolation
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext, loader, Context
from django.core.files import File
from django.core.servers.basehttp import FileWrapper
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.db.models import Count
from models import Violation, Attachment, Comment, Confirmation, COUNTRIES, STATUS
from tempfile import mkstemp
from datetime import datetime
import hashlib, os, re, json
from random import randint
from email.mime.text import MIMEText
from email.header import Header
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup, Comment as BComment
from operator import itemgetter

def sanitizeHtml(value, base_url=None):
    rjs = r'[\s]*(&#x.{1,7})?'.join(list('javascript:'))
    rvb = r'[\s]*(&#x.{1,7})?'.join(list('vbscript:'))
    re_scripts = re.compile('(%s)|(%s)' % (rjs, rvb), re.IGNORECASE)
    validTags = 'p i strong b u a h1 h2 h3 pre br img'.split()
    validAttrs = 'href src width height'.split()
    urlAttrs = 'href src'.split() # Attributes which should have a URL
    soup = BeautifulSoup(value)
    for comment in soup.findAll(text=lambda text: isinstance(text, BComment)):
        # Get rid of comments
        comment.extract()
    for tag in soup.findAll(True):
        if tag.name not in validTags:
            tag.hidden = True
        attrs = tag.attrs
        tag.attrs = []
        for attr, val in attrs:
            if attr in validAttrs:
                val = re_scripts.sub('', val) # Remove scripts (vbs & js)
                if attr in urlAttrs:
                    val = urljoin(base_url, val) # Calculate the absolute url
                tag.attrs.append((attr, val))

    return soup.renderContents().decode('utf8')

def activate(request):
    try:
        v=Violation.objects.get(activationid=request.GET.get('key','asdf'))
    except:
        messages.add_message(request, messages.INFO, unicode(_('Thank you, this key has been already activated')))
        return HttpResponseRedirect('/') # Redirect after POST
    if v:
        actid = hashlib.sha1(''.join([chr(randint(32, 122)) for x in range(12)])).hexdigest()
        to=[x.email for x in User.objects.filter(groups__name='moderator')]
        details='\n'.join(["%s: %s" % (k.capitalize(), val) for k,val in v.__dict__.items() if not k.startswith('_') and val])

        msg = {'from': 'nnmon@respectmynet.eu',
               'to': to,
               'subject': 'NNMon submission approval'.encode("Utf-8"),
               'body': "A new report was submitted. To approve click here: %s/moderate/?key=%s\n\nDetails follow:\n%s\n%s" %
                       (settings.ROOT_URL or 'http://localhost:8001/', actid, details, v.comment_set.get().comment)
               }
        send_mail(msg['subject'], msg['body'], msg['from'], msg['to'], fail_silently=False)

        v.activationid=actid
        v.save()
        messages.add_message(request, messages.INFO, _('Thank you for verifying your submission. It will be listed shortly, after we\'ve checked that the report is valid.').encode("Utf-8"))
    return HttpResponseRedirect('/') # Redirect after POST

def moderate(request):
    try:
        v=Violation.objects.get(activationid=request.GET.get('key','asdf'))
    except:
        messages.add_message(request, messages.INFO, unicode(_('Thank you, this key has been already activated')))
        return HttpResponseRedirect('/') # Redirect after POST
    if not v:
        messages.add_message(request, messages.INFO, _('No such key'))
        return HttpResponseRedirect('/') # Redirect after POST
    if request.GET.get('action','')=='approve':
        messages.add_message(request, messages.INFO, _('Thank you for approving the <a href="%s">submission</a>.' % v.get_absolute_url))

        msg = {'from': 'nnmon@respectmynet.eu',
               'to': [v.comment_set.get().submitter_email],
               'subject': _('NNMon submission approved').encode("Utf-8"),
               'body': _("Your report has been approved.\nTo see it, please visit: %s/view/%s") %
                      (settings.ROOT_URL or 'http://localhost:8001/', v.get_absolute_url())
               }
        send_mail(msg['subject'], msg['body'], msg['from'], msg['to'], fail_silently=False)

        s.quit()
        if settings.TWITTER_API:
            try:
                settings.TWITTER_API.PostUpdate("New #NetNeutrality violation reported for %s (%s) %s %s/%s" % (v.operator, v.country, v.contract, settings.ROOT_URL or 'http://localhost:8001/', v.id))
            except:
                pass
        v.activationid=''
        v.save()
        return redirect(v) # Redirect after POST to violation url
    if request.GET.get('action','')=='delete':
        v.delete()
        messages.add_message(request, messages.INFO, _('Thank you for deleting the submission.'))
        return HttpResponseRedirect('/') # Redirect after POST
    return render_to_response('view.html', { 'v': v, 'key': request.GET.get('key') },context_instance=RequestContext(request))

def confirm(request, id, name=None):
    if name:
        if Confirmation.objects.filter(email=name, violation=id).count()==0:
            msg=_("Thank you for confirming a case. To finalize your confirmation please validate using your confirmation key.\nYour confirmation key is %s/%s%s")
            actid=sendverifymail('confirm/',name, msg)
            try:
                c=Confirmation(key=actid, email=name, violation=Violation.objects.get(pk=id))
            except:
                return HttpResponse(unicode(_('Thank you, this has been already confirmed')))
            c.save()
        return HttpResponse(unicode(_('Thank you for your confirmation')))
    try:
        c = get_object_or_404(Confirmation, key=id)
    except:
        messages.add_message(request, messages.INFO, unicode(_("Thank you, this has been already confirmed")))
        return HttpResponseRedirect('/') # Redirect after POST
    c.key=''
    c.save()
    messages.add_message(request, messages.INFO, unicode(_('Thank you for verifying your confirmation')))
    return HttpResponseRedirect('/') # Redirect after POST

def sendverifymail(service,to,body):
    actid = hashlib.sha1(''.join([chr(randint(32, 122)) for x in range(12)])).hexdigest()
    msg = {'from': 'nnmon@respectmynet.eu',
           'to': [to.encode("Utf-8")],
           'subject': _('NNMon submission verification').encode("Utf-8"),
           'body': body % (settings.ROOT_URL or 'http://localhost:8001/', service, actid),
           }
    send_mail(msg['subject'], msg['body'], msg['from'], msg['to'], fail_silently=False)

    return actid

def add(request):
    if request.method == 'POST':
        form = AddViolation(request.POST)
        if form.is_valid():
            msg=_("Thank you for submitting a new report. To finalize your submission please confirm using your validation key.\nYour verification key is %s/%s%s\nPlease note that reports are moderated, it might take some time before your report appears online. Thank you for your patience.")
            actid=sendverifymail('activate?key=',form.cleaned_data['email'], msg)
            operator, created = Operator.objects.get_or_create(name=form.cleaned_data['operator'])
            v=Violation(
                country = form.cleaned_data['country'],
                operator_ref = operator,
                contract = form.cleaned_data['contract'],
                resource = form.cleaned_data['resource'],
                resource_name = form.cleaned_data['resource_name'],
                type = form.cleaned_data['type'],
                media = form.cleaned_data['media'],
                temporary = form.cleaned_data['temporary'],
                contractual = form.cleaned_data['contractual'],
                contract_excerpt = sanitizeHtml(form.cleaned_data['contract_excerpt']),
                loophole = form.cleaned_data['loophole'],
                activationid = actid
                )
            v.save()
            #c=Confirmation(key='', email=form.cleaned_data['email'], violation=v)
            #c.save()
            c = Comment(
                comment=form.cleaned_data['comment'],
                submitter_email=form.cleaned_data['email'],
                submitter_name=form.cleaned_data['nick'],
                consent=form.cleaned_data['consent'],
                timestamp=datetime.now(),
                violation=v,
                )
            c.save()
            for f in request.FILES.getlist('attachments[]'):
                a=Attachment(comment=c, name=f.name, type=f.content_type)
                m = hashlib.sha256()
                for chunk in f.chunks():
                    m.update(chunk)
                sname=m.hexdigest()
                a.storage.save(sname,f)
                a.save()

            messages.add_message(request, messages.INFO, _('Thank you for submitting this report, you will receive a verification email immediately, if not check your spam folder.'))
            return HttpResponseRedirect('/') # Redirect after POST
    else:
        form = AddViolation()

    v_list = Violation.objects.filter(activationid='',featuredcase__isnull=False).order_by('id').reverse()[:3]
    return render_to_response(
        'index.html',
        { 'form': form,
          'violations': v_list },
        context_instance=RequestContext(request))

# XXX obsoleted by API
#def ajax(request, country=None, operator=None):
#    if not operator:
#        return HttpResponse(json.dumps(sorted(list(set([x.operator for x in Violation.objects.filter(country=country,activationid='')])))))
#    else:
#        return HttpResponse(json.dumps(sorted(list(set([x.contract for x in Violation.objects.filter(country=country,activationid='',operator=operator)])))))

def index(request):
    v_list = Violation.objects.filter(activationid='',featuredcase__isnull=False).order_by('id').reverse()[:3]
    form = AddViolation()
    reports=sorted([(i['total'],i['id'])
                     for i in Violation.objects.values('id').filter(activationid='').exclude(state__in=['closed', 'ooscope', 'duplicate']).annotate(total=Count('confirmation'))],
                    reverse=True)
#    countries=sorted([(i['total'],i['country'])
#                      for i in Violation.objects.values('country').filter(activationid='').annotate(total=Count('country'))],
#                     reverse=True)
    confirms=sorted([(i['total'],i['country'])
                     for i in Violation.objects.values('country').filter(activationid='').exclude(state__in=['closed', 'ooscope', 'duplicate']).annotate(total=Count('confirmation'))],
                    reverse=True)
    operators=sorted([(i['total'],i['operator_ref__name'])
                     for i in Violation.objects.values('operator_ref__name').filter(activationid='').exclude(state__in=['closed', 'ooscope', 'duplicate']).annotate(total=Count('confirmation'))],
                     reverse=True)

    return render_to_response(
        'index.html',
        { 'form': form,
          'stats': [ (_('Total confirmed reports'), len([i for i,z in reports if i>0])),
                     (_('Countries with some confirmed reports'), len([i for i,z in confirms if i>0])),
                     (_('Operators with some confirmed reports'), len([i for i,z in operators if i>0])),
                     ],
          'violations': v_list },
        context_instance=RequestContext(request))

def filter_violations(request, country, operator=None):
    if not operator:
        violations = Violation.objects.filter(activationid='', country=country)
        if not violations.count():
            violations = Violation.objects.filter(activationid='', operator_ref__name=country)
    else:
        violations = Violation.objects.filter(activationid='', country=country, operator_ref__name=operator)
    if not request.GET.get('all'):
        violations = violations.exclude(state__in=['duplicate', 'closed'])
    countries=sorted([(i['total'],i['country'])
                      for i in Violation.objects.values('country').filter(activationid='',country=country).exclude(state__in=['duplicate', 'closed']).annotate(total=Count('country'))],
                     reverse=True)
    countryweights=json.dumps([{'iso2': y, 'w': x} for x, y in countries])
    return render_to_response('list.html',
                              { "violations": violations,
                               "country": country,
                                "status": STATUS },
                              context_instance=RequestContext(request))

def list_violations(request):
    violations = Violation.objects.filter(activationid='')
    if not request.GET.get('all'):
        violations = violations.exclude(state__in=['duplicate', 'closed'])
    countries=sorted([(i['total'],i['country'])
                      for i in Violation.objects.values('country').filter(activationid='').exclude(state__in=['duplicate', 'closed']).annotate(total=Count('country'))],
                     reverse=True)
    countryweights=json.dumps([{'iso2': y, 'w': x} for x, y in countries])
    #countrycolors=json.dumps(dict([(c.lower(),"#ff%02x00" % (w*768/(countries[0][0]+1)%256)) for w,c in countries]))
    #confirms=sorted([(i['total'],i['country'])
    #                 for i in Violation.objects.values('country').filter(activationid='').annotate(total=Count('confirmation'))
    #                 if i['total']>1],
    #                reverse=True)
    return render_to_response('list.html',
                              {"violations": violations,
                               "countries": dict([(y,x) for x,y in countries]),
                               "countryweights": countryweights,
                               "status": STATUS,},
                               #"confirms": confirms,},
                              context_instance=RequestContext(request))

def view(request,id):
    v = get_object_or_404(Violation, pk=id)
    if v.activationid:
        raise Http404
    return render_to_response('view.html', { 'v': v, },context_instance=RequestContext(request))

def get_attach(request,id):
    f = get_object_or_404(Attachment, pk=id)
    wrapper = FileWrapper(f.storage)
    response=HttpResponse(wrapper, mimetype=f.type)
    response['Content-Disposition'] = 'attachment; filename="%s"' % f.name
    response['Content-Length'] = f.storage.size
    return response

def lookup(request):
    if request.method == 'GET':
        form = SearchViolation(request.GET)
        if form.is_valid():
            v=Violation.objects.filter(
                country = form.cleaned_data['country'],
                operator_ref__name = form.cleaned_data['operator'],
                contract = form.cleaned_data['contract'],
                media = form.cleaned_data['media'],
                activationid = ''
                )
            res=json.dumps(sorted([(x.id,x.resource_name) for x in v],reverse=True))
            return HttpResponse(res)
    return HttpResponse('')

def ascsv(request):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=respectmynet.csv'

    res=[]
    for v in Violation.objects.filter(activationid=''):
        res.append((v.state, v.country, v.operator, v.contract, v.resource, v.resource_name, v.type, v.media, v.temporary, v.contractual, v.contract_excerpt, v.loophole, v.editorial,v.comment_set.get().comment))
    t = loader.get_template('csv.tmpl')
    c = Context({
        'data': res,
    })
    response.write(t.render(c))
    return response

from sheet import save_ods
def asods(request):
    response = HttpResponse(mimetype='application/vnd.oasis.opendocument.spreadsheet')
    response['Content-Disposition'] = 'attachment; filename=respectmynet-ec_berec_tm_questionnaire.ods'
    save_ods()
    f=open('/tmp/ec_berec_tm_questionnaire.ods','r')
    response.write(f.read())
    f.close()
    return response
