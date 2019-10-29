import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *
''' IMPORTS '''

import json
import requests
from distutils.util import strtobool
from urllib.parse import urlencode

# Disable insecure warnings
requests.packages.urllib3.disable_warnings()

''' GLOBALS/PARAMS '''

CLIENT_ID = demisto.params().get('client_id')
CLIENT_SECRET = demisto.params().get('client_secret')
# Remove trailing slash to prevent wrong URL path to service
# SERVER = f"https://login.microsoftonline.com/{demisto.params().get('tenant_id')}"
# Should we use SSL
USE_SSL = not demisto.params().get('insecure', False)
# How many time before the first fetch to retrieve incidents
FETCH_TIME = demisto.params().get('fetch_time', '3 days')
# Service base URL
AUTH_URL = f"https://login.microsoftonline.com/{demisto.params().get('tenant_id')}/oauth2/v2.0/token"

BASE_URL = 'https://graph.microsoft.com/v1.0'
SHARE_POINT_DOMAIN = demisto.params().get('share_point_domain')


# Headers to be sent in requests
HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
}

''' HELPER FUNCTIONS '''


def http_request(method, url, params=None, data=None, json=None, headers=None):
    # A wrapper for requests lib to send our requests and handle requests and responses better

    res = requests.request(
        method,
        url,
        verify=USE_SSL,
        params=params,
        data=data,
        json=json,
        headers=headers
    )
    # Handle error responses gracefully
    if res.status_code not in {200, 204, 201}:
        return_error('Error in API call to Example Integration [%d] - %s' % (res.status_code, res.reason))

    return res.json()


def item_to_incident(item):
    incident = {}
    # Incident Title
    incident['name'] = 'Example Incident: ' + item.get('name')
    # Incident occurrence time, usually item creation date in service
    incident['occurred'] = item.get('createdDate')
    # The raw response from the service, providing full info regarding the item
    incident['rawJSON'] = json.dumps(item)
    return incident


''' COMMANDS + REQUESTS FUNCTIONS '''


def get_api_token():
    res = http_request('POST', AUTH_URL, data=urlencode({
        'client_id': demisto.params().get('client_id'),
        'client_secret': demisto.params().get('client_secret'),
        'grant_type': 'client_credentials',
        'scope': 'https://graph.microsoft.com/.default'
    }), headers=HEADERS)
    try:
        access_token = res['access_token']
    except KeyError:
        demisto.error('could not get acceess token')
        raise
    else:
        return access_token


def test_module():
    """
    Performs basic get request to get item samples
    """
    samples = get_api_token()


def convert_site_name_to_site_id(site_name):
    url = BASE_URL + '/sites/' + SHARE_POINT_DOMAIN + f':/sites/{site_name}?'
    query_string = {"$select": "id"}
    access_token = get_api_token()  # TODO: put this in a class and access token will be an attribute
    if not access_token:
        return False  # TODO: return an error
    all_headers = HEADERS
    final_headers = {}
    final_headers['Authorization'] = f'Bearer {access_token}'
    res = http_request('GET', url, headers=final_headers, params=query_string)
    try:
        site_id = res['id']
    except KeyError:
        demisto.error('could not get site id')
    else:
        return site_id

def get_drive_id_for_site(site_id):
    access_token = get_api_token()  # TODO: put this in a class and access token will be an attribute

    headers = {'Authorization': f'Bearer {access_token}'}
    if not access_token:
        return False  # TODO: return an error
    url = BASE_URL + '/sites/' + site_id + '/drive'
    query_string = {"$select": "id"}

    res = http_request('GET', url, params=query_string, headers=headers)
    try:
        documents_id = res['id']
    except KeyError:
        demisto.error('could not get site id')
    else:
        return documents_id

def find_documents_folder_id(site_id):
    access_token = get_api_token()  # TODO: put this in a class and access token will be an attribute
    # see premissions - why can't  I find sites
    headers = {'Authorization': f'Bearer {access_token}'}
    if not access_token:
        return False  # TODO: return an error
    url = BASE_URL + '/sites/' + site_id + '/drive/root?'
    query_string = {"$select": "id"}

    res = http_request('GET', url, params=query_string, headers=headers)
    try:
        documents_id = res['id']
    except KeyError:
        demisto.error('could not get site id')
    else:
        return documents_id

def get_item_id_by_path(path, site_id):
    # site_id = convert_site_name_to_site_id(site_name)  # TODO comment out
    # TODO: path: need to add slash and back slash validation
    access_token = get_api_token()  # TODO: put this in a class and access token will be an attribute
    headers = {'Authorization': f'Bearer {access_token}'}
    query_string = {"$select": "id"}
    url = BASE_URL + f'/sites/{site_id}/drive/root:/{path}?'

    res = http_request('GET', url, params=query_string, headers=headers)
    try:
        item_id = res['id']
    except KeyError:
        raise # TODO: handle exception
    else:
        return item_id

def create_folder_command(folder_name, path, site_name):
    site_id = convert_site_name_to_site_id(site_name)  # TODO comment out
    access_token = get_api_token()  # TODO: put this in a class and access token will be an attribute
    headers = {'Authorization': f'Bearer {access_token}'}
    if path:
        item_id_to_create = get_item_id_by_path(path, site_id) # if empty default is documents
    else:
        item_id_to_create = find_documents_folder_id(site_id)

    payload = f"{{'name': '{folder_name}',  'folder': {{}},  '@microsoft.graph.conflictBehavior': 'rename'}}"
    url = BASE_URL + f'/sites/{site_id}/drive/items/{item_id_to_create}/children'
    res = http_request('POST', url, data=payload, headers=headers)


