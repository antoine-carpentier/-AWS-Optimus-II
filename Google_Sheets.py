from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from datetime import datetime
import json
 
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
spreadsheet_id = 'YOUR GOOGLE SHEETS SPREADSHEET ID' 


def main_gs(option,gs_link, bool):
    creds = service_account.Credentials.from_service_account_file('Google_service_acc_creds.json',scopes=SCOPES)
    
    service = build('sheets', 'v4', credentials=creds)
    
    spreadsheet_id = gs_link[gs_link.index('d/'):]
    print(spreadsheet_id)
    spreadsheet_id = spreadsheet_id.split("/")[1]
    print(spreadsheet_id)

    # Call the Sheets API
    sheet = service.spreadsheets()

    if option == 'submittals':
        slackpost = open_submittals(sheet, spreadsheet_id)
    elif option == 'rfis':
        slackpost = open_rfis(sheet, spreadsheet_id)
    elif option == 'due':
        slackpost = get_rfis_due(sheet, spreadsheet_id,bool)
        slackpost += '\r\n' + get_submittals_due(sheet, spreadsheet_id,bool)
    else:
        slackpost = 'Please select an option.\r\nAvailable options are \'submittals\', \'rfis\' or \'due\'.'

    print(slackpost)

    return slackpost


def open_submittals(sheet, spreadsheet_id):
    cell_range = 'Submittals!A3:L'
    
    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=cell_range).execute()
    values = result.get('values', [])

    values.pop(0)
    
    for row in values:
        try:
            row[4] = datetime.strptime(row[4], '%m/%d/%Y').strftime('%m/%d/%Y')
        except ValueError:
            row[4] = '1/1/2099'
    
    values.sort(key=lambda x: datetime.strptime(x[4], '%m/%d/%Y'))

    high_subs = ''
    med_subs = ''
    other_subs = ''

    if not values:
        print('No data found.')
    else:
        for row in values:
            # only process subs that have not been sent
            print(len(row))
            if len(row) < 6 or row[5] == "":
                # sort by priority
                if len(row) >= 12 and row[11] != "":
                    if 'h' in row[10].lower():
                        high_subs += f'\t - {row[0]} - {row[2]} (Due *{row[4]}*) [assigned to {row[11]}].\r\n'
                    elif 'm' in row[10].lower():
                        med_subs += f'\t - {row[0]} - {row[2]} (Due *{row[4]}*) [assigned to {row[11]}].\r\n'
                    else:
                        other_subs += f'\t - {row[0]} - {row[2]} (Due *{row[4]}*) [assigned to {row[11]}].\r\n'
                elif len(row) >= 11 and 'h' in row[10].lower():
                    high_subs += f'\t - {row[0]} - {row[2]} (Due *{row[4]}*).\r\n'
                elif len(row) >= 11 and 'm' in row[10].lower():
                    med_subs += f'\t - {row[0]} - {row[2]} (Due *{row[4]}*).\r\n'
                else:
                    other_subs += f'\t - {row[0]} - {row[2]} (Due *{row[4]}*).\r\n'
                    
    slackpost = '' #'Here are the currently open submittals for Perryville: \r\n'

    if high_subs:
        slackpost += "\r\n *• High Priority:* \r\n" + high_subs
    if med_subs:
        slackpost += "\r\n *• Medium Priority:* \r\n" + med_subs
    if other_subs:
        slackpost += "\r\n *• Low Priority:* \r\n" + other_subs

    return slackpost


def open_rfis(sheet, spreadsheet_id):
    cell_range = 'RFIs!A4:O'

    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=cell_range).execute()
    values = result.get('values', [])

    values.pop(0)
    
    for row in values:
        try:
            row[3] = datetime.strptime(row[3], '%m/%d/%Y').strftime('%m/%d/%Y')
        except ValueError:
            row[3] = '1/1/2099'
    
    values.sort(key=lambda x: datetime.strptime(x[3], '%m/%d/%Y'))

    high_rfis = ''
    med_rfis = ''
    other_rfis = ''

    if not values:
        print('No data found.')
    else:
        for row in values:
            # only process subs that have not been sent
            if len(row) < 5 or row[4] == "":
                # sort by priority
                if len(row) >= 15 and row[14] != "":
                    if 'h' in row[13].lower():
                        high_rfis += f'\t - {row[0]} - {row[1]} (Due *{row[3]}*) [assigned to {row[14]}].\r\n'
                    elif 'm' in row[13].lower():
                        med_rfis += f'\t - {row[0]} - {row[1]} (Due *{row[3]}*) [assigned to {row[14]}].\r\n'
                    else:
                        other_rfis += f'\t - {row[0]} - {row[1]} (Due *{row[3]}*) [assigned to {row[14]}].\r\n'
                elif len(row) >= 14 and 'h' in row[13].lower():
                    high_rfis += f'\t - {row[0]} - {row[1]} (Due *{row[3]}*).\r\n'
                elif len(row) >= 14 and 'm' in row[13].lower():
                    med_rfis += f'\t - {row[0]} - {row[1]} (Due *{row[3]}*).\r\n'
                else:
                    other_rfis += f'\t - {row[0]} - {row[1]} (Due *{row[3]}*).\r\n'

    slackpost = '' #'Here are the currently open RFIs for Perryville: \r\n'

    if high_rfis:
        slackpost += "\r\n *• High Priority:* \r\n" + high_rfis
    if med_rfis:
        slackpost += "\r\n *• Medium Priority:* \r\n" + med_rfis
    if other_rfis:
        slackpost += "\r\n *• Low Priority:* \r\n" + other_rfis

    return slackpost


