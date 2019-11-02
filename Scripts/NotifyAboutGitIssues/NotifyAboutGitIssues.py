import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

GITHUB_TO_SLACK = {
    'Itay4': 'ikeren@paloaltonetworks.com',
    'yaakovi': 'syaakovi@paloaltonetworks.com',
    'ronykoz': 'rkozakish@paloaltonetworks.com',
    'yuvalbenshalom': 'ybenshalom@paloaltonetworks.com',
    'anara123': 'aazadaliyev@paloaltonetworks.com',
    'adi88d': 'adaud@paloaltonetworks.com',
    'amshamah419': 'ashamah@paloaltonetworks.com',
    'Arsenikr': 'akrupnik@paloaltonetworks.com',
    'bakatzir': 'bkatzir@paloaltonetworks.com',
    'dantavori': 'dtavori@paloaltonetworks.com',
    'DeanArbel': 'darbel@paloaltonetworks.com',
    'guykeller': 'gkeller@paloaltonetworks.com',
    'GalRabinDemisto': 'grabin@paloaltonetworks.com',
    'glicht': 'glichtman@paloaltonetworks.com',
    'guyfreund': 'gfreund@paloaltonetworks.com',
    'David-BMS': 'dbaumstein@paloaltonetworks.com',
    'idovandijk': 'ivandijk@paloaltonetworks.com',
    'IkaDemisto': 'igabashvili@paloaltonetworks.com',
    'liorblob': 'lblobstein@paloaltonetworks.com',
    'michalgold': 'mgoldshtein@paloaltonetworks.com',
    'mayagoldb': 'mgoldberg@paloaltonetworks.com',
    'orenzohar': 'ozohar@paloaltonetworks.com',
    'orlichter1': 'olichter@paloaltonetworks.com',
    'reutshal': 'rshalem@paloaltonetworks.com',
    'roysagi': 'rsagi@paloaltonetworks.com',
    'Shellyber': 'sberman@paloaltonetworks.com',
    'teizenman': 'teizenman@paloaltonetworks.com',
    'yardensade': 'ysade@paloaltonetworks.com',
    'avidan-H': 'ahessing@paloaltonetworks.com',
    'ShahafBenYakir': 'sbenyakir@paloaltonetworks.com'
}

FETCH_WINDOW = demisto.args().get('fetch_window', '2 months')
USER = demisto.args().get('user')
REPO = demisto.args().get('repo')
LABELS = argToList(demisto.args().get('labels'))
LIMIT = demisto.args().get('limit')
PERIOD_FILTER = int(demisto.args().get('period_filter'))


def is_once_aweek(issue):
    date = issue.get('created_at')[:-1]
    formatted_date = parse_date_string(date)
    today = datetime.today()
    delta = today - formatted_date
    days_passed = delta.days
    # True only if the issue have completed a period. For example if the PERIOD_FILTER is 7 days this will return true
    # after 7 days, 14 days, 21 days and on
    return days_passed > 0 and days_passed % PERIOD_FILTER == 0


def add_email_to_issues(issues):
    for issue in issues:
        if issue.get('assignee'):
            assignee = issue.get('assignee').get('login')
            issue['AssigneeEmail'] = GITHUB_TO_SLACK[assignee]

    return issues


def send_message(issue):
    recipient = issue.get('AssigneeEmail')
    if recipient:
        url = issue.get('html_url')
        message = '*This is a friendly reminder about your dev task involving a failing test.*\n' \
                  'We know you are doing your best, just making sure you have not forgot about it ' \
                  f':muscle::skin-tone-3::dbot-new:.\n{url}'
        demisto.results(demisto.executeCommand('send-notification', {'to': recipient, 'message': message, 'ignoreAddURL': 'true'}))
    return


time_range_start, _ = parse_date_range(FETCH_WINDOW)
timestamp = time_range_start.isoformat().split('T')[0]
labels = str([f'label:\"{label}\"' for label in LABELS])[1:-1].replace(',', '').replace('\'', '')

query = f'repo:{USER}/{REPO} is:issue is:open {labels} created:>{timestamp}'
try:
    # Calling a command - returns a list of one or more entries
    cmd_res = demisto.executeCommand('GitHub-search-issues', {'query': query, 'limit': LIMIT})
    issues = demisto.get(cmd_res[0], 'Contents.items')
    filtered_issues = list(filter(is_once_aweek, issues))
    filtered_issues = add_email_to_issues(filtered_issues)
    return_outputs(tableToMarkdown('List of Issues', filtered_issues), {'GitHub.Issue': filtered_issues}, cmd_res)
    for issue in filtered_issues:
        send_message(issue)

except Exception as e:
    demisto.results(e)