def delete_item_from_documents_command(path_to_item, site_id):
    item_id_to_delete = get_item_id_by_path(path_to_item, site_id)
    drive_id = get_drive_id_for_site(site_id)
    access_token = get_api_token()  # TODO: put this in a class and access token will be an attribute
    headers = {'Authorization': f'Bearer {access_token}'}

    url = BASE_URL + f'/drives/{drive_id}/items/{item_id_to_delete}'

    res = http_request('DELETE', url, headers=headers)  # TODO: add validation if it works


def upload_document_to_document_folder_command(file_name, entry_id, site_name=None):

    access_token = get_api_token()  # TODO: put this in a class and access token will be an attribute
    headers = {'Authorization': f'Bearer {access_token}'}

    # file_path = demisto.getFilePath(entry_id).get(‘path’) # TODO: change it to the file_path

    site_id = convert_site_name_to_site_id(site_name)
    documents_id = find_documents_folder_id(site_id)
    url = BASE_URL + f'/sites/{site_id}/drive/items/{documents_id}:/{file_name}:/content'

    with open(file_path, 'rb') as file:
        res = http_request('PUT', url, data=file, headers=headers)
    if res:
        pass  # TODO: add test for if the action was successful
    contents = []
    context = {}
    title = ''
    """
    upload a document to "Documents" folder. 
    :param name: file name
    :param entry_id: demisto_entry_id
    :site_name: default value is the main team's site. 
    :return: demisto.output
    """
    demisto.results({
        'Type': entryTypes['note'],
        'ContentsFormat': formats['json'],
        'Contents': contents,
        'ReadableContentsFormat': formats['markdown'],
        'HumanReadable': tableToMarkdown(title, contents, removeNull=True),
        'EntryContext': context
    })


def get_items_command():
    """
    Gets details about a items using IDs or some other filters
    """
    # Init main vars
    headers = []
    contents = []
    context = {}
    context_entries = []
    title = ''
    # Get arguments from user
    item_ids = argToList(demisto.args().get('item_ids', []))
    is_active = bool(strtobool(demisto.args().get('is_active', 'false')))
    limit = int(demisto.args().get('limit', 10))
    # Make request and get raw response
    items = get_items_request(item_ids, is_active)
    # Parse response into context & content entries
    if items:
        if limit:
            items = items[:limit]
        title = 'Example - Getting Items Details'

        for item in items:
            contents.append({
                'ID': item.get('id'),
                'Description': item.get('description'),
                'Name': item.get('name'),
                'Created Date': item.get('createdDate')
            })
            context_entries.append({
                'ID': item.get('id'),
                'Description': item.get('description'),
                'Name': item.get('name'),
                'CreatedDate': item.get('createdDate')
            })

        context['Example.Item(val.ID && val.ID === obj.ID)'] = context_entries

    demisto.results({
        'Type': entryTypes['note'],
        'ContentsFormat': formats['json'],
        'Contents': contents,
        'ReadableContentsFormat': formats['markdown'],
        'HumanReadable': tableToMarkdown(title, contents, removeNull=True),
        'EntryContext': context
    })


def get_items_request(item_ids, is_active):
    # The service endpoint to request from
    endpoint_url = 'items'
    # Dictionary of params for the request
    params = {
        'ids': item_ids,
        'isActive': is_active
    }
    # Send a request using our http_request wrapper
    response = http_request('GET', endpoint_url, params)
    # Check if response contains errors
    if response.get('errors'):
        return_error(response.get('errors'))
    # Check if response contains any data to parse
    if 'data' in response:
        return response.get('data')
    # If neither was found, return back empty results
    return {}


def fetch_incidents():
    last_run = demisto.getLastRun()
    # Get the last fetch time, if exists
    last_fetch = last_run.get('time')

    # Handle first time fetch, fetch incidents retroactively
    if last_fetch is None:
        last_fetch, _ = parse_date_range(FETCH_TIME, to_timestamp=True)

    incidents = []
    items = get_items_request()
    for item in items:
        incident = item_to_incident(item)
        incident_date = date_to_timestamp(incident['occurred'], '%Y-%m-%dT%H:%M:%S.%fZ')
        # Update last run and add incident if the incident is newer than last fetch
        if incident_date > last_fetch:
            last_fetch = incident_date
            incidents.append(incident)

    demisto.setLastRun({'time': last_fetch})
    demisto.incidents(incidents)


''' COMMANDS MANAGER / SWITCH PANEL '''

LOG('Command being called is %s' % (demisto.command()))

try:
    if demisto.command() == 'test-module':
        # This is the call made when pressing the integration test button.
        create_folder_command('gal_foldser', '', 'site_test2')        # test_module()
        demisto.results('ok')
    elif demisto.command() == 'fetch-incidents':
        # Set and define the fetch incidents command to run after activated via integration settings.
        fetch_incidents()
    elif demisto.command() == 'example-get-items':
        # An example command
        get_items_command()

# Log exceptions
except Exception as e:
    LOG(e.message)
    LOG.print_log()
    raise
