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
def get_data_from_conf():
    conf_json = requests.request('GET', CONF_JSON_PATH, verify=False).json()
    tests = conf_json.get('tests')
    skipped_tests = conf_json.get('skipped_tests')
    skipped_integrations = conf_json.get('skipped_integrations')
    return tests, skipped_tests, skipped_integrations


# Getting all integrations playbooks from latest id_set.json
def get_id_set():
    artifacts = demisto.executeCommand('circleci-get-latest-artifacts', {'branch': 'master', 'project': 'content'})
    for entry in artifacts:
        # demisto.results(json.dumps())
        artifact = entry.get('Contents')
        if 'id_set.json' in artifact.get('pretty_path'):
            id_set_url = artifact.get('url')
    id_set = requests.request('GET', id_set_url, verify=False).json()
    return id_set


def get_total_integrations_and_playbook():
    id_set = get_id_set()
    id_set_integrations = id_set.get('integrations')
    integrations_ids = [list(integration_obj.keys())[0] for integration_obj in id_set_integrations]
    integrations_names_set = (set(integrations_ids))

    id_set_playbooks = id_set.get('playbooks')
    playbook_ids = [list(integration_obj.keys())[0] for integration_obj in id_set_playbooks]
    playbook_ids_set = (set(playbook_ids))

    return integrations_names_set, playbook_ids_set

#
# # Removing integrations that are skipped in conf.json
# for integration in skipped_integrations:
#     if integration in integrations_names_set:
#         integrations_names_set.remove(integration)
#         skipped_integrations_count += 1


# skipped_integrations_count = 0
# skipped_playbook_count = 0


def count_skipped_tests_in_conf(tests_in_conf, skipped_integrations_in_conf, skipped_test_list):
    for entry in tests_in_conf:
        test_playbook = entry.get('playbookID')
        integrations = entry.get('integrations')
        if integrations:
            integrations_list = integrations if isinstance(integrations, list) else [integrations]

            # Removing from integration list integrations that have a skipped test in conf.json
            # if test_playbook in skipped_tests:
            #     for integration in integrations_list:
            #         if integration in integrations_names_set:
            #             integrations_names_set.remove(integration)
            #             skipped_integrations_count += 1

            # Removing from playbook list playbook with skipped integration in conf.json
            for integration in integrations_list:
                if integration in skipped_integrations_in_conf:
                    if test_playbook not in skipped_test_list:
                        skipped_test_list.append(test_playbook)


# for playbook in skipped_tests:
#     if playbook in playbook_ids_set:
#         playbook_ids_set.remove('playbook')
#         skipped_playbook_count += 1


all_integrations, all_playbooks = get_total_integrations_and_playbook()
# all_integrations_count = len(all_integrations)
all_playbooks_count = len(all_playbooks)
skipped_playbook_count = len()



tested_integrations = len(integrations_names_set)
# skipped_integrations_count = total_integrations_count - tested_integrations

# demisto.results(f'Total integrations: {total_integrations_count}')
# demisto.results(f'Tested integrations: {tested_integrations}')
# demisto.results(f'Skipped integrations: {skipped_integrations_count}')

# tested_playbooks = len(playbook_ids_set)
# # skipped_playbook_count = total_playbook_count - tested_playbooks

# demisto.results(f'Total playbooks: {total_playbook_count}')
# demisto.results(f'Tested playbooks: {tested_playbooks}')
# demisto.results(f'Skipped playbooks: {skipped_playbook_count}')

data = [
    {'name': "Integrations", 'groups': [{'name': "Skipped", 'data': [skipped_integrations_count]}, {'name': "Tested", 'data': [tested_integrations]}]},
    {'name': "2018-04-10", 'groups': [{'name': "a", 'data': [3]}, {'name': "b", 'data': [12]}]}
]
demisto.results(json.dumps(data))


import requests
import urllib3

urllib3.disable_warnings()

CONF_JSON_PATH = 'https://raw.githubusercontent.com/demisto/content/master/Tests/conf.json'

"""
LOGIC

"""
# Data from conf.json
conf_json = requests.request('GET', CONF_JSON_PATH, verify=False).json()
skipped_tests = conf_json.get('skipped_tests')
tests_in_conf = conf_json.get('tests')
skipped_integrations = conf_json.get('skipped_integrations')

# Getting all integrations playbooks from latest id_set.json
artifacts = demisto.executeCommand('circleci-get-latest-artifacts', {'branch': 'master', 'project': 'content'})
for entry in artifacts:
    # demisto.results(json.dumps())
    artifact = entry.get('Contents')
    if 'id_set.json' in artifact.get('pretty_path'):
        id_set_url = artifact.get('url')
id_set = requests.request('GET', id_set_url, verify=False).json()
id_set_integrations = id_set.get('integrations')
integrations_ids = [list(integration_obj.keys())[0] for integration_obj in id_set_integrations]
integrations_names_set = (set(integrations_ids))
total_integrations_count = len(integrations_names_set)
id_set_playbooks = id_set.get('playbooks')
playbook_ids = [list(integration_obj.keys())[0] for integration_obj in id_set_playbooks]
playbook_ids_set = (set(playbook_ids))
total_playbook_count = len(playbook_ids_set)
skipped_integrations_count = 0
skipped_playbook_count = 0

# Removing integrations that are skipped in conf.json
for integration in skipped_integrations:
    if integration in integrations_names_set:
        integrations_names_set.remove(integration)
        skipped_integrations_count += 1

#
for entry in tests_in_conf:
    test_playbook = entry.get('playbookID')
    integrations = entry.get('integrations')
    if integrations:
        integrations_list = integrations if isinstance(integrations, list) else [integrations]

        # Removing from integration list integrations that have a skipped test in conf.json
        if test_playbook in skipped_tests:
            for integration in integrations_list:
                if integration in integrations_names_set:
                    integrations_names_set.remove(integration)
                    skipped_integrations_count += 1

        # Removing from playbook list playbook with skipped integration in conf.json
        for integration in integrations_list:
            if integration in skipped_integrations:
                if test_playbook in playbook_ids_set:
                    playbook_ids_set.remove(test_playbook)
                    skipped_playbook_count += 1


for playbook in skipped_tests:
    if playbook in playbook_ids_set:
        playbook_ids_set.remove('playbook')
        skipped_playbook_count += 1


tested_integrations = len(integrations_names_set)
# skipped_integrations_count = total_integrations_count - tested_integrations

demisto.results(f'Total integrations: {total_integrations_count}')
demisto.results(f'Tested integrations: {tested_integrations}')
demisto.results(f'Skipped integrations: {skipped_integrations_count}')

tested_playbooks = len(playbook_ids_set)
# skipped_playbook_count = total_playbook_count - tested_playbooks

demisto.results(f'Total playbooks: {total_playbook_count}')
demisto.results(f'Tested playbooks: {tested_playbooks}')
demisto.results(f'Skipped playbooks: {skipped_playbook_count}')

data = [
    {'name': "Integrations", 'groups': [{'name': "Skipped", 'data': [skipped_integrations_count]}, {'name': "Tested", 'data': [tested_integrations]}]},
    {'name': "2018-04-10", 'groups': [{'name': "a", 'data': [3]}, {'name': "b", 'data': [12]}]}
]
demisto.results(json.dumps(data))

# demisto.executeCommand('')
