import sys
import requests
from requests.structures import CaseInsensitiveDict
import telebot
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerUser, InputPeerChannel
from telethon import TelegramClient, sync, events
import time ,getopt
from sys import argv,exit
from datetime import datetime, timedelta

full_cmd_arguments = argv
argument_list = full_cmd_arguments[1:]

#Argument Description
short_options = "a:c:d:D:A:v:o:t:O"
long_options = ["api=", "cid=", "did=","date=","age=","vaccine=","dose=","threshold=","alternate"]

#Required Values
listOfDistrictID = []
bot_token = 0
bot_chatID = 0

#Default Values
threshold = 1
expireTime = 3
alternate = 0
doses=["1","2"]
vaccinesPreferred = ["COVAXIN","COVISHIELD","SPUTNIK"]
agePreferred = [18,45]
listOfDates = [datetime.today().strftime("%d-%m-%Y")]

#Extracting user args
try:
    arguments, values = getopt.getopt(argument_list, short_options, long_options)
except getopt.error as err:
    # Output error, and return with an error code
    print (str(err))
    exit(2)


for current_argument, current_value in arguments:
    if current_argument in ("-a", "--api"):
        bot_token = current_value
    
    elif current_argument in ("-c", "--cid"):
        bot_chatID = current_value
        
    elif current_argument in ("-d", "--did"):
        listOfDistrictID = list(map(int,current_value.split(",")))

    elif current_argument in ("-D", "--date"):
        listOfDates = current_value.split(",")

    elif current_argument in ("-A", "--age"):
        agePreferred = list(map(int,current_value.split(",")))

    elif current_argument in ("-v", "--vaccine"):
        vaccinesPreferred = current_value.split(",")

    elif current_argument in ("-o", "--dose"):
        doses = current_value.split(",")
    
    elif current_argument in ("-e", "--expire"):
        expireTime = int(current_value)
    
    elif current_argument in ("-t", "--threshold"):
        threshold = int(current_value)

    elif current_argument in ("-O", "--alternate"):
        alternate = 1




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


def requestInfoV2(dID,date):
    url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id="+str(dID)+"&date="+ date

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

    #print("E Q",expire_queue)
    return expire_queue


def infoV1Parse(bot_token, bot_chatID, listOfDistrictID, listOfDates, agePreferred, vaccinesPreferred, doses, expireTime):
    expire_queue = {}
    while(True):
        try:
            expire_queue = removeExpired(expire_queue)
            time.sleep( 8*len(listOfDistrictID)*len(listOfDates) )
            print("\n"*5)
            print("   Checking   ".center(50,"#"))
            print()
            print()

            for date in listOfDates:
                print()
                print("{date}".format(date=date).center(50,"_"))
                print("‾".center(50,"‾") )
                #print()

                for Did in listOfDistrictID:
                    data = requestInfo(Did,date)
                    listOfSessions = data["sessions"]
                    print()
                    print("DID {d}:".format(d=Did).ljust(50,"~") )
                    flag = 1

                    for session in listOfSessions:

                        if( (session["vaccine"] in vaccinesPreferred) 
                            and (   (int(session["available_capacity_dose1"] ) >= threshold and "1" in doses) or (int(session["available_capacity_dose2"]) >= threshold and "2" in doses)   ) 
                            and ( int(session["min_age_limit"]) in agePreferred) 
                        ):
                            message = """*{pincode}*\n*For {age}*\n*{date}*\n{hname}\n{address}\n*{vname}:*\n{doses1} doses available for dose 1 \n{doses2} doses available for dose 2\n[{slots}]
                            """.format(pincode = session["pincode"],
                            age = session['min_age_limit'],
                            hname = session['name'],
                            date = date,
                            address = session["address"],
                            vname=session["vaccine"], 
                            doses1 = session["available_capacity_dose1"],
                            doses2 = session["available_capacity_dose2"],
                            slots = session["slots"],
                            )

                            endingmsg = "\n\n*last updated at:* \n{atime}\n\n\n".format(atime = datetime.now())

                            if message not in expire_queue.keys():
                                resp = sendtext(message+endingmsg,bot_token,bot_chatID)

                                print("Update:{hname})".format(hname=str(session['name'])).rjust(50," ") )
                                print("D1:{d1} D2:{d2}".format( d1= str(session["available_capacity_dose1"]) ,d2= str(session["available_capacity_dose2"]) ).rjust(50," ") )
                                
                                expire_queue[message] = datetime.now()+ timedelta(minutes = expireTime )
                                print(expire_queue)
                            else:
                                #print("\n\Unchanged:{hname}\nD1:{d1} D2:{d2}\n\n".format(hname=session['name'] ,d1=session["available_capacity_dose1"],d2=session["available_capacity_dose2"] ))
                                pass

                            flag = 0

                    if(flag):
                        print("Not Found!".rjust(50," "))
                        print("Not Found!".rjust(50," "))
    
                    print("~".center(50,"~") )
                    print()

                print("_".format(dt=datetime.now() ).center(50,"_") )
                print("‾".format(dt=datetime.now() ).center(50,"‾") )
                print()

            print("\n"*3)
            print("   {dt}   ".format(dt=datetime.now() ).center(50,"#") )   
        except KeyboardInterrupt:
            sys.exit(2)
        except:
            print("FAILED")
            pass


