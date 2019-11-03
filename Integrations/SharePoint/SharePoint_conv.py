import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

from Scripts.CommonServerPython.CommonServerPython import *


''' IMPORTS '''

import json
import requests
from distutils.util import strtobool
from urllib.parse import urlencode
import datetime


# Disable insecure warnings
requests.packages.urllib3.disable_warnings()

''' GLOBALS/PARAMS '''


# Service base URL



# Headers to be sent in requests
SITE_ID = 'Demistodev.sharepoint.com,142d3744-cd7e-4f4c-bbe9-f3dae7ebdc83,9e632eea-5727-4232-b68a-ecd4b9a460d4'
# TODO: this is only for debugging. remove it when test it in demisto.
BASE_URL = 'https://graph.microsoft.com/v1.0'
GRANT_TYPE = 'client_credentials'
SCOPE = 'https://graph.microsoft.com/.default'
INTEGRATION_NAME = 'SharePoint'
HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
}


class Client(BaseClient):
    """
    Client will implement the service API, should not contain Demisto logic.
    Should do requests and return data
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client_id = demisto.params().get('client_id')  # TODO: remove to const
        self.client_secret = demisto.params().get('client_secret')  # TODO: remove to const
        self.auto_url = f"https://login.microsoftonline.com/{demisto.params().get('tenant_id')}/oauth2/v2.0/token"  # TODO: remove to const
        self.tenant_domain = demisto.params().get('share_point_domain')
        self.access_token = self.get_api_token()
        self.headers = {'Authorization': f'Bearer {self.access_token}'}  # TODO: remove to const



    def _http_request(self, method, url, params=None, data=None, json=None, headers=None):
        # A wrapper for requests lib to send our requests and handle requests and responses better

        res = requests.request(
            method,
            url,
            verify=self._verify,
            params=params,
            data=data,
            json=json,
            headers=headers
        )
        if res.status_code == 401:
            self.get_api_token()

        # Handle error responses gracefully
        if res.status_code not in {200, 204, 201}:
            return_error('Error in API call to Example Integration [%d] - %s' % (res.status_code, res.reason))

        return res.json()

    def list_incidents(self):
        # """
        # returns dummy incident data, just for the example.
        # """
        # return [
        #     {
        #         'incident_id': 1,
        #         'description': 'Hello incident 1',
        #         'created_time': datetime.utcnow().strftime(DATE_FORMAT)
        #     },
        #     {
        #         'incident_id': 2,
        #         'description': 'Hello incident 2',
        #         'created_time': datetime.utcnow().strftime(DATE_FORMAT)
        #     }
        # ]
        pass

    def get_api_token(self):
        res = self._http_request('POST', self.auto_url, data=urlencode({
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': GRANT_TYPE,
            'scope': SCOPE
        }), headers=HEADERS)
        try:
            access_token = res['access_token']
        except KeyError:
            return_error('could not get access token')
            raise
        else:
            self.access_token = access_token

    def get_items_request(self, item_ids, is_active):
        # # The service endpoint to request from
    #         # endpoint_url = 'items'
    #         # # Dictionary of params for the request
    #         # params = {
    #         #     'ids': item_ids,
    #         #     'isActive': is_active
    #         # }
    #         # # Send a request using our http_request wrapper
    #         # response = self._http_request('GET', endpoint_url, params)
    #         # # Check if response contains errors
    #         # if response.get('errors'):
    #         #     return_error(response.get('errors'))
    #         # # Check if response contains any data to parse
    #         # if 'data' in response:
    #         #     return response.get('data')
    #         # # If neither was found, return back empty results
    #         # return {}
        pass

    def convert_site_name_to_site_id(self, site_name):
        url = BASE_URL + '/sites/' + self.tenant_domain + f':/sites/{site_name}?'
        query_string = {"$select": "id"}
        access_token = self.get_api_token()  # TODO: put this in a class and access token will be an attribute
        if not access_token:
            return False  # TODO: return an error
        final_headers = {}
        final_headers['Authorization'] = f'Bearer {access_token}'
        res = self._http_request('GET', url, headers=final_headers, params=query_string)
        try:
            site_id = res['id']
        except KeyError:
            demisto.error('could not get site id')
        else:
            return site_id

    def get_drive_id_for_site(self, site_id):
        access_token = self.get_api_token()  # TODO: put this in a class and access token will be an attribute

        headers = {'Authorization': f'Bearer {access_token}'}
        if not access_token:
            return False  # TODO: return an error
        url = BASE_URL + '/sites/' + site_id + '/drive'
        query_string = {"$select": "id"}

        res = self._http_request('GET', url, params=query_string, headers=headers)
        try:
            documents_id = res['id']
        except KeyError:
            demisto.error('could not get site id')
        else:
            return documents_id

    def find_documents_folder_id(self, site_id):
        access_token = self.get_api_token()  # TODO: put this in a class and access token will be an attribute
        # see premissions - why can't  I find sites
        headers = {'Authorization': f'Bearer {access_token}'}
        if not access_token:
            return False  # TODO: return an error
        url = BASE_URL + '/sites/' + site_id + '/drive/root?'
        query_string = {"$select": "id"}

        res = self._self._http_request('GET', url, params=query_string, headers=headers)
        try:
            documents_id = res['id']
        except KeyError:
            demisto.error('could not get site id')
        else:
            return documents_id

    def get_item_id_by_path(self, path, site_id):
        # site_id = convert_site_name_to_site_id(site_name)  # TODO comment out
        # TODO: path: need to add slash and back slash validation
        access_token = self.get_api_token()  # TODO: put this in a class and access token will be an attribute
        headers = {'Authorization': f'Bearer {access_token}'}
        query_string = {"$select": "id"}
        url = BASE_URL + f'/sites/{site_id}/drive/root:/{path}?'

        res = self._http_request('GET', url, params=query_string, headers=headers)
        try:
            item_id = res['id']
        except KeyError:
            raise  # TODO: handle exception
        else:
            return item_id

    def upload_document_to_document_folder(self, file_name, entry_id, site_name=None):
        """
        upload a document to "Documents" folder.
        :param name: file name
        :param entry_id: demisto_entry_id, an ID of an uploaded document
        :site_name: default value is the main team's site.
        :return: demisto.output
        """
        file_path = r'/Users/gberger/Desktop/Untitled.docx'



        # file_path = demisto.getFilePath(entry_id).get(‘path’) # TODO: change it to the file_path

        site_id = self.convert_site_name_to_site_id(site_name)
        documents_id = self.find_documents_folder_id(site_id)
        url = BASE_URL + f'/sites/{site_id}/drive/items/{documents_id}:/{file_name}:/content'

        with open(file_path, 'rb') as file:
            return self._http_request('PUT', url, data=file, headers=headers)

    def validate_object_type(self, object_type, object_type_id):
        if object_type not in ['me', 'drives', 'groups', 'sites', 'users']:
            return_error("object type can be only the next values: \"'me', 'drives', 'groups', 'sites', 'users'\"")

        if object_type_id != 'me':
            if not object_type_id:
                return_error("for \"'drives', 'groups', 'sites', 'users'\", must pass 'object_type_id' as argument")

    def upload_new_file(self, object_type, parent_id, file_name, entry_id, object_type_id=None):
        """
        this function upload new file to a selected folder(parent_id)
        :param object_type: drive/ group/ me/ site/ users
        :param object_type_id: the selected object type id.
        :param parent_id: 
        :param file_name:
        :param entry_id: 
        :return:
        """
        object_type = object_type.lower()
        file_path = r'/Users/gberger/Desktop/Untitled.docx' #  TODO: remove when finish to debug
        # file_path = demisto.getFilePath(entry_id).get(‘path’) # TODO: change it to the file_path

        self.validate_object_type(object_type, object_type_id)

        if 'me' == object_type:
            url = f'{object_type}/drive/items/{parent_id}:/{file_name}:/content'

        elif 'drives' == object_type:
            url = f'{object_type}/{object_type_id}/items/{parent_id}:/{file_name}:/content'

        else:
            url = f'{object_type}/{object_type_id}/drive/items/{parent_id}:/{file_name}:/content'
            # for sites, groups, users
        url = self.base_url + f'/{url}'
        with open(file_path, 'rb') as file:
            return self._http_request('PUT', url, data=file, headers=self.headers)


    def create_folder(self, folder_name, path, site_name):
        site_id = self.convert_site_name_to_site_id(site_name)  # TODO comment out
        access_token = self.get_api_token()  # TODO: put this in a class and access token will be an attribute
        headers = {'Authorization': f'Bearer {access_token}'}
        if path:
            item_id_to_create = self.get_item_id_by_path(path, site_id)  # if empty default is documents
        else:
            item_id_to_create = self.find_documents_folder_id(site_id)

        payload = f"{{'name': '{folder_name}',  'folder': {{}},  '@microsoft.graph.conflictBehavior': 'rename'}}"
        url = BASE_URL + f'/sites/{site_id}/drive/items/{item_id_to_create}/children'
        res = self._self._http_request('POST', url, data=payload, headers=headers)


    def delete_item_from_documents(self, path_to_item, site_name):
        site_id = self.convert_site_name_to_site_id(site_name)
        item_id_to_delete = self.get_item_id_by_path(path_to_item, site_id)
        drive_id = self.get_drive_id_for_site(site_id)
        access_token = self.get_api_token()  # TODO: put this in a class and access token will be an attribute
        headers = {'Authorization': f'Bearer {access_token}'}

        url = BASE_URL + f'/drives/{drive_id}/items/{item_id_to_delete}'

        res = self._http_request('DELETE', url, headers=headers)  # TODO: add validation if it works


