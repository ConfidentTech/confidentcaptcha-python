# -*- coding: utf-8 -*-\
'''Confident CAPTCHA Python Library'''

import string
import sys
import urllib
import urllib2

import captchalib_config
CALLBACK_OK='The callback is working.'

def make_request(resource, parameters, method = 'POST', expected=[200], server_url = None):
    '''POST a request to the captcha server, returning HTTP code and content string.

    Keyword arguments:
    resource - The path to request on the CAPTCHA server, such as 'captcha'
    parameters - A dictionary of POST form parameters
    method - Optional HTTP method.  Accepted values are 'POST' and 'GET'
    server_url - Optional server URL, overriding captchalib_config.captcha_server_url
    '''

    server = server_url or captchalib_config.captcha_server_url
    assert(server)

    params = dict([(k,v or '') for k,v in parameters.items()])
    params['library_version'] = '20100621_PYTHON'
    url = server + resource
    if method == 'GET':
        req = urllib2.Request(url + '?' + urllib.urlencode(params))
    else:
        req = urllib2.Request(url, urllib.urlencode(params))

    try:
        resp = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        err = e.read()
        if (e.code not in expected):
            print >> sys.stderr, "An HTTP error occurred (%d %s):\n%s" % (e.code, e.msg, err)
        return (e.code, err)
    except urllib2.URLError, e:
        code, message = e.reason
        print >> sys.stderr, "A socket error occurred (%d %s)" % (code, message)
        return (0, "Server at %s is not responding: %d '%s'.\n"%(server, code, message))
    except Exception, e:
        print >> sys.stderr, "An unknown error occurred:\n%s" % e
        return (0, "Unknown error:\n%s" % e)
    else:
        return (resp.code, resp.read())


def get_user_info(environ):
    '''Get the user's IP address and browser agent

    Keyword Arguments:
    environ - A dictionary of request variables, like as WSGI environ
    '''

    if environ.get('HTTP_CLIENT_IP', ''):
        # IP from share internet
        ip = environ['HTTP_CLIENT_IP']
    elif environ.get('HTTP_X_FORWARDED_FOR', ''):
        # IP from proxy
        ip = environ['HTTP_X_FORWARDED_FOR']
    else:
        # IP from request
        ip = environ.get('REMOTE_ADDR', '')
    agent = environ.get('HTTP_USER_AGENT', '')
    return ip, agent


def create_block(user_ip, user_agent, api_credentials=None, server_url=None):
    '''Create a CAPTCHA block, returning HTTP code and content string.

    Keyword arguments:
    user_ip - The end-user's IP address, for risk profile
    user_agent - The end-user's browser agent, for risk profile
    api_credentials - An optional dictionary containing API credentials and settings
    server_url - An optional override of the server url
    '''
    creds = api_credentials or captchalib_config.api_credentials
    params = creds.copy()
    params['ip_addr'] = user_ip
    params['user_agent'] = user_agent
    return make_request('block', params, server_url=server_url)


def create_instance(block_id, captcha_length=None, width=None, height=None,
    image_code_color=None, include_audio_form=None, display_style=None,
    max_attempts=None, server_url=None):
    '''Create a visual (and maybe audio) CAPTCHA instance, returning HTTP code and content string.

    Not all combinations of captcha_length, width, and height are valid.  There
    are a limited number of categories, and if a captcha is "too easy" it will
    be rejected.  In the future, this may be taken as a minimal value, and the
    actual visual CAPTCHA may be larger for end users with a larger risk profile.

    Keyword arguments:
    block_id - The block ID included in create_block's return
    captcha_length - Optional number of images to select, defaults to 3
    width - Optional grid width, defaults to 3
    height - Optional grid height, defaults to 4
    image_code_color - Optional code color, defaults to White, one of 
        White, Red, Orange, Yellow, Green, Teal, Blue, Indigo, Violet, Gray
    include_audio_form - Optional include audio, defaults to False
    display_style - Optional style 'flyout' (default) or 'lightbox'
    include_audio - True if audio CAPTCHA should be included (default False)
    max_attempts - Number of CAPTCHAs before lockout (default 3)
    server_url - An optional override of the server url
    '''

    params = dict()
    if captcha_length: params['captcha_length'] = captcha_length
    if width: params['width'] = width
    if height: params['height'] = height
    if image_code_color: params['image_code_color'] = image_code_color
    if include_audio_form: params['include_audio_form'] = include_audio_form
    if display_style: params['display_style'] = display_style
    if max_attempts: params['max_attempts'] = max_attempts

    resource = 'block/%s/visual'%(block_id)
    return make_request(resource, params, expected=[200,410], server_url=server_url)


