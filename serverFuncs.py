import requests
import json

headers = {
    'Authorization': 'Basic V0E6V2E1ODUxMzM1', 
    'Content-Type': 'application/json'
}

def checkGRZ(grz, baseAdress):
    url = baseAdress+"/GetDataGRZ?grz="+grz
    response = requests.request("GET", url, headers=headers, data="")
    data=json.loads(response.text)
    grzInfo=[None,None,None,None,None]
    for datas in data:
        if datas == "Success":
                grzInfo[0]=data[datas]
        if datas == "Car":
                grzInfo[1]=data[datas]
        if datas ==  "Driver":
                grzInfo[2]=data[datas]
        if datas ==  "Act_number":
                grzInfo[3]=data[datas]
        if datas ==  "Rent_number":
                grzInfo[4]=data[datas]
    return grzInfo

def checkUser(userPhone):
    payload = json.dumps({
    "Telephone": userPhone
    })
    url = "https://тест.атимо.рф/ATM/hs/WebApp/UserAuthorization"
    response = requests.request("GET", url, headers=headers, data=payload)
    data=json.loads(response.text)
    if data["Success"]==True:
        contacts = [
            data["Success"],
            data["User"],
            data["Base_address"],
        ]  
        return contacts
    else:
        contacts = [
            data["Success"]
        ]
        return contacts  
  
    

def checkDamageList():
    url = "http://тест.атимо.рф/Taksopark/hs/WebApp/GetDamage"
    response = requests.request("GET", url, headers=headers, data={})
    print(response.text)


def getCarDamages():
    url = "http://тест.атимо.рф/Taksopark/hs/WebApp/GetCarDamages?grz=ВМ43899&Telephone=+79313033207&Object_id=1"
    response = requests.request("GET", url, headers=headers, data={})
    print(response.text)