def upload_new_file_command(client, args):

    object_type = args.get('object_type')
    entry_id = args.get('entry_id')
    parent_id = args.get('parent_id')
    file_name = args.get('file_name')
    object_type_id = args.get('object_type_id')

    result = client.upload_new_file(object_type, parent_id, file_name, entry_id, object_type_id)


    context_entry = result # TODO: think about what I want to return to the user: file name ? location? date_of_creation ?

    title = f'{INTEGRATION_NAME} - File information:'
    # Creating human readable for War room
    human_readable = tableToMarkdown(title, context_entry)

    # context == output
    context = {
        f'{INTEGRATION_NAME}.Document(val.ID && val.ID === obj.ID)': context_entry
    }

    return (
        human_readable,
        context,
        result
    )
def upload_document_to_document_folder_command(client, args):

    file_name = args.get('file_name')
    entry_id = args.get('entry_id')
    site_name = args.get('site_name')

    result = client.upload_document_to_document_folder(file_name, entry_id, site_name)


    context_entry = result  # TODO: think about what I want to return to the user: file name ? location? date_of_creation ?

    title = f'{INTEGRATION_NAME} - File information:'
    # Creating human readable for War room
    human_readable = tableToMarkdown(title, context_entry)

    # context == output
    context = {
        f'{INTEGRATION_NAME}.Document(val.ID && val.ID === obj.ID)': context_entry
    }

    return (
        human_readable,
        context,
        result
    )