def check_instance(block_id, visual_id, code, server_url=None):
    '''Check a visual CAPTCHA, returning code and content string

    Keyword arguments:
    block_id - The block ID included in create_block's return
    visual_id - The visual ID included in create_instance's return
    code - The code guessed by the user
    server_url - An optional override of the server url
    '''
    params = dict(code=code)
    resource = 'block/%s/visual/%s'%(block_id, visual_id)
    return make_request(resource, params, server_url=server_url);


def start_block_audio(block_id, phone_number, server_url=None):
    '''Start an audio CAPTCHA, returning HTTP code and content string.

    Keyword arguments:
    block_id - The block ID included in create_block's return
    phone_number - The phone number provided by the user
    server_url - An optional override of the server url
    '''
    params = dict(phone_number=phone_number)
    resource = '/block/%s/audio'%block_id
    return make_request(resource, params, server_url=server_url)


def check_block_audio(block_id, audio_id, server_url=None):
    '''Check an audio CAPTCHA, returning HTTP code and content string.

    Keyword arguments:
    block_id - The block ID included in create_block's return
    audio_id - The audio ID included in start_audio's return
    server_url - An optional override of the server url
    '''
    resource = 'block/%s/audio/%s'%(block_id, audio_id)
    return make_request(resource, dict(), method='GET', server_url=server_url);


def callback(environ, parameters, api_credentials=None, server_url=None):
    '''Callback for in-browser checking

    Keyword arguments:
    environ - Dictionary of the request environment, like WSGI environ
    parameters - Dictionary of the request parameters
    api_credentials - An optional dictionary containing API credentials and settings
    server_url - An optional override of the server url

    Return is tuple of:
        HTTP code
        List of headers
        Body
    '''
    def bad_request(reason):
        return (400, [('Content-type', 'plain/text')], reason)

    endpoint = parameters.get('endpoint', None)
    if endpoint == 'block_onekey_start':
        block_id = parameters.get('block_id', None)
        if not block_id: return bad_request('block_id must be set.')
        phone_number = parameters.get('phone_number', None)
        if not phone_number: return bad_request('phone_number must be set.')

        audio_code, audio_id = start_block_audio(block_id, phone_number,
            server_url=server_url)
        xml = '''\
<?xml version="1.0"?>
<response>
  <status>%(audio_code)d</status>
  <onekey_id>%(audio_id)s</onekey_id>
</response>''' % locals()
        return (audio_code, [('Content-type', 'text/xml')], xml)

    elif endpoint == 'block_onekey_verify':
        block_id = parameters.get('block_id', None)
        if not block_id: return bad_request('block_id must be set.')
        captcha_id = parameters.get('captcha_id', None)
        if not captcha_id: return bad_request('captcha_id must be set.')

        check_code, check_result = check_block_audio(block_id, captcha_id, 
            server_url=server_url)
        return (check_code, [('Content-type', 'text/xml')], check_result)

    elif endpoint == 'create_block':
        user_ip, user_agent = get_user_info(environ)
        block_code, block_html = create_block(user_ip, user_agent,
            api_credentials=api_credentials, server_url=server_url)
        return (block_code, [('Content-type', 'text/html')], block_html)

    elif endpoint == 'create_captcha_instance':
        block_id = parameters.get('block_id', None)
        if not block_id: return bad_request('block_id must be set.')
        display_style = parameters.get('display_style', None)
        include_audio = parameters.get('include_audio', None)

        visual_code, visual_html = create_instance(block_id, 
            display_style=display_style, include_audio_form=include_audio,
            server_url=server_url)
        if '410 Gone' in visual_html:
            return (410, [], "")
        else:
            return (visual_code, [('Content-type', 'text/html')], visual_html)

    elif endpoint == 'verify_block_captcha':
        block_id = parameters.get('block_id', None)
        if not block_id: return bad_request('block_id must be set.')
        captcha_id = parameters.get('captcha_id', None)
        if not captcha_id: return bad_request('captcha_id must be set.')
        code = parameters.get('code', None)
        if not code: return bad_request('code must be set.')

        check_code, check_result = check_instance(block_id, captcha_id, code,
            server_url=server_url)
        result = check_result.lower()
        return (check_code, [('Content-type', 'plain/text')], result)

    elif endpoint == 'check_credentials':
        check_code, check_result = make_request('check_credentials',
            api_credentials, server_url=url)
        return (check_code, [('Content-type', 'text/html')], check_result)

    elif endpoint == 'callback_check':
        return (200, [('Content-type', 'text/html')], CALLBACK_OK)

    elif not endpoint:
        return bad_request('endpoint must be set.')
    else:
        return bad_request("Unknown endpoint '%s'"% endpoint)


