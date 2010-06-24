#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''Sample page showing Confident CAPTCHA

If this seems complicated, it is.  No one directly writes a web application in
CGI or WSGI anymore.  Instead, use a framework like Werzeug or Django.  See
http://wiki.python.org/moin/WebFrameworks for some alternatives.
'''

import cgi
import Cookie
import httplib

import captchalib
from captchalib_config import callback_url, include_audio


config_template = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Confident CAPTCHA</title>
    <meta http-equiv="content-type" 
        content="text/html;charset=utf-8" />
</head>
<body>
<p>
Welcome to the Confident CAPTCHA Python sample code.  The table below
details if your configuration is supported by Confident CAPTCHA.  Local settings
are set in <tt>captchalib_config.py</tt>, and remote settings come from
<a href="http://captcha.confidenttechnologies.com/">captcha.confidenttechnologies.com</a>.
</p>
%(config_body)s
<p>
Your configuration is %(supported)s supported by the Confident CAPTCHA Python
sample code. %(instructions)s
</p>
<p>
There are two CAPTCHA configurations available:
</p>
<ul>
  <li><a href="single">Single CAPTCHA Method</a> - One CAPTCHA attempt, checked at form submit</li>
  <li><a href="multiple">Multiple CAPTCHA Method</a> - Multiple CAPTCHA attempts, checked at CAPTCHA completion</li>
</ul>
</body>
</html>
"""


def root_GET(environ, start_response):
    '''Response to GET /'''

    config_status, config_body = captchalib.check_config()
    if config_status:
        supported = ''
        instructions = 'Use this <tt>captchalib_config.py</tt> in your own project.'
    else:
        supported = '<b>not</b>'
        instructions = 'Please fix the errors before trying the samples and integrating into your own project.'

    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    html = config_template % locals()

    start_response(status, headers)
    return html.encode('utf-8')


single_template = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Confident CAPTCHA Demonstration - Single Method</title>
    <meta http-equiv="content-type" 
        content="text/html;charset=utf-8" />
</head>

<body>
<script type='text/javascript' src='http://code.jquery.com/jquery-1.4.2.min.js'></script>
<p>
This is a sample page for the single method of Confident CAPTCHA.
If this were a real page, then this would be part of a form, such as a sign-up
form, a blog comment form, or some other page where you want to prove that the
user is human before allowing them access.
</p>
<p>
When you solve the CAPTCHA below, nothing will happen until you submit the
form.  At that point, the CAPTCHA will be checked.
</p>
<p>
Things to try:
</p>
<ol>
  <li>Solve the CAPTCHA, then Submit</li>
  <li>Fail the CAPTCHA, then Submit</li>
</ol>

<form method='POST'>
    %(captcha_body)s
    <input type='submit' name='submit' value='Submit' />
</form>

<p>
%(verify_body)s
</p>

</body>
</html>
"""

def single_GET(environ, start_response):
    '''Response to GET /single'''

    user_ip, user_agent = captchalib.get_user_info(environ)
    captcha_status, captcha_body = captchalib.create_captcha(user_ip, user_agent)

    # Verbose error handling.  In your application, you may want to disable
    #  CAPTCHA instead, or add a fallback CAPTCHA.
    if (captcha_status != 200):
        captcha_body = ("<b>Server returned error %d on create_captcha:</b>" %
            captcha_status) + captcha_body

    html_params = {
        'captcha_body': captcha_body,
        'verify_body': 'Solve the CAPTCHA above, then click Submit.',
    }

    status = '200 OK'
    headers = [
        ('Content-type', 'text/html; charset=utf-8'),
    ]
    html = single_template % html_params

    start_response(status, headers)
    return html.encode('utf-8')


def single_POST(environ, start_response):
    '''Response to POST /single'''

    # Handle old CAPTCHA
    form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    code = form.getfirst('confidentcaptcha_code')
    captcha_id = form.getfirst('confidentcaptcha_captcha_id')
    check_status, check_body = captchalib.check_captcha(captcha_id, code)

    if check_body == 'True':
        verify_body = "CAPTCHA solution was correct.  Click above to try another, or go back to the <a href='.'>config check</a>."
    else:
        verify_body = "CAPTCHA solution was incorrect.  Click above to try another, or go back to the <a href='.'>config check</a>."

    # Create next CAPTCHA
    user_ip, user_agent = captchalib.get_user_info(environ)
    captcha_status, captcha_body = captchalib.create_captcha(user_ip, user_agent)

    # Verbose error handling.  In your application, you may want to disable
    #  CAPTCHA instead, or add a fallback CAPTCHA.
    if (captcha_status != 200):
        captcha_body = ("<b>Server returned error %d on create_captcha:</b>" %
            captcha_status) + captcha_body

    html_params = {
        'captcha_body': captcha_body,
        'verify_body': verify_body,
    }
    status = '200 OK'
    headers = [('Content-type', 'text/html; charset=utf-8')]
    html = single_template % html_params

    start_response(status, headers)
    return html.encode('utf-8')


multiple_template = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Confident CAPTCHA Demonstration - Multiple Method</title>
    <meta http-equiv="content-type" 
        content="text/html;charset=utf-8" />
</head>

<body>

<script type='text/javascript'>
    var CONFIDENTCAPTCHA_CALLBACK_URL = '%(callback_url)s'
    var CONFIDENTCAPTCHA_INCLUDE_AUDIO = %(audio_bool)s
</script>
<script type='text/javascript' src='http://code.jquery.com/jquery-1.4.2.min.js'></script>

<p>
This is a sample page for the multiple method of Confident CAPTCHA.
If this were a real page, then this would be part of a form, such as a sign-up
form, a blog comment form, or some other page where you want to prove that the
user is human before allowing them access.
</p>
<p>
When you solve the CAPTCHA below, it will immediately confirm if the CAPTCHA
is correct.  The result will be stored in the server-side session data store.
When you then submit the form, this data store will be checked to see what the
result was.
</p>
<p>
Things to try:
</p>
<ol>
  <li>Solve the CAPTCHA, then Submit</li>
  <li>Fail the CAPTCHA, then Submit</li>
  <li>Fail the CAPTCHA, then solve the second CAPTCHA, then Submit</li>
  <li>Fail the CAPTCHA three times</li>
</ol>

<form method='POST'>
    %(captcha_body)s
    <input type='submit' name='submit' value='Submit' />
</form>

<p>
%(verify_body)s
</p>

</body>
</html>
"""


def multiple_get_header(state = 'not_attempted'):
    '''Get a header string that sets the authentication state.

    Instead of a true server-side session, which would require a database or a
    more capable server, a cookie is used to store the CAPTCHA state.

    In a real application, use the framework's server-side session to store
    this data.  Don't store the state in a cookie.
    '''
    c = Cookie.SimpleCookie()
    c['captcha_state'] = state
    k, v = c.output().split(':',1)
    return (k.strip(),v.strip())


def multiple_get_state(environ):
    '''Read the authentication state from the headers

    Instead of a true server-side session, which would require a database or a
    more capable server, a cookie is used to store the CAPTCHA state.

    In a real application, use the framework's server-side session to store
    this data.  Don't trust state in a cookie sent from the user's browser.
    '''
    cookies = environ.get('HTTP_COOKIE',None)
    if cookies:
        for pair in cookies.split(';'):
            key, val = pair.split('=',1)
            if key.strip() == 'captcha_state':
                return val.strip()
    return 'not_attempted'


def multiple_create_captcha(environ):
    '''Return a status code and HTML fragment for a multiple captcha'''

    user_ip, user_agent = captchalib.get_user_info(environ)
    block_status, block_id = captchalib.create_block(user_ip, user_agent)

    # Verbose error handling.  In your application, you may want to disable
    #  CAPTCHA instead, or add a fallback CAPTCHA.
    if (block_status != 200):
        body = ("<b>Server returned error %d on create_block:</b>" %
            block_status) + block_id
        return block_status, body
    else:
        captcha_status, captcha_body = captchalib.create_instance(block_id,
            include_audio_form=include_audio)

        # Verbose error handling.  In your application, you may want to disable
        #  CAPTCHA instead, or add a fallback CAPTCHA.
        if (captcha_status != 200):
            body = ("<b>Server returned error %d on create_instance:</b>"
                % captcha_status) + captcha_body
            return captcha_status, body
        else:
            return captcha_status, captcha_body


def multiple_GET(environ, start_response):
    '''Response to GET /multiple'''

    captcha_status, captcha_body = multiple_create_captcha(environ)
    html_params = {
        'callback_url': callback_url,
        'audio_bool': include_audio and 'true' or 'false',
        'captcha_body': captcha_body,
        'verify_body': '''\
