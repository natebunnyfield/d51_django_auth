from d51_django_auth.backends import AbstractAuthBackend
from d51_django_auth.twitter.models import TwitterToken
from django import conf
from django.contrib.auth.models import User
from oauthtwitter import OAuthApi
from urllib2 import HTTPError

TWITTER_BACKEND_STRING = 'd51_django_auth.backend.TwitterBackend'

class TwitterBackend(AbstractAuthBackend):
    def __init__(self, **kwargs):
        super(TwitterBackend, self).__init__(**kwargs)
        # TODO: allow injection of settings
        self.settings = conf.settings

    def _get_twitter(self, access_token = None):
        return OAuthApi(
            self.settings.D51_DJANGO_AUTH['TWITTER']['CONSUMER_KEY'],
            self.settings.D51_DJANGO_AUTH['TWITTER']['CONSUMER_SECRET'],
            access_token = access_token
        )

    def _get_access_token(self, request_token):
        oauth = self._get_twitter(request_token)
        return oauth.getAccessToken()

    def authenticate(self, **credentials):
        if not credentials.has_key('request_token'):
            return None
        request_token = credentials['request_token']

        try:
            #import pdb; pdb.set_trace()
            access_token = self._get_access_token(request_token)

            twitter = self._get_twitter(access_token = access_token)
            user_info = twitter.GetUserInfo()

            username = "tw$%s" % user_info.id
            try:
                user = self.user_manager.get(username = username)
            except User.DoesNotExist:
                name = user_info.name.split(' ', 1)
                user = self.user_manager.create(username = username)
                user.first_name = first_name = name[0]
                user.last_name = len(name) > 1 and name[1] or ""
                user.set_unusable_password()
                user.save()

            token, _created = TwitterToken.objects.get_or_create(user = user)
            token.key = access_token.key
            token.secret = access_token.secret
            token.save()

            return user
        except HTTPError, e:
            print e