def infoV2Parse():
    expire_queue = {}

    while True:

        expire_queue = removeExpired(expire_queue)
        time.sleep( 8*len(listOfDistrictID)*len(listOfDates) )

        print("\n"*5)
        print("   Checking   ".center(50,"#"))
        print("\n"*2)
        try:
            for date in listOfDates:
                print()
                print("Week: {date}".format(date=date).center(50,"_"))
                print("‾".center(50,"‾") )

                for districtID in listOfDistrictID:
                    data = requestInfoV2(districtID,date)
                    print()
                    print("DID {d}:".format(d=districtID).ljust(50,"~") )
                    flag = 1

                    for centre in data["centers"]:
                        listOfSessions = centre["sessions"]
                        for session in listOfSessions:
                            if( (session["vaccine"] in vaccinesPreferred) 
                            and (   (int(session["available_capacity_dose1"] ) >= threshold and "1" in doses) or (int(session["available_capacity_dose2"]) >= threshold and "2" in doses)   ) 
                            and ( int(session["min_age_limit"]) in agePreferred) 
                            ):

                                message = """*{pincode}*\n*For {age}*\n*{date}*\n{hname}\n{address}\n*{vname}:*\n{doses1} doses available for dose 1 \n{doses2} doses available for dose 2\n[{slots}]
                                """.format(pincode = centre["pincode"], 
                                age = session['min_age_limit'],
                                hname = centre['name'],
                                date = session['date'],
                                address = centre["address"],
                                vname = session["vaccine"], 
                                doses1 = session["available_capacity_dose1"],
                                doses2 = session["available_capacity_dose2"],
                                slots = session["slots"],
                                )

                                endingmsg = "\n\n*last updated at:* \n{atime}\n\n\n".format(atime = datetime.now())

                                if message not in expire_queue.keys():
                                    resp = sendtext(message+endingmsg,bot_token,bot_chatID)

                                    print("Update:{hname})".format(hname=str(centre['name'])).rjust(50," ") )
                                    print("D1:{d1} D2:{d2}".format( d1= str(session["available_capacity_dose1"]) ,d2= str(session["available_capacity_dose2"]) ).rjust(50," ") )
                                    
                                    expire_queue[message] = datetime.now()+ timedelta(minutes = expireTime )
                                    print(expire_queue)
                                    

                                else:
                                    #print("\n\Unchanged:{hname}\nD1:{d1} D2:{d2}\n\n".format(hname=session['name'] ,d1=session["available_capacity_dose1"],d2=session["available_capacity_dose2"] ))
                                    pass

                                flag = 0

                                print("Waiting..")
                                time.sleep(5)

                    if(flag):
                        print("Not Found!".rjust(50," "))
                        print("Not Found!".rjust(50," "))
        
                    print("~".center(50,"~") )
                    print()

                print("_".format(dt=datetime.now() ).center(50,"_") )
                print("‾".format(dt=datetime.now() ).center(50,"‾") )
                print()

            print("\n"*3)
            print("   {dt}   ".format(dt=datetime.now() ).center(50,"#") )

        except KeyboardInterrupt:
            sys.exit(2)



if alternate:
    infoV2Parse()
else:
    infoV1Parse(bot_token, bot_chatID, listOfDistrictID, listOfDates, agePreferred, vaccinesPreferred, doses, expireTime)