def create_folder_command(client, args):
    folder_name = args.get('folder_name')
    entry_id = args.get('entry_id')
    site_name = args.get('site_name')
    path = args.get('path')

    result = client.create_folder(folder_name, path, site_name)


    context_entry = raw_response_to_context(result)  # TODO: think about what I want to return to the user: file name ? location? date_of_creation ?

    title = f'{INTEGRATION_NAME} - Folder information:'
    # Creating human readable for War room
    human_readable = tableToMarkdown(title, context_entry)

    # context == output
    context = {
        f'{INTEGRATION_NAME}.Folder(val.ID && val.ID === obj.ID)': context_entry
    }

    return (
        human_readable,
        context,
        result
    )


def delete_file_command(client, args):

    site_name = args.get('site_name')
    path = args.get('path')

    result = client.delete_item_from_documents(path, site_name)

    context_entry = raw_response_to_context(
        result)  # TODO: think about what I want to return to the user: file name ? location? date_of_creation ?

    title = f'{INTEGRATION_NAME} - Folder information:'
    # Creating human readable for War room
    human_readable = tableToMarkdown(title, context_entry)

    # context == output
    context = {
        f'{INTEGRATION_NAME}.Folder(val.ID && val.ID === obj.ID)': context_entry
    }

    return (
        human_readable,
        context,
        result  # == raw response
    )