def create_captcha(user_ip, user_agent, captcha_length=None, width=None,
    height=None, image_code_color=None, display_style=None,
    api_credentials=None, server_url=None):
    '''Create a single visual CAPTCHA, returning HTTP code and content string.

    Not all combinations of captcha_length, width, and height are valid.  There
    are a limited number of categories, and if a captcha is "too easy" it will
    be rejected.  In the future, this may be taken as a minimal value, and the
    actual visual CAPTCHA may be larger for end users with a larger risk profile.

    Keyword arguments:
    captcha_length - Optional number of images to select, defaults to 3
    width - Optional grid width, defaults to 3
    height - Optional grid height, defaults to 4
    image_code_color - Optional code color, defaults to White, one of 
        White, Red, Orange, Yellow, Green, Teal, Blue, Indigo, Violet, Gray
    display_style - Optional style 'flyout' (default) or 'lightbox'
    api_credentials - An optional dictionary containing API credentials and settings
    server_url - An optional override of the server url
    '''

    creds = api_credentials or captchalib_config.api_credentials
    params = creds.copy()
    params['ip_addr'] = user_ip
    params['user_agent'] = user_agent
    if captcha_length: params['captcha_length'] = captcha_length
    if width: params['width'] = width
    if height: params['height'] = height
    if image_code_color: params['image_code_color'] = image_code_color
    if display_style: params['display_style'] = display_style

    return make_request('captcha', params, server_url=server_url)


def check_captcha(captcha_id, code, api_credentials=None, server_url=None):
    '''Check a visual CAPTCHA, returning code and content string

    Keyword arguments:
    captcha_id - The captcha ID included in create_captcha's return
    code - The code guessed by the user
    api_credentials - An optional dictionary containing API credentials and settings
    server_url - An optional override of the server url
    '''

    creds = api_credentials or captchalib_config.api_credentials
    params = creds.copy()
    params['code'] = code
    resource = 'captcha/%s'%(captcha_id)
    return make_request(resource, params, server_url=server_url);


def start_onekey(phone_number, api_credentials=None, server_url=None):
    '''Start a single audio CAPTCHA, returning HTTP code and content string.

    Keyword arguments:
    phone_number - The phone number provided by the user
    api_credentials - An optional dictionary containing API credentials and settings
    server_url - An optional override of the server url
    '''

    creds = api_credentials or captchalib_config.api_credentials
    params = creds.copy()
    params['phone_number'] = phone_number
    return make_request('onekey', params, server_url=server_url)


def check_onekey(onekey_id, api_credentials=None, server_url=None):
    '''Check a single audio CAPTCHA, returning HTTP code and content string.

    Keyword arguments:
    onekey_id - The audio ID included in start_onekey's return
    api_credentials - An optional dictionary containing API credentials and settings
    server_url - An optional override of the server url
    '''
    creds = api_credentials or captchalib_config.api_credentials
    params = creds.copy()
    resource = 'onekey/%s'%(onekey_id)
    return make_request(resource, params, server_url=server_url);


