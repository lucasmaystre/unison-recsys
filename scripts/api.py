#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import ast
import base64
import requests
import requests.auth


DEFAULT_MAIL = 'a@gs.com'
DEFAULT_PASSWORD = 'h3ll0'


class UnisonGetter:

    URL_FORMAT = "http://api.unison.local%s"

    def __init__(self, mail, password):
        mail = base64.b64encode(mail)
        password = base64.b64encode(password)
        self.auth = requests.auth.HTTPBasicAuth(mail, password)

    def __getattr__(self, name):
        getter = getattr(requests, name)
        def wrapper(path, data=None):
            url = self.URL_FORMAT % path
            res = getter(url, data=data, auth=self.auth)
            print "method: %s" % name.upper()
            print "URL:    %s" % url
            print "data:   %s" % str(data)
            print "status: %s" % res.status_code
            print
            print res.text
        return wrapper


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mail', '-m', default=DEFAULT_MAIL)
    parser.add_argument('--password', '-p', default=DEFAULT_PASSWORD)
    parser.add_argument('--data', '-d', action='store_true', default=False)
    parser.add_argument('method', choices=['GET', 'POST', 'PUT', 'DELETE'])
    parser.add_argument('url')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    unison = UnisonGetter(args.mail, args.password)
    fct = getattr(unison, args.method.lower())
    if args.data:
        raw = raw_input('data: ')
        if raw != '':
            fct(args.url, data=ast.literal_eval(raw))
        else:
            fct(args.url)
    else:
        fct(args.url)
