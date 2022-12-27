
import telebot
from telebot import types
from telebot import custom_filters
import configure 
from telebot.handler_backends import State, StatesGroup #States
from telebot.storage import StateMemoryStorage
import gettext
import serverFuncs
import urllib


#Инициализация бота
state_storage = StateMemoryStorage()
bot = telebot.TeleBot(configure.config['token'], state_storage=state_storage)

ru=gettext.translation('messages', localedir='localization', languages=['ru_RU'])
en=gettext.translation('messages', localedir='localization', languages=['en'])
en.install()    

#Настройка "Menu" в боте
bot.set_my_commands([
    telebot.types.BotCommand("/start", "Перезапуск бота"),
    telebot.types.BotCommand("/cancel", "Отмена действия"),
    telebot.types.BotCommand("/help", "Помощь"),
    telebot.types.BotCommand("/changelanguage", "Смена языка")
])
reply_markup=types.ReplyKeyboardRemove()


#Словарь с данными о пользователе и введенных им значений.
user_dict = {}
user_lang_dict= {}


class User(StatesGroup):
    def __init__(self, phNumber):
        self.phoneNumber = phNumber
        self.name = None
        self.driver = None
        self.plates = None
        self.voditel= None
        self.aktNumber = None 
        self.odometer = None
        self.crashes=None
        self.base_address=None

class MyStates(StatesGroup): 
    language = {}
    base = None
    mechanicPhone = State()
    carAccept = State()
    carPretrip = State()
    chooseAction = State()
    mileageAccept = State()
    mileageCheck = State()
    vehicleNumber = State()
    mileagePretrip = State()
    webAppResponse = State()

#Клавиатура действий
def createInlineKeyboardWithFuncs():
    inlineKeyboard = types.InlineKeyboardMarkup(row_width=1)
    btns=[
            types.InlineKeyboardButton(text=_("Pre-trip inspection"), callback_data="pretrip_inspect"),
            types.InlineKeyboardButton(text=_("Car acceptance"), callback_data="car_acceptance"),
            types.InlineKeyboardButton(text=_("Exit"), callback_data="to_start")
    ] 
    inlineKeyboard.add(*btns)
    return inlineKeyboard

#Проверка языка пользователя
def checkLang(message):
    #print(MyStates.language)
    if user_lang_dict.get(message.chat.id)==None:
        if message.from_user.language_code=="ru":
            user_lang_dict[message.chat.id]="ru"
            ru.install()
        else:
            user_lang_dict[message.chat.id]="en"
            en.install()
    return True

#Проверка языка пользователя
def testLang(message):
    if user_lang_dict.get(message.chat.id)!=None:
        if message.from_user.language_code=="ru":
            ru.install()
        else:
            en.install()
    return True

#Изменение языка пользователя
def changeLanguage(message):
    if user_lang_dict[message.chat.id]=="ru":
        user_lang_dict[message.chat.id]="en"
        en.install()
        msg= bot.send_message(message.chat.id,"Language changed to English")
        
    else:
        user_lang_dict[message.chat.id]="ru"
        ru.install()
        msg= bot.send_message(message.chat.id,"Язык изменен на русский")



@bot.message_handler(commands=['start'], func=checkLang)
def start_ex(message):
    bot.set_state(message.from_user.id, MyStates.mechanicPhone, message.chat.id)
    bot.send_message(message.chat.id, _("Hello! \nPlease login to get started."), reply_markup='')
    bot.send_message(message.chat.id, _("Press the button at the bottom of the screen or send a phone number (ex. 79998887766) in a message:"), reply_markup=getSendPhoneKeyboard())

@bot.message_handler(commands=['changelanguage'])
def change_language_state(message):
    changeLanguage(message)
    start_ex(message)

@bot.message_handler(state=MyStates.mechanicPhone, content_types=['contact', 'text'], func=testLang)
def name_get(message):
    try:
        chat_id = message.chat.id
        #print(message.content_type)
        if message.content_type=="contact":
            contacts=serverFuncs.checkUser(message.contact.phone_number)
            if (contacts[0]):
                user= User(message.contact.phone_number)
                user.name=contacts[1]
                user.base_address=contacts[2]
                user_dict[chat_id] = user
                msg=bot.send_message(chat_id, f"{contacts[1]}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
                bot.set_state(message.from_user.id, MyStates.chooseAction, message.chat.id)
            else:
                msg=bot.send_message(chat_id, _("The employee is not in the database, enter the phone number again."), reply_markup=getSendPhoneKeyboard())
        else:
            contacts=serverFuncs.checkUser(message.text)
            if (contacts[0]):
                user= User(message.text)
                user.name=contacts[1]
                user.base_address=contacts[2]
                user_dict[chat_id] = user
                msg=bot.send_message(chat_id, f"{contacts[1]}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
                bot.set_state(message.from_user.id, MyStates.chooseAction, message.chat.id)
            else:
                msg=bot.send_message(chat_id, _("The employee is not in the database, enter the phone number again."), reply_markup=getSendPhoneKeyboard())
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))


