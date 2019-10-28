import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

FETCH_WINDOW = demisto.args().get('fetch_window', '2 months')
USER = demisto.args().get('user')
REPO = demisto.args().get('repo')
LABEL = demisto.args().get('label')
time_range_start, _ = parse_date_range(FETCH_WINDOW)
reg = re.compile("\.\d{6}$")
timestamp, _ = reg.subn('', time_range_start.isoformat())
query = f'repo:{USER}/{REPO} is:pr is:open label:{LABEL} updated:>{timestamp}'

try:
    # Calling a command - returns a list of one or more entries
    cmd_res = demisto.executeCommand('GitHub-search-issues', {'query': query})
    issues = demisto.get(cmd_res[0], 'Contents.items')
    demisto.results(issues)

except Exception as e:
    return_error(e)
