#!/usr/bin/env python
"""WSGI handler for Unison's REST API.

Tiny wrapper around Flask to add the proper paths to PYTONPATH. The virtual
environment setup is already done by mod_wsgi (see Apache config).
"""

import sys


def application(environ, start_response):
    """Handle a request.

    Expects the UNISON_ROOT environment variable to be properly set by Apache.
    """
    sys.path.insert(0, '%s/www/api/unison' % environ['UNISON_ROOT'])
    from unison import app
    return app(environ, start_response)