#Обработка выбора функции
@bot.callback_query_handler(func=lambda call: True, state=MyStates.chooseAction, func=testLang)
def process_choose_func(call):
    try:
        chat_id=call.message.chat.id
        if call.data == 'car_acceptance':
            msg= bot.send_message(chat_id, _("Enter vehicle number"))
            bot.set_state(msg.chat.id, MyStates.carAccept)
        else:
            if call.data == 'pretrip_inspect':
                msg= bot.send_message(chat_id, _("Enter the driver's phone number"))
                bot.set_state(msg.chat.id, MyStates.carPretrip)
            else:
                if call.data == 'to_start':
                    msg=bot.send_message(chat_id, _("Exit"))
                    start_ex(msg)
        return
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))

#Приёмка авто - проверка номера авто
@bot.message_handler(state=MyStates.carAccept, func=testLang)
def car_accept(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        carInfo=serverFuncs.checkGRZ(message.text, user.base_address)
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

        if (carInfo[1]!=None):
            if (carInfo[2]!=None):
                keyboard.add(_("Yes"), _("No"))
                user.plates=message.text
                user.driver=carInfo[2]
                user.aktNumber=carInfo[3]
                msg= bot.send_message(chat_id, _("The driver")+f" \"{carInfo[2]}\" "+_("hands over the car issued under the act No.")+ carInfo[3]+ "?",reply_markup=keyboard )
                bot.set_state(message.from_user.id, MyStates.mileageAccept, message.chat.id)
            else:
                bot.send_message(chat_id, _("Driver not found. Check the entered data"))
        else:
            bot.send_message(chat_id, _("Vehicle not found. Check the entered data"))
       
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))

#Приёмка авто - проверка пробега
@bot.message_handler(state=MyStates.mileageAccept, func=testLang)
def process_car_accept_check(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        if message.text=="Да" or message.text=="Yes":
            msg=bot.send_message(chat_id, _("Enter vehicle mileage"), reply_markup=types.ReplyKeyboardRemove())
            bot.set_state(message.from_user.id, MyStates.mileageCheck, message.chat.id)
        elif message.text=="Нет" or message.text=="No":
            msg=bot.send_message(chat_id, _("You abandoned the action"), reply_markup=types.ReplyKeyboardRemove())
            msg=bot.send_message(chat_id, f"{user.name}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
        else:
            msg = bot.send_message(chat_id, _("Command not found"))
       
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))

#Приёмка авто - проверка пробега и открытие WebApp 
@bot.message_handler(state=MyStates.mileageCheck, func=testLang)
def process_car_odometer_check(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        odometerValue=serverFuncs.getOdometer(user.plates)
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if odometerValue[0]==True:
            #Настроить условия
            if int(message.text)>int(odometerValue[1])-500 and int(message.text)<int(odometerValue[1])+2000 :
                bot.reply_to(message, _("Mileage meets conditions"))
                user.odometer=int(message.text)
                x=urllib.parse.quote(user.plates)
                #print(user_lang[chat_id])
                url=types.WebAppInfo(configure.config['webAppNewDamage']+"?grz="+x+"&telephone="+user.phoneNumber+"&lang="+user_lang_dict[chat_id]+"&base="+urllib.parse.quote(user.base_address))
                #print(url)
                button = types.KeyboardButton(text=_("Form an act"), web_app=url)
                keyboard.add(button)
                msg=bot.send_message(chat_id, _("Next, you need to create an act"), reply_markup=keyboard)
                bot.set_state(message.from_user.id, MyStates.webAppResponse, message.chat.id)
            else:
                bot.reply_to(message, _("Mileage does not meet conditions"))
                msg = bot.send_message(chat_id, _("Enter mileage again"))
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))