def main():
    CLIENT_ID = demisto.params().get('client_id')
    CLIENT_SECRET = demisto.params().get('client_secret')
    # Remove trailing slash to prevent wrong URL path to service
    # SERVER = f"https://login.microsoftonline.com/{demisto.params().get('tenant_id')}"

    # Should we use SSL
    verify_certificate = not demisto.params().get('insecure', False)
    proxy = demisto.params().get('proxy', False)


    # How many time before the first fetch to retrieve incidents
    SHARE_POINT_DOMAIN = demisto.params().get('share_point_domain')


    LOG(f'Command being called is {demisto.command()}')
    try:
        # client = Client(BASE_URL, proxy=proxy, verify=verify_certificate)
        client = Client(base_url=BASE_URL, verify=verify_certificate, proxy=proxy)

        if demisto.command() == 'test-module':
            # This is the call made when pressing the integration Test button.
            result = test_module(client)
            demisto.results(result)

        elif demisto.command() == 'fetch-incidents':
            # Set and define the fetch incidents command to run after activated via integration settings.
            next_run, incidents = fetch_incidents(
                client=client,
                last_run=demisto.getLastRun(),
                first_fetch_time=first_fetch_time)

            demisto.setLastRun(next_run)
            demisto.incidents(incidents)

        elif demisto.command() == 'delete_item_from_documents_command':
            return_outputs(*delete_item_from_documents_command(client, demisto.args()))

        elif demisto.command() == 'create_folder_command':
            return_outputs(*create_folder_command(client, demisto.args()))

        elif demisto.command() == 'upload_document_to_document_folder_command':
            return_outputs(*upload_document_to_document_folder_command(client, demisto.args()))
        elif demisto.command() == 'upload_new_file_command':
            return_outputs(*upload_new_file_command(client, demisto.args()))

    # Log exceptions
    except Exception as e:
        return_error(f'Failed to execute {demisto.command()} command. Error: {str(e)}', e)


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


def test_module(client):
    """
    Performs basic get request to get item samples
    """

    result = client.get_api_token()
    if 'Hello DBot' == result:
        return 'ok'
    else:
        return 'Test failed because could not get access token'







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





def fetch_incidents(client, last_run, first_fetch_time):
    """
    This function will execute each interval (default is 1 minute).

    Args:
        client: HelloWorld client
        last_run: The greatest incident created_time we fetched from last fetch
        first_fetch_time: If last_run is None then fetch all incidents since first_fetch_time

    Returns:
        next_run: This will be last_run in the next fetch-incidents
        incidents: Incidents that will be created in Demisto
    """
    # Get the last fetch time, if exists
    last_fetch = last_run.get('last_fetch')

    # Handle first time fetch
    if last_fetch is None:
        last_fetch, _ = dateparser.parse(first_fetch_time)
    else:
        last_fetch = dateparser.parse(last_fetch)

    latest_created_time = last_fetch
    incidents = []
    items = client.list_incidents()
    for item in items:
        incident_created_time = dateparser.parse(item['created_time'])
        incident = {
            'name': item['description'],
            'occurred': incident_created_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'rawJSON': json.dumps(item)
        }

        incidents.append(incident)

        # Update last run and add incident if the incident is newer than last fetch
        if incident_created_time > latest_created_time:
            latest_created_time = incident_created_time

    next_run = {'last_fetch': latest_created_time.strftime(DATE_FORMAT)}
    return next_run, incidents



if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()