import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

FETCH_WINDOW = demisto.args().get('fetch_window', '2 months')
USER = demisto.args().get('user')
REPO = demisto.args().get('repo')
LABEL = demisto.args().get('label')
time_range_start, _ = parse_date_range(FETCH_WINDOW)
timestamp = time_range_start.isoformat().split('T')[0]
query = f'repo:{USER}/{REPO} is:issue is:open label:{LABEL} updated:>{timestamp}'
demisto.results(query)

try:
    # Calling a command - returns a list of one or more entries
    cmd_res = demisto.executeCommand('GitHub-search-issues', {'query': query})
    demisto.results(cmd_res)
    issues = demisto.get(cmd_res[0], 'Contents.items')
    demisto.results(issues)

except Exception as e:
    demisto.results(e)
