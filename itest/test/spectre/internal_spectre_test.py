# -*- coding: utf-8 -*-
import json
import time

import pytest

from util import get_from_spectre
from util import get_through_spectre


@pytest.fixture(scope='module')
def wait_for_casper():
    """ Wait for casper and cassandra to be ready.

    It takes a bit for casper and cassandra to be ready to serve requests,
    while the tests usually start immediately without waiting.
    """
    for i in range(30):
        response = get_from_spectre('/status')
        if response.status_code == 200:
            return
        else:
            time.sleep(1)
    else:
        raise RuntimeError("Spectre was not ready after 30 seconds")


class TestCanReachStatuses(object):

    def test_can_reach_casper_status(self, wait_for_casper):
        response = get_through_spectre('/status')
        assert response.status_code == 200
        assert response.text == 'Backend is alive\n'

        response = get_from_spectre('/status')
        assert response.status_code == 200
        status = json.loads(response.text)
        assert status['cassandra_status'] == 'up'
        assert status['smartstack_configs'] == 'present'
        assert status['spectre_configs'] == 'present'
        assert status['proxied_services'] == {
            'backend.main': {
                'host':'10.5.0.3',
                'port': 9080,
            },
        }


class TestConfigs(object):

    def test_can_get_casper_configs(self, wait_for_casper):
        response = get_from_spectre('/configs')
        assert response.status_code == 200
        status = json.loads(response.text)
        # status['service_configs'] is too long and changes too quickly
        # to be worth asserting its entire content
        assert 'long_ttl' in status['service_configs']['backend.main']['cached_endpoints']
        assert status['service_configs']['backend.main']['uncacheable_headers'] == ['Uncacheable-Header']
        assert status['service_configs']['backend.main']['vary_headers'] == ['Accept-Encoding']
        # status['smartstack_configs'] should only contain enabled services
        assert status['smartstack_configs'] == {
            u'backend.main': {u'host': u'10.5.0.3', u'port': 9080},
        }
        # services.yaml, backend.main.yaml and casper.internal.yaml
        assert len(status['mod_time_table']) == 3
        assert isinstance(status['worker_id'], int)
