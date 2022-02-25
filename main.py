from functools import lru_cache
from random import randint
import json
import logging
import math
import urllib
import Google_Sheets
import requests
import boto3

s3 = boto3.resource('s3')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


#used to post message to Slack or edit previously posted message
SLACK_URL = "https://slack.com/api/chat.postMessage"
SLACK_UPDATE = "https://slack.com/api/chat.update"
SLACK_HISTORY = "https://slack.com/api/conversations.history"
SLACK_MODAL = "https://slack.com/api/views.open"

auth_token = 'YOUR SLACK BOT TOKEN'


def lambda_handler(event, context):

    
    bucket = 'YOUR AWS BUCKET'
    key = 'YOUR BUCKET KEY'

    obj = s3.Object(bucket, key)
    data = obj.get()['Body'].read().decode('utf-8')
    json_data = json.loads(data)

    
    #get the imput from the SNS event
    message = event['Records'][0]['Sns']['Message']
    
    #change the string into a dict
    message = json.loads(message)
    print(message)
    
    #get the subcommand, subsubcommand and channel id from the input
    subcommand = message['subcommand']
    subsubcommand = message['subsubcommand']
    channel_id = message['channel_id']
    trigger_id = message['trigger_id']

    #if the receiver posted "just a second...", try and update it
    if subcommand=='submittals' or subcommand=='rfis' or subcommand=='submittal' or subcommand=='rfi' or subcommand=='due':
        if subsubcommand is not None:
            for projects in json_data:
                if projects['Project Number'] == subsubcommand:
                    print('found it')
                    project_name = projects['Project Name']
                    gs_link = projects['Google Sheets']
                    payload_text = "Just a second..."
                    break
            else:
                payload_text = "I cannot find that project number in my database.\r\nMake sure it is correct and that it belongs to a project I am assigned to monitor."
                
        else:
            for projects in json_data:
                if projects['Slack Channel Id'] == channel_id:
                    print('posted in project-specific channel')
                    gs_link = projects['Google Sheets']
                    project_name = projects['Project Name']
                    payload_text = "Just a second..."
                    break
            else:
                print('no subsub AND not in project specific-channel')
                payload_text = "No project number detected. Please try again with a project number, or send the command from the project-specific channel."
            
         #send a waiting message to aknowledge request
        payload = {
                "channel": channel_id,
                "text": payload_text #"Just a second..."
        }
        
        post_to_slack(payload,SLACK_URL)
        
        if "second" not in payload_text:
            print("ABORT")
            return None
        
        #url for the get request (to get channel history and change the last message)
        querystring = SLACK_HISTORY + f'?channel={channel_id}&limit=5&pretty=1'
        header = {'Authorization': 'Bearer ' + auth_token}

        #ask Slack for the last 5 messages sent to this channel
        response = requests.get(querystring, headers=header)

        #translate them to a json
        history_json = response.json()
        
        #check the array of each message and return the most recent said by a bot that is saying "Just a second..."
        for array in history_json['messages']:
            if 'bot_id' in array.keys() and array['text'] == 'Just a second...' :
                timestamp = array['ts']
                break
        
        #now that we have sent that message and have the necessary data, we can later update it after the Google Sheets data is ready

    
    #route the command to the appropriate response
    if subcommand == 'prime':
        if subsubcommand is None:
            response = "This command requires a number as second argument to run."
        elif not is_integer(subsubcommand):
            response = "Only integers can be Prime. Well, integers and me - Optimus Prime!"
        else:
            response = isPrime(int(float(subsubcommand)))
            
    elif subcommand == 'quote':
            response = quote_list[randint(0, len(quote_list)-1)]
        
    elif subcommand == 'powerball':
            response = powerballstr()
        
    elif subcommand == 'echo':
        response = 'test received.' 
                
    elif subcommand == 'submittals' or subcommand == 'submittal':
        response = f'Here are the currently open submittals for {project_name}: \r\n'
        response += Google_Sheets.main_gs('submittals',gs_link, False)
        
    elif subcommand == 'rfis' or subcommand == 'rfi':
        response = f'Here are the currently open RFIs for {project_name}: \r\n'
        response += Google_Sheets.main_gs('rfis',gs_link, False)
        
    elif subcommand == 'due':
        response = f'Here are the currently outstanding items for {project_name}: \r\n\r\n'
        response += Google_Sheets.main_gs('due',gs_link, False)
        
    elif subcommand == 'due_scheduled':
        for project in json_data:
            try:
                response = Google_Sheets.main_gs('due',project['Google Sheets'], True)
                
                if response and not response.isspace():
                    project_name = project['Project Name']
                    response = f'Here are the currently outstanding items for {project_name}: \r\n\r\n' + response
                    payload = {
                        "channel": project['Slack Channel Id'],
                        "text": response
                    }
                    
                    post_to_slack(payload,SLACK_URL)
            except Exception as e:
                print(f"Issue posting to Slack: {e}")
    
    else:
        response = f'I do not recognize that command {subcommand}. For a list of recognized command, type \"/optimus help\".' 
    
    #content to send to Slack
    if subcommand=='submittals' or subcommand=='rfis' or subcommand=='submittal' or subcommand=='rfi' or subcommand=='due':
        payload = {
            "channel": channel_id,
            "ts": timestamp,
            "text": response
        }
        
        post_to_slack(payload,SLACK_UPDATE)
        
    elif subcommand =='due_scheduled':
        print('do nothing')
        
    else:
        payload = {
            "channel": channel_id,
            "text": response
        }
        
        post_to_slack(payload,SLACK_URL)

    return None


