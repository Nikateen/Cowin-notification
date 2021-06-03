import requests
from requests.structures import CaseInsensitiveDict
import telebot
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerUser, InputPeerChannel
from telethon import TelegramClient, sync, events
import time
from sys import argv
from datetime import datetime, timedelta


listOfDates = argv[1].split(",")
agePreferred = list(map(int,argv[2].split(",")))
vaccinesPreferred = argv[3].split(",")
listOfDistrictID = list(map(int,argv[4].split(",")))
bot_token = argv[5]
bot_chatID = argv[6]


expireTime = 3

def sendtext(bot_message, bot_token, bot_chatID):
   send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
   response = requests.get(send_text)
   return response.json()


def requestInfo(dID,date):
    url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/findByDistrict?district_id="+str(dID)+"&date="+ date

    headers = CaseInsensitiveDict()
    headers["accept"] = "application/json"
    headers["Accept-Language"] = "en_US"

    response = requests.get(url,headers=headers)
    data = response.json()
    return data

def removeExpired(expire_queue):
    now = datetime.now()
    topop = []
    for i in expire_queue.keys():    
        if(expire_queue[i] < now ):
            topop.append(i)

    for i in topop:
        expire_queue.pop(i)

    print("E Q",expire_queue)
    return expire_queue



expire_queue = {}

while(True):
    expire_queue = removeExpired(expire_queue)
    time.sleep( 7*len(listOfDistrictID)*len(listOfDates) )

    print("Checking...")
    for date in listOfDates:
        for Did in listOfDistrictID:
            data = requestInfo(Did,date)
            listOfSessions = data["sessions"]
            print("District {d}:".format(d=Did))
            flag = 1
            for session in listOfSessions:
                if( (session["vaccine"] in vaccinesPreferred) and (  (int(session["available_capacity_dose1"]) > 0) or (int(session["available_capacity_dose2"] > 0))  ) and (int(session["min_age_limit"]) in agePreferred) ):
                    message = """*{pincode}*\n*{date}*\n{hname}\n{address}\n*{vname}:*\n{doses1} doses available for dose 1 \n{doses2} doses available for dose 2\n[{slots}]""".format(pincode = session["pincode"], 
                    hname = session['name'],
                    date = date,
                    address = session["address"],
                    vname=session["vaccine"], 
                    doses1 = session["available_capacity_dose1"],
                    doses2 = session["available_capacity_dose2"],
                    slots = session["slots"],
                    )

                    endingmsg = "\n\n\n*last updated at:* \n{atime}\n\n\n".format(atime = datetime.now())
                    #print(message + endingmsg)

                    if message not in expire_queue.keys():
                        resp = sendtext(message+endingmsg,bot_token,bot_chatID)
                        print("Message sent!\n\n\n")
                        
                        expire_queue[message] = datetime.now()+ timedelta(minutes = expireTime )
                        print(expire_queue)
                    else:
                        print("Message already sent")

                    flag = 0

            if(flag):
                print("Not Found!")

    print()
    print()
    print("Finished!")
    print()
    print()  


#print(listOfSessions)