Solve the CAPTCHA above.  After solving, it will tell you if you passed or failed.
<br/>Then, click the Submit button to post and run the local server check.''',
    }

    status = '200 OK'
    headers = [
        ('Content-type', 'text/html; charset=utf-8'),
        multiple_get_header(),
    ]
    html = multiple_template % html_params

    start_response(status, headers)
    return html.encode('utf-8')


def multiple_POST(environ, start_response):
    '''Response to POST /multiple'''

    # Handle old CAPTCHA
    form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    code = form.getfirst('confidentcaptcha_code')
    captcha_id = form.getfirst('confidentcaptcha_captcha_id')
    old_block_id = form.getfirst('confidentcaptcha_block_id')
    old_block_passed = multiple_get_state(environ)

    if old_block_passed == 'not_attempted':
        # callback was not used - check the code
        check_status, check_body = captchalib.check_instance(old_block_id, captcha_id, code)
    else:
        # callback was used
        check_body = (old_block_passed == 'passed') and 'True' or 'False'

    if check_body == 'True':
        verify_body = "CAPTCHA solution was correct.  Click above to try another, or go back to the <a href='.'>config check</a>."
    else:
        verify_body = "CAPTCHA solution was incorrect.  Click above to try another, or go back to the <a href='.'>config check</a>."

    # Create next CAPTCHA
    captcha_status, captcha_body = multiple_create_captcha(environ)
    html_params = {
        'callback_url': callback_url,
        'audio_bool': include_audio and 'true' or 'false',
        'captcha_body': captcha_body,
        'verify_body': verify_body,
    }
    status = '200 OK'
    headers = [
        ('Content-type', 'text/html; charset=utf-8'),
        multiple_get_header(),
    ]
    html = multiple_template % html_params

    start_response(status, headers)
    return html.encode('utf-8')


def multiple_callback_POST(environ, start_response):
    '''Response to config.callback_url'''

    form = cgi.FieldStorage(fp=environ['wsgi.input'], environ=environ)
    params = dict([(key, form.getfirst(key)) for key in form.keys()])
    endpoint = params.get('endpoint', None)
    block_id = params.get('block_id', None)
    status, headers, body = captchalib.callback(environ, params)
    state = multiple_get_state(environ)
    if endpoint in ['block_onekey_verify', 'verify_block_captcha']:
        state = (body == 'true') and 'passed' or 'failed'
    headers.append(multiple_get_header(state))

    if type(status) is int:
        try:
            text = httplib.responses[status]
        except AttributeError:
            # httplib.response is Python 2.5 feature
            responses = {200:'OK', 400:'Bad Request', 404:'Not Found',
                410:'Gone', 500:'Server Error'}
            text = responses.get(status, 'Unknown')
        status = "%d %s"%(status, text)
    start_response(status, headers)
    return body.encode('utf-8')


def captcha_app(environ, start_response):
    '''WGSI application serving the CAPTCHA sample page'''
    method = environ.get('REQUEST_METHOD','GET')
    path = environ.get('PATH_INFO', '/')

    # Config check page
    if method == 'GET' and path == '/':
        return root_GET(environ, start_response)
    elif method == 'GET' and path in ('/favicon.ico', '/robots.txt'):
        start_response('404 Not Found', [])
        return ""
    # Single CAPTCHA method
    elif method == 'GET' and path == '/single':
        return single_GET(environ, start_response)
    elif method == 'POST' and path == '/single':
        return single_POST(environ, start_response)
    # Multiple CAPTCHA method
    elif method == 'GET' and path == '/multiple':
        return multiple_GET(environ, start_response)
    elif method == 'POST' and path == '/multiple':
        return multiple_POST(environ, start_response)
    elif method == 'POST' and path == ('/' + callback_url):
        return multiple_callback_POST(environ, start_response)
    else:
        base = environ.get('SCRIPT_NAME', '')
        start_response('303 See Other', [('Location', base + '/')])
        return "Invalid page requested.  Redirecting to /"


if __name__ == '__main__':
    import threading
    import webbrowser
    from wsgiref.simple_server import make_server

    # Open a webbrowser after a 1 second delay
    def open_browser():
        print "Opening webbrowser at http://localhost:8001 ..."
        webbrowser.open('http://localhost:8001')
    t = threading.Timer(1.0, open_browser)
    t.start()

    httpd = make_server('', 8001, captcha_app)
    print "Serving on port 8001.  Interrupt (Ctrl-C) to quit."
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print "\nDone."
        pass