def get_rfis_due(sheet, spreadsheet_id,bool):
    cell_range = 'RFIs!A4:O'

    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=cell_range).execute()
    values = result.get('values', [])

    values.pop(0)
    
    for row in values:
        try:
            row[3] = datetime.strptime(row[3], '%m/%d/%Y').strftime('%m/%d/%Y')
        except ValueError:
            row[3] = '1/1/2099'
    
    values.sort(key=lambda x: datetime.strptime(x[3], '%m/%d/%Y'))

    rfis_due = ''

    userjson = open('Slack_users.json', )
    users_ids = json.load(userjson)

    today = datetime.now()

    date_string = today.strftime("%d/%m/%Y")

    if not values:
        print('No data found.')
    else:
        for row in values:
            # only process subs that have not been sent
            if len(row) < 5 or row[4] == "":
                # check rfis due today
                if datetime.strptime(row[3], '%m/%d/%Y').strftime("%d/%m/%Y") == date_string or datetime.strptime(
                        row[3], '%m/%d/%Y') < today:
                    if len(row) >= 15 and row[14] != "":
                        if row[14].lower() in users_ids.keys():
                            rfis_due += f'\t • {row[0]} - {row[1]} [assigned to <@{users_ids[row[14].lower()]}>].\r\n'
                        else:
                            rfis_due += f'\t • {row[0]} - {row[1]} [assigned to {row[14]}].\r\n'
                    else:
                        rfis_due += f'\t • {row[0]} - {row[1]}.\r\n'

    if rfis_due == '':
        if bool == True:
            slackpost=''
        else:
            slackpost = 'There are *no RFIS* due today or overdue. Good job, folks!\r\n\r\n'
    else:
        slackpost = 'Here are the RFIs that are due today/overdue: \r\n' + rfis_due

    return slackpost


def get_submittals_due(sheet, spreadsheet_id,bool):
    cell_range = 'Submittals!A3:L'

    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=cell_range).execute()
    values = result.get('values', [])

    values.pop(0)
    
    for row in values:
        try:
            row[4] = datetime.strptime(row[4], '%m/%d/%Y').strftime('%m/%d/%Y')
        except ValueError:
            row[4] = '1/1/2099'
        
    values.sort(key=lambda x: datetime.strptime(x[4], '%m/%d/%Y'))

    submittals_due = ''

    user_json = open('Slack_users.json', )
    users_ids = json.load(user_json)

    today = datetime.now()

    date_string = today.strftime("%d/%m/%Y")

    if not values:
        print('No data found.')
    else:
        for row in values:
            # only process subs that have not been sent
            if len(row) < 6 or row[5] == "":
                # check  due today
                if datetime.strptime(row[4], '%m/%d/%Y').strftime("%d/%m/%Y") == date_string or datetime.strptime(
                        row[4], '%m/%d/%Y') < today:
                    if len(row) >= 12 and row[11] != "":
                        if row[11].lower() in users_ids.keys():
                            submittals_due += f'\t • {row[0]} - {row[2]} [assigned to <@{users_ids[row[11].lower()]}>].\r\n '
                        else:
                            submittals_due += f'\t • {row[0]} - {row[2]} [assigned to {row[11]}].\r\n'
                    else:
                        submittals_due += f'\t • {row[0]} - {row[2]}.\r\n'

    if submittals_due == '':
        if bool == True:
            slackpost=''
        else:
            slackpost = 'There are *no submittals* due today or overdue. Well done!'
    else:
        slackpost = 'Here are the submittals that are due today/overdue: \r\n' + submittals_due  # + '\r\nGet cranking!'

    return slackpost
    
def sort_by_date(x):
    try:
        date = datetime.strptime(x, '%m/%d/%Y')
    except ValueError:
        date = '1/1/2099'
    
    return date
    
