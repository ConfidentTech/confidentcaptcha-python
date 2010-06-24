# -*- coding: utf-8 -*-
'''Settings for Confident CAPTCHA'''

# Enter your login.confidenttechnologies.com account information here
api_credentials = {
    'customer_id': '',
    'site_id': '',
    'api_username': '',
    'api_password': '',
}

# You shouldn't need to modify this, unless you are running your own captcha service.
captcha_server_url = 'http://captcha.confidenttechnologies.com/'

# Set to True to enable the audio CAPTCHA alternative, False to disable
# Audio CAPTCHA will only appear if your API account has Audio CAPTCHA enabled
#  (a.k.a. voiceptl).  See login.confidenttechnologies.com for what services
#  are enabled for your account.
include_audio = True

# Path on your server for JavaScript to call
# It should be a relative path, and not start with /
callback_url = 'callback'


# Local overrides - used by Confident Technologies for testing.
try:
    from local_captchalib_config import *
except ImportError:
    pass

# vi: expandtab tabstop=4 shiftwidth=4
