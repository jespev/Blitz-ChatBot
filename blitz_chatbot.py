import json
import requests
import time
from requests_toolbelt.multipart.encoder import MultipartEncoder
import random

roomId = "xxx" 
meraki_api_key = "xxx"
webex_token = "xxx"
done_messages = []

jokes = [
    "I love pressing the F5 button. It's so refreshing",
    "There's no place like 127.0.0.1",
    "What is 100 IT Professionals under the sea? Answer - A good start",
    "I changed my password to 'incorrect'. So whenever I forget what it is the computer will say 'Your password is incorrect'",
    "What kind of doctor fixes broken websites? A URLologist",
    "There are only 10 kinds of people in the world. Those who understand binary and those do not",
    "Email from a friend – CanYouFixTheSpaceBarOnMyKeyboard?",
    "Why do java developers need to wear glasses? Because they don't C#",
    "A Man from the toilet shouts to his wife: Darling, darling, do you hear me?!!!! What happened, did you run out of toilet paper? No, restart the router, please!",
    '''A guy prepares to demonstrate voice control of a computer.
    Silence, please, I will now demonstrate how easy voice control works. A man from the back of the room:
    Format: C. Enter.''']
joke_index = 0


def initialize_bot():
    url = "https://api.ciscospark.com/v1/messages?roomId=" + roomId
    headers = {"Accept": "application/yang-data+json",
               'Authorization': "Bearer "+webex_token}
    response = requests.request("GET", url, headers=headers, verify=False)
    messages = json.loads(response.text)["items"]
    for item in messages:
        done_messages.append(item["id"])


def post_to_spark(text, roomId):
    url = "https://api.ciscospark.com/v1/messages"

    payload = {
        "text": text,
        "roomId": roomId
    }
    headers = {
        'Authorization': "Bearer "+webex_token,
        'Content-Type': "application/json; charset=utf-8",
        'cache-control': "no-cache"
    }
    response = requests.request("POST", url, data=json.dumps(payload), headers=headers, verify=False)
    return response


def display_menu(item):
    menu = '''
	Hello ''' + item["personEmail"] + ''', this is the Blitz-ChatBot Menu: 
	* blitz-help: displays this menu
	* blitz-joke: displays a bad joke
	* blitz-orgs: displays meraki organisations
	* blitz-networks {{org_id}}: displays meraki networks within an organisation
	'''
    post_to_spark(menu, roomId)
    done_messages.append(item["id"])


def display_joke():
    joke_index = random.randint(0, 9)
    post_to_spark(jokes[joke_index], roomId)


def display_orgs():
    url = "https://dashboard.meraki.com/api/v0/organizations"
    payload = ""
    headers = {
        'X-Cisco-Meraki-API-Key': meraki_api_key
    }
    response = requests.request("GET", url, data=payload, headers=headers)

    post_to_spark(response.text,roomId)


def display_networks(org_id):
    url = "https://dashboard.meraki.com/api/v0/organizations/"+org_id+"/networks"

    payload = ""
    headers = {
        'X-Cisco-Meraki-API-Key': meraki_api_key
    }

    response = requests.request("GET", url, data=payload, headers=headers)
    if response.status_code == 404:
        post_to_spark("* Organisation with id: " + str(org_id)+ " not found.",roomId)
        return
    post_to_spark(response.text, roomId)


def check_channel():
    url = "https://api.ciscospark.com/v1/messages?max=1&roomId=" + roomId
    headers = {"Accept": "application/yang-data+json",
               'Authorization': "Bearer "+webex_token}
    response = requests.request("GET", url, headers=headers, verify=False)
    messages = json.loads(response.text)["items"]

    for item in messages:
        message = item["text"].strip()
        if item["id"] in done_messages:
            break

        if "blitz-help" in message and "*" not in item["text"] and "Type" not in item["text"]:
            display_menu(item)
        elif "blitz-joke" in message and "*" not in item["text"]:
            display_joke()
        elif "blitz-orgs" in message and "*" not in item["text"]:
            display_orgs()
        elif "blitz-networks" in message and "*" not in item["text"]:
            params = item["text"].split()
            if len(params) != 2:
                post_to_spark("* Hello "+item["personEmail"] + ", usage is: blitz-networks {{org_id}}", roomId)
            else:
                org_id = params[1]
                display_networks(org_id)
    return


def post_file_to_spark(file_path, roomId):
    m = MultipartEncoder({'roomId': roomId,
                          'text': 'Config attached',
                          'files': ('File', open(file_path, 'rb'),
                                    'text/plain')})
    headers = {
        'Authorization': "Bearer " + webex_token,
        'Content-Type': m.content_type,
        'cache-control': "no-cache"
    }
    r = requests.post('https://api.ciscospark.com/v1/messages', data=m,
                      headers=headers)
    return


initialize_bot()
post_to_spark("Initializing Blitz-ChatBot. Type blitz-help for supported commands", roomId)
while (True):
    messages = check_channel()
    time.sleep(1)