from django.conf.urls.defaults import patterns, include, url
from django.views.generic.simple import direct_to_template, redirect_to
from django.conf import settings
from django.contrib import admin
from bt import views as bt
from bt.feeds import RssSiteNewsFeed, AtomSiteNewsFeed

from bt.api import APIResource

api_resource = APIResource()


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$',
        view=bt.index,
        name="homepage"),
    url(r'^list/$',
        view=bt.list_violations,
        name="list_violations"),
    url(r'^list/(?P<country>[^/]*)(/(?P<operator>[^/]*))?$',
        view=bt.filter_violations,
        name="filter"),
    url(r'^add/$',
        view=bt.add,
        name="add_violation"),
    # violation cannonical url and redirections
    url(r'^(?P<id>[0-9]*)$',
        redirect_to,
        {'url': '/view/%(id)s'}),
    url(r'^view/(?P<id>[0-9]*)$',
        view=bt.view,
        name="violation_url"),
    url(r'^attach/(?P<id>[0-9]*)$',
        view=bt.get_attach,
        name="attach"),
    # different data outputs
    url(r'^csv$',
        view=bt.ascsv,
        name="csv_output"),
    url(r'^ods$',
        view=bt.asods,
        name="ods_output"),
    url(r'^rss/$',
        view=RssSiteNewsFeed(),
        name="rss_output"),
    url(r'^atom/$',
        view=AtomSiteNewsFeed(),
        name="atom_output"),
    url(r'^activate/$',
        view=bt.activate,
        name="activate"),
    url(r'^confirm/(?P<id>[0-9a-z]*)$',
        view=bt.confirm,
        name="confirm"),
    url(r'^confirm/(?P<id>[0-9]*)/(?P<name>.*)$',
        view=bt.confirm,
        name="confirm_full"),
    url(r'^moderate/$',
        view=bt.moderate,
        name="moderate"),
    url(r'^lookup/$',
        view=bt.lookup,
        name="lookup"),
    url(r'^accounts/logout$',
        'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^accounts/',
        include('registration.urls')),
    url(r'^comments/',
        include('django.contrib.comments.urls')),
    url(r'^about/$',
        direct_to_template, {'template': 'nn.html'}),
    url(r'^start/$',
        direct_to_template, {'template': 'start.html'}),
    url(r'^contact/$',
        direct_to_template, {'template': 'about.html'}),
    url(r'^captcha/',
        include('captcha.urls')),
    url(r'^admin/',
        include(admin.site.urls)),
    url(r'^api/',
        include(api_resource.urls)),
)

if settings.DEV_SERVER:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$',
            'django.views.static.serve',
            {'document_root': settings.MEDIA_PATH}),
    )
