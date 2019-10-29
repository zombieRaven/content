import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

FETCH_WINDOW = demisto.args().get('fetch_window', '2 months')
USER = demisto.args().get('user')
REPO = demisto.args().get('repo')
LABELS = argToList(demisto.args().get('label'))
LIMIT = demisto.args().get('limit')
time_range_start, _ = parse_date_range(FETCH_WINDOW)
timestamp = time_range_start.isoformat().split('T')[0]
labels = str([f'label:\"{label}\"' for label in LABELS])[1:-1].replace(',', '').replace('\'', '')

query = f'repo:{USER}/{REPO} is:issue is:open {labels} updated:>{timestamp}'
demisto.results(query)

try:
    # Calling a command - returns a list of one or more entries
    cmd_res = demisto.executeCommand('GitHub-search-issues', {'query': query, 'limit': {LIMIT}})
    demisto.results(cmd_res)
    issues = demisto.get(cmd_res[0], 'Contents.items')
    demisto.results(issues)

except Exception as e:
    demisto.results(e)
