import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

import requests
import urllib3

urllib3.disable_warnings()

CONF_JSON_PATH = 'https://raw.githubusercontent.com/demisto/content/master/Tests/conf.json'

conf_json = requests.request('GET', CONF_JSON_PATH, verify=False).json()

skipped_test = conf_json.get('skipped_tests')
total_test_count = conf_json.get('tests')
demisto.results(skipped_test.len())
demisto.results(total_test_count.len())

# demisto.results(conf_json)
# skipped_test = conf_json.get('skipped_tests')
# total_test_count = conf_json.get('tests')
#
# data = [
#     {"name": "Skipped Tests", "data": [skipped_test]},
#     {"name": "Skipped Tests", "data": [total_test_count]}
# ]
data = [
    {'name': "2018-04-12", 'groups': [{'name': "a", 'data': [10]}, {'name': "b", 'data': [10]}]},
    {'name': "2018-04-10", 'groups': [{'name': "a", 'data': [3]}, {'name': "b", 'data': [12]}]}
]
demisto.results(json.dumps(data))

# demisto.executeCommand('')