def check_config(api_credentials=None, server_url=None):
    '''Check the local and remote configuration, returning boolean (True = OK) and HTML string.

    Keyword arguments:
    api_credentials - A dictionary containing API credentials and settings

    Return: A tuple of:
     * boolean, True if config checks OK, False if failed.
     * string, HTML describing the checks and any failures.
    '''

    api_credentials = api_credentials or captchalib_config.api_credentials
    url = server_url or captchalib_config.captcha_server_url

    local_config = [("Item", "Value", "Required Value", "Acceptable?")]

    # Python version 2.x (not 3.x)
    try:
        version = sys.version_info
        python_version = "%d.%d.%d" % version[0:3]
        python_supported = (version[0] == 2) and 'Yes' or 'No'
    except:
        python_version = 'Before 2.0'
        python_supported = 'No'
    local_config.append(('Python version', python_version, "2.x series", python_supported))

    # Check captcha_server_url
    not_set = '(NOT SET)'
    expected_url = 'http://captcha.confidenttechnologies.com/'
    if url == expected_url:
        url_supported = 'Yes'
    elif url.startswith('http') and url.endswith('/'):
        url_supported = 'Maybe'
    else:
        url_supported = 'No'
    local_config.append(('captcha_server_url', url, expected_url, url_supported))

    # Check API parameters
    customer_id = api_credentials.get('customer_id', not_set)
    customer_id_ok = (customer_id and customer_id != not_set) and 'Yes' or 'No'
    local_config.append(('customer_id', customer_id, '(some value)', customer_id_ok))

    site_id = api_credentials.get('site_id', not_set)
    site_id_ok = (site_id and site_id != not_set) and 'Yes' or 'No'
    local_config.append(('site_id', site_id, '(some value)', customer_id_ok))

    api_username = api_credentials.get('api_username', not_set)
    api_username_ok = (api_username and api_username != not_set) and 'Yes' or 'No'
    local_config.append(('api_username', api_username, '(some value)', api_username_ok))

    api_password = api_credentials.get('api_password', not_set)
    api_password_ok = (api_password and api_password != not_set) and 'Yes' or 'No'
    local_config.append(('api_password', api_password, '(some value)', api_password_ok))

    display_style = api_credentials.get('display_style', not_set)
    display_style_ok = (display_style.lower() in \
        [not_set.lower(), 'flyout', 'lightbox']) and 'Yes' or 'No'
    local_config.append(('display_style', display_style, '"flyout", "lightbox", or not set (flyout)', display_style_ok))

    display_style = api_credentials.get('display_style', not_set)
    display_style_ok = (display_style.lower() in \
        [not_set.lower(), 'flyout', 'lightbox']) and 'Yes' or 'No'
    local_config.append(('display_style', display_style, '"flyout", "lightbox", or not set (flyout)', display_style_ok))

    callback_url = captchalib_config.callback_url
    callback_ok = (callback_url and not callback_url.startswith('/')) \
        and 'Yes' or 'No'
    local_config.append(('callback_url', callback_url, "(Local URL, doesn't start with /)", callback_ok))

    # Make local tables
    local = "<h1>Local Settings</h1>\n<table border='1'>\n<tr><th>"
    local += "</th><th>".join(local_config[0]) + "</th></tr>\n"
    local_ok = True
    for row in local_config[1:]:
        local += '<tr><td>' + '</td><td>'.join(row) + '</td></tr>\n'
        if row[-1] == 'No': local_ok = False
    local += '</table>'

    # Add callback check button
    # TODO: Use javascript to check
    local += '''<br/>
        <form name='callback_check' action='%s' method='post'>
        <input type='hidden' name='endpoint' value='callback_check' />
        <input type='submit' value='Click to check the callback' />
    </form>
    <p>
    Response to clicking above should be '%s'.
    </p>
    ''' % (callback_url, CALLBACK_OK)

    api = "<h1>API Settings</h1>"
    api_status, api_table = make_request('check_credentials', api_credentials,
        server_url=url)
    if (api_status != 200):
        api_ok = False
        api += "Error %d generated when checking credentials on %s\n" % (api_status, url)
        api += '<hr />\n'
        api += api_table
        api += '<hr />\n'
    else:
        api += api_table
        api_ok = "api_failed='True'" not in api_table

    return local_ok and api_ok, local + api

# vi: expandtab tabstop=4 shiftwidth=4
