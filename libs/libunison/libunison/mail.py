#!usr/bin/env python
import re

# Adapted from the Django project:
# http://code.djangoproject.com/svn/django/trunk/django/core/validators.py
EMAIL_RE = re.compile(
  # dot-atom
  r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
  # quoted-string, see also http://tools.ietf.org/html/rfc2822#section-3.2.5
  r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"'
  r')@((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$)'  # domain
  # literal form, ipv4 address (SMTP 4.1.3)
  r'|\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$',
  re.IGNORECASE
)

def is_valid(email):
    # Adapted from the Django project:
    # http://code.djangoproject.com/svn/django/trunk/django/core/validators.py
    parts = email.split(u'@')
    try:
        parts[-1] = parts[-1].encode('idna')
    except UnicodeError:
        return False
    email = u'@'.join(parts)
    if EMAIL_RE.search(email) is not None:
        return True
    return False
