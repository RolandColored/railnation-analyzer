#!/usr/bin/env python
# -*- coding:  utf-8 -*-

import time
import json
import hashlib
import logging

import requests
import requests.exceptions

CLIENT_CHECKSUM = -1
MAX_RECONNECT = 2


def _quote(item):
    """
    Explicit quotation and spacing to ensure correct md5 sum calculation.

    :param item: object
    :type item: str or dict or list of bool or int
    :return: accurately quoted and spaced json
    :rtype: str
    """
    if isinstance(item, list):
        return '[' + ','.join([_quote(i) for i in item]) + ']'
    elif isinstance(item, dict):
        return '{' + ','.join([_quote(k) + ':' + _quote(v)
                               for k, v in item.items()]) + '}'
    elif isinstance(item, str):
        return '"' + item + '"'
    else:
        return str(item).lower()


def _make_hash(item):
    return hashlib.md5(_quote(item).encode("utf-8")).hexdigest()


class ServerCaller:
    def __init__(self, server_url, session_id):
        self.log = logging.getLogger('ServerCaller')
        self.log.debug('Initialization...')
        self.api_url = 'https://%s/web/rpc/flash.php' % server_url

        self.session = requests.Session()
        self.session.headers.update({
            'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4)'
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
        })
        self.session.cookies.update({'PHPSESSID': session_id})

    def call(self, interface_name, method_name, data=None, short_call=205):
        """
        Actual server query.

        Construct URL from base_url + url params "interface" & "method".
        And POST data in json format there.

        In case of an error - retry MAX_RECONNECT times before die.

        :type interface_name: str
        :type method_name: str
        :type data: list
        :param short_call: int
        :return: server response as dict object (parsed from json)
        :rtype: dict
        """
        if data is None:
            data = []
        assert self.session is not None
        assert isinstance(interface_name, str)
        assert isinstance(method_name, str)
        assert isinstance(data, list)

        self.log.debug('Requesting: %s %s' % (interface_name, method_name))
        self.log.debug('Data: %s' % data)

        target = {'interface': interface_name,
                  'method': method_name,
                  'shortCall': short_call}
        payload = {'ckecksum': CLIENT_CHECKSUM,
                   'client': 1,
                   'hash': _make_hash(data),
                   'parameters': data}

        retry_count = 0
        while retry_count < MAX_RECONNECT:
            retry_count += 1
            try:
                r = self.session.post(self.api_url,
                                      params=target,
                                      data=json.dumps(payload))

            except requests.exceptions.ConnectionError as err:
                self.log.error('Connection to %s resulted in error: %s' % (self.api_url,
                                                                           str(err)))
                time.sleep(0.25)

            except requests.exceptions.Timeout as err:
                self.log.error('Connection to %s timeout: %s' % (self.api_url,
                                                                 str(err)))
                pass

            else:
                result = r.json()
                self.log.debug('Got response: %s' % result)
                return result

        self.log.critical('Too many connection failures (%s)' % retry_count)
        raise Exception('Too many connection failures (%s)' % retry_count)