#Обработка результата WebApps-ов
@bot.message_handler(content_types="web_app_data", state=MyStates.webAppResponse, func=testLang)
def webAppAnswer(message):
    try:
        if message.web_app_data.data=="Акт был сформирован" :
            bot.send_message(message.chat.id, _("The act has been formed."), reply_markup=types.ReplyKeyboardRemove())    
            bot.send_message(message.chat.id, _("Select an action."), reply_markup=createInlineKeyboardWithFuncs())    
            bot.set_state(message.from_user.id, MyStates.chooseAction, message.chat.id)
        else: 
            bot.send_message(message.chat.id, _("Error!"), reply_markup=types.ReplyKeyboardRemove())  
            bot.send_message(message.chat.id, f"{message.web_app_data.data}", reply_markup=createInlineKeyboardWithFuncs())  
            bot.set_state(message.from_user.id, MyStates.chooseAction, message.chat.id)
    except Exception as e:
        msg=bot.send_message(message.chat.id, _('Oops. Something went wrong'))

#Предрейсовый осмотр - проверка номера телефона водителя
@bot.message_handler(state=MyStates.carPretrip, func=testLang)
def process_car_inspection(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        if message.text!="Назад" or message.text!="Отмена" or message.text!="Cancel" or message.text!="Back":
            driverInfo=serverFuncs.getDriver(message.text)
            if driverInfo==True:
                user.voditel=message.text
                msg=bot.send_message(chat_id, _("Enter the vehicle number."))
                bot.set_state(message.from_user.id, MyStates.vehicleNumber, message.chat.id)
            else: 
                msg=bot.send_message(chat_id, _("Driver not found, please enter a different phone number."))
        else:
            msg=bot.send_message(chat_id, f"{user.name}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())

    except Exception as e:
         msg=bot.send_message(chat_id, _('Oops. Something went wrong'))

#Предрейсовый осмотр - ввод номера автомобиля
@bot.message_handler(state=MyStates.vehicleNumber, func=testLang)
def process_car_inspection_grz(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        if message.text!="Назад" or message.text!="Отмена" or message.text!="Cancel" or message.text!="Back":
            carInfo=serverFuncs.getCar(message.text)
            if carInfo==True:
                user.plates=message.text
                msg=bot.send_message(chat_id, _("Enter mileage"))
                bot.set_state(message.from_user.id, MyStates.mileagePretrip, message.chat.id)
            else: 
                msg=bot.send_message(chat_id, _("Vehicle not found, please enter another number"))
        else:
            msg=bot.send_message(chat_id, f"{user.name}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))

#Предрейсовый осмотр - ввод пробега и вывод кнопок с WebApp 
@bot.message_handler(state=MyStates.mileagePretrip, func=testLang)
def process_car_inspection_odometer(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

        if message.text!="Назад" or message.text!="Отмена" or message.text!="Cancel" or message.text!="Back":
            carInfo=serverFuncs.getOdometer(user.plates)
            #print(carInfo)
            if carInfo[0]==True and (carInfo[1]-100>int(message.text) and int(message.text)<carInfo[1]+100):
                x=urllib.parse.quote(user.plates)
                url=types.WebAppInfo(configure.config['webAppPretrip']+"?grz="+str(x)+"&lang="+user_lang_dict[chat_id]+"&mechPhone="+str(user.phoneNumber)+"&driverPhone="+str(user.voditel)+"&odo="+str(message.text)+"&base="+urllib.parse.quote(user.base_address));
                #print(url)
                button = types.KeyboardButton(text=_("Car check"), web_app=url)
                keyboard.add(button)
                msg=bot.send_message(chat_id, _("To go through the list of checks, click on the button \"Car check\""), reply_markup=keyboard)
            else: 
                msg=bot.send_message(chat_id, _("Mileage is not correct, please re-enter"))
        else:
            msg=bot.send_message(chat_id, f"{user.name}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())

    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))


#Отмена шага
@bot.message_handler(state="*", commands=['cancel'])
def any_state(message):
    bot.send_message(message.chat.id, "Действие отменено.")
    bot.delete_state(message.from_user.id, message.chat.id)

#Функция поиска команд в сообщении
def findComands(message):
    if message.text==('/start') or message.text==('/help') :
        return True
    else:
        return False

#Получение клавиатуры с отправкой телефона
def getSendPhoneKeyboard():
    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True) 
    button_phone = types.KeyboardButton(text=_("Send phone number"), request_contact=True)
    keyboard.add(button_phone)
    return keyboard


bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.add_custom_filter(custom_filters.IsDigitFilter())

bot.infinity_polling(skip_pending=True)