def is_integer(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()
        

@lru_cache(maxsize=60)
def isPrime(i):
    if (i == 2 or i==3):  # shortcut low primes
        return f'This number is a Prime. Not as great of a Prime as I am though.'
    else: 
        if (i % 2 == 0 or i % 3 == 0):  # special since we go 3-> sqrt
            return "That number is not a Prime. Unlike me!"
        sqrt = int(math.sqrt(i) // 1)
        for s in range(3,sqrt+1,2):  # check odd vals, or all prior primes + new primes
            if (i % s == 0):
                return "That number is not a Prime. Unlike me!"
        return f'This number is a Prime. Not as great of a Prime as I am though.'
        
        
def powerballstr():

    #Would be better randomized, but that will do
    powerball_numbers = ["46 56 63 39 57 (PB: 26)", 
                        "10 14 29 11 13 (PB: 10)", 
                        "50 13 2 22 40 (PB: 13)", 
                        "25 60 11 31 7 (PB: 14)", 
                        "17 1 6 5 41 (PB: 14)", 
                        "40 64 22 15 31 (PB: 11)"]

    intro_sentences = ["I have a good feeling about ", 
                        "Let me calculate the odds... My processor tells me that you should play ", 
                        "Trust me, you should play ", 
                        "I came from the future, and if I were you I'd go big on "]
                        
    return f'{intro_sentences[randint(0, len(intro_sentences)-1)]} {powerball_numbers[randint(0, len(powerball_numbers)-1)]}.'
    

quote_list = ['Freedom is the right of all sentient beings.',
            'In any war, there are calms between storms. There will be days when we lose faith. Days when our allies turn against us...but the day will never come that we forsake this planet and its people.',
            'I am Optimus Prime, leader of the autobots.',
            'I will never stop fighting for our Freedom.',
            'Fate rarely calls upon us at a moment of our choosing.',
            'Neither impossible nor impassable!',
            'Sometimes even the wisest of men and machines can be in error.',
            'I am Optimus Prime, and I send this message so that our pasts will always be remembered. For in those memories, we live on.',
            'Above all, do not lament my absence, for in my spark, I know that this is not the end, but merely a new beginning. Simply put, another transformation.',
            'Hang on your dreams, Chip. The future is built on dreams. Hang on.',
            'Save the war stories, hotshot. Just remember, there’s a thin line between being a hero, and being a memory.',
            'Your people must learn to be masters of their own fate.']
            
def post_to_slack(json_payload,post_url):

    #encode content
    payload = json.dumps(json_payload).encode('utf8')
    
    request = urllib.request.Request(post_url, data=payload, method="POST")
    request.add_header( 'Content-Type', 'application/json;charset=utf-8' )
    request.add_header( 'Authorization', 'Bearer ' + auth_token )

    # Fire off the request!
    x = urllib.request.urlopen(request).read()
    print("posted to slack")
    