import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

import requests
import urllib3

urllib3.disable_warnings()

CONF_JSON_PATH = 'https://raw.githubusercontent.com/demisto/content/master/Tests/conf.json'

"""
LOGIC

"""
# Data from conf.json
conf_json = requests.request('GET', CONF_JSON_PATH, verify=False).json()
skipped_test = conf_json.get('skipped_tests')
tests_in_conf = conf_json.get('tests')
skipped_integrations = conf_json.get('skipped_integrations')

# Getting all integrations from latest id_set.json
artifacts = demisto.executeCommand('circleci-get-latest-artifacts', {'branch': 'master', 'project': 'content'})
for entry in artifacts:
    # demisto.results(json.dumps())
    artifact = entry.get('Contents')
    if 'id_set.json' in artifact.get('pretty_path'):
        id_set_url = artifact.get('url')
id_set = requests.request('GET', id_set_url, verify=False).json()
id_set_integrations = id_set.get('integrations')
integrations_names = [list(integration_obj.keys())[0] for integration_obj in id_set_integrations]
integrations_names_set = (set(integrations_names))


demisto.results(f'All integrations count: {len(integrations_names_set)}')

# Removing integrations that are skipped in conf.json
for integration in skipped_integrations:
    if integration != '_comment':
        integrations_names_set.remove(integration)

# Removing integrations that have a skipped test conf.json
for entry in tests_in_conf:
    test_playbook = entry.get('playbookID')
    integrations = entry.get('integrations')
    if integrations:
        integrations_list = integrations if isinstance(integrations, list) else [integrations]
        if test_playbook in skipped_test:
            for integration in integrations_list:
                integrations_names_set.remove(integration)

demisto.results(f'All integrations count: {len(integrations_names_set)}')

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
