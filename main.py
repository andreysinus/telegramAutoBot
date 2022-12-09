
import telebot 
from telebot import types
import serverFuncs
import urllib
import configure 
import gettext

#Инициализация бота
bot = telebot.TeleBot(configure.config['token'])

ru=gettext.translation('messages', localedir='localization', languages=['ru_RU'])
en=gettext.translation('messages', localedir='localization', languages=['en'])
en.install()

#Настройка "Menu" в боте
bot.set_my_commands([
    telebot.types.BotCommand("/start", "Restart"),
    telebot.types.BotCommand("/help", "Help"),
    telebot.types.BotCommand("/changelanguage", "Change language")
])
reply_markup=types.ReplyKeyboardRemove()


#Словарь с данными о пользователе и введенных им значений.
user_dict = {}
class User:
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

#
user_lang = {}

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

def checkLang(message):
    if message.from_user.language_code=="ru":
        user_lang[message.chat.id]=1
        ru.install()
    else:
        user_lang[message.chat.id]=2
        en.install()
    return True

def changeLanguage(message):
    if user_lang[message.chat.id]==1:
        user_lang[message.chat.id]=2
        en.install()
        msg= bot.send_message(message.chat.id,"Language changed to English")
        restart(msg)
    else:
        user_lang[message.chat.id]=1
        ru.install()
        msg= bot.send_message(message.chat.id,"Язык изменен на русский")
        restart(msg)

#Стартовое сообщение
@bot.message_handler(commands=['start'], func=checkLang)
def send_welcome(message):
        msg = bot.reply_to (message, _("Hello! \nPlease login to get started."), reply_markup='')
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True) 
        button_phone = types.KeyboardButton(text=_("Send phone number"), request_contact=True)
        keyboard.add(button_phone)
        bot.send_message(message.chat.id,_("Press the button at the bottom of the screen or send a phone number (ex. 79998887766) in a message:"), reply_markup=keyboard)
        bot.register_next_step_handler(msg, process_check_phone)

#Сообщение с помощью
@bot.message_handler(commands=['help'])
def send_help(message):
    try:
        chat_id = message.chat.id
        msg = bot.reply_to (message, _("""
        To start work, you need to authorize using your mobile phone!
        \nNext, you need to select the required operation (for example, \"Pretrip inspection\".
        \nAfter choosing, follow the bot's instructions.
        \nIn case of technical problems, contact:\n8 (800) 101-40-64, ATIMO technical support hotline.
        """), reply_markup='')
        if chat_id in user_dict:
             msg=bot.send_message(chat_id, f"{user_dict[chat_id].name}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
        else:
             send_welcome(msg)
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))
        restart(msg)


#Функция поиска команд в сообщении
def findComands(message):
    if message.text==('/start') or message.text==('/help') or message.text==('/changelanguage'):
        return True
    else:
        return False


#Проверка телефонного номера механика
def process_check_phone(message):
    try:
        chat_id = message.chat.id
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if findComands(message)==False:
            if message.contact is not None:
                contacts=serverFuncs.checkUser(message.contact.phone_number)
                if (contacts[0]):
                    user= User(message.contact.phone_number)
                    user.name=contacts[1]
                    user.base_address=contacts[2]
                    user_dict[chat_id] = user
                    msg=bot.send_message(chat_id, f"{contacts[1]}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
                else:
                    button_phone = types.KeyboardButton(text=_("Send phone number"), request_contact=True)
                    msg=bot.send_message(chat_id, _("The employee is not in the database, enter the phone number again."), reply_markup=keyboard)
                    bot.register_next_step_handler(msg, process_check_phone)
            else:
                contacts=serverFuncs.checkUser(message.text)
                if (contacts[0]):
                    user= User(message.text)
                    user.name=contacts[1]
                    user.base_address=contacts[2]
                    user_dict[chat_id] = user
                    msg=bot.send_message(chat_id, f"{contacts[1]}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
                else:
                    if (message.text!="/start"):
                        button_phone = types.KeyboardButton(text=_("Send phone number"), request_contact=True)
                        msg=bot.send_message(chat_id, _("The employee is not in the database, enter the phone number again."), reply_markup=keyboard)
                        bot.register_next_step_handler(msg, process_check_phone)
                    else:
                        msg=bot.send_message(chat_id, _("Restart."))
                        send_welcome(msg)
        else:
            if message.text=="/help":
                send_help(message)
            elif message.text=="/changelanguage":
                changeLanguage(message)
            else: 
                restart(message);
            return
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))
        restart(msg)

#Обработка выбора функции
@bot.callback_query_handler(func=lambda call: True)
def process_choose_func(call):
    try:
        chat_id=call.message.chat.id
        if call.data == 'car_acceptance':
            msg= bot.send_message(chat_id, _("Enter vehicle number"))
            bot.register_next_step_handler(msg, process_car_accept)
        else:
            if call.data == 'pretrip_inspect':
                msg= bot.send_message(chat_id, _("Enter the driver's phone number"))
                bot.register_next_step_handler(msg, process_car_inspection)
            else:
                if call.data == 'to_start':
                    msg=bot.send_message(chat_id, _("Exit"))
                    restart(msg)
        return
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))
        restart(msg)

# Приёмка авто - Проверка авто
def process_car_accept(message):
    #try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        carInfo=serverFuncs.checkGRZ(message.text, user.base_address)
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if findComands(message)==False:
            if (carInfo[1]!=None):
                if (carInfo[2]!=None):
                    keyboard.add(_("Yes"), _("No"))
                    user.plates=message.text
                    user.driver=carInfo[2]
                    user.aktNumber=carInfo[3]
                    msg= bot.send_message(chat_id, _("The driver")+f" \"{carInfo[2]}\" "+_("hands over the car issued under the act No.")+ carInfo[3]+ "?",reply_markup=keyboard )
                    bot.register_next_step_handler(msg, process_car_accept_check)
                else:
                    bot.send_message(chat_id, _("Driver not found. Check the entered data"))
                    #Replace
                    msg=bot.send_message(chat_id, f"{user.name}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
            else:
                bot.send_message(chat_id, _("Vehicle not found. Check the entered data"))
                #Replace
                msg=bot.send_message(chat_id, f"{user.name}, "+ _("select an action."), reply_markup=createInlineKeyboardWithFuncs())
        else:
            if message.text=="/help":
                send_help(message)
            elif message.text=="/changelanguage":
                changeLanguage(message)
            else: 
                restart(message);
            return
    #except Exception as e:
     #   msg=bot.send_message(chat_id, _('Oops. Something went wrong'))
      #  restart(msg)


#Приёмка авто - проверка пробега
def process_car_accept_check(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        if findComands(message)==False:
            if message.text=="Да" or message.text=="Yes":
                msg=bot.send_message(chat_id, _("Enter vehicle mileage"), reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(msg, process_car_odometer_check)
            elif message.text=="Нет" or message.text=="No":
                msg=bot.send_message(chat_id, _("You abandoned the action"), reply_markup=types.ReplyKeyboardRemove())
                msg=bot.send_message(chat_id, f"{user.name}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
            else:
                msg = bot.send_message(chat_id, _("Command not found"))
                restart(msg)
        else:
            if message.text=="/help":
                send_help(message)
            elif message.text=="/changelanguage":
                changeLanguage(message)
            else: 
                restart(message);
            return
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))
        restart(msg)
        
#Приёмка авто - проверка пробега и открытие WebApp 
def process_car_odometer_check(message):
    #try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        odometerValue=serverFuncs.getOdometer(user.plates)
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if odometerValue[0]==True and findComands(message)==False:
            #Настроить условия
            if int(message.text)>int(odometerValue[1])-500 and int(message.text)<int(odometerValue[1])+2000 :
                bot.reply_to(message, _("Mileage meets conditions"))
                user.odometer=int(message.text)
                x=urllib.parse.quote(user.plates)
                url=types.WebAppInfo(configure.config['webAppNewDamage']+"?grz="+x+"&telephone="+user.phoneNumber+"&base="+urllib.parse.quote(user.base_address));
                #
                button = types.KeyboardButton(text=_("Form an act"), web_app=url)
                keyboard.add(button)
                msg=bot.send_message(chat_id, _("Next, you need to create an act"), reply_markup=keyboard)
            elif message.text!="/start":
                bot.reply_to(message, _("Mileage does not meet conditions"))
                msg = bot.send_message(chat_id, _("Enter mileage again"))
                bot.register_next_step_handler(msg, process_car_odometer_check)
            else:
                restart(message)
        else:
            if message.text=="/help":
                send_help(message)
            elif message.text=="/changelanguage":
                changeLanguage(message)
            else: 
                restart(message);
            return
    #except Exception as e:
     #   msg=bot.send_message(chat_id, _('Oops. Something went wrong'))
      #  restart(msg)

#Предрейсовый осмотр - ввод номера телефона водителя
def process_car_inspection(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        if findComands(message)==False:
            if message.text!="Назад" or message.text!="Отмена" or message.text!="Cancel" or message.text!="Back":
                driverInfo=serverFuncs.getDriver(message.text)
                if driverInfo==True:
                    user.voditel=message.text
                    msg=bot.send_message(chat_id, _("Enter the vehicle number."))
                    bot.register_next_step_handler(msg, process_car_inspection_grz)
                else: 
                    msg=bot.send_message(chat_id, _("Driver not found, please enter a different phone number."))
                    bot.register_next_step_handler(msg, process_car_inspection)
            else:
                msg=bot.send_message(chat_id, f"{user.name}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
        else:
            if message.text=="/help":
                send_help(message)
            elif message.text=="/changelanguage":
                changeLanguage(message)
            else: 
                restart(message);
            return

    except Exception as e:
         msg=bot.send_message(chat_id, _('Oops. Something went wrong'))
         restart(msg)

#Предрейсовый осмотр - ввод номера автомобиля
def process_car_inspection_grz(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        if findComands(message)==False:
            if message.text!="Назад" or message.text!="Отмена" or message.text!="Cancel" or message.text!="Back":
                carInfo=serverFuncs.getCar(message.text)
               
                if carInfo==True:
                    user.plates=message.text
                    msg=bot.send_message(chat_id, _("Enter mileage"))
                    bot.register_next_step_handler(msg, process_car_inspection_odometer)
                else: 
                    msg=bot.send_message(chat_id, _("Vehicle not found, please enter another number"))
                    bot.register_next_step_handler(msg, process_car_inspection_grz)
            else:
                msg=bot.send_message(chat_id, f"{user.name}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
        else:
            if message.text=="/help":
                send_help(message)
            elif message.text=="/changelanguage":
                changeLanguage(message)
            else: 
                restart(message);
            return
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))
        restart(msg)


#Предрейсовый осмотр - ввод пробега и вывод кнопок с WebApp 
def process_car_inspection_odometer(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if findComands(message)==False:
            if message.text!="Назад" or message.text!="Отмена" or message.text!="Cancel" or message.text!="Back":
                carInfo=serverFuncs.getOdometer(user.plates)
                if carInfo[0]==True and (carInfo[1]<int(message.text)):
                    x=urllib.parse.quote(user.plates)
                    url=types.WebAppInfo(configure.config['webAppPretrip']+"?grz="+str(x)+"&mechPhone="+str(user.phoneNumber)+"&driverPhone="+str(user.voditel)+"&odo="+str(message.text)+"&base="+urllib.parse.quote(user.base_address));
                    print(url)
                    button = types.KeyboardButton(text=_("Car check"), web_app=url)
                    keyboard.add(button)
                    msg=bot.send_message(chat_id, _("To go through the list of checks, click on the button \"Car check\""), reply_markup=keyboard)
                else: 
                    msg=bot.send_message(chat_id, _("Mileage is not correct, please re-enter"))
                    bot.register_next_step_handler(msg, process_car_inspection_odometer)
            else:
                msg=bot.send_message(chat_id, f"{user.name}, "+_("select an action."), reply_markup=createInlineKeyboardWithFuncs())
        else:
            if message.text=="/help":
                send_help(message)
            elif message.text=="/changelanguage":
                changeLanguage(message)
            else: 
                restart(message);
            return
    except Exception as e:
        msg=bot.send_message(chat_id, _('Oops. Something went wrong'))
        restart(msg)


#Обработка результата WebApps-ов
@bot.message_handler(content_types="web_app_data")
def webAppAnswer(webAppMes):
    try:
        if webAppMes.web_app_data.data=="Акт был сформирован" :
            bot.send_message(webAppMes.chat.id, _("The act has been formed."), reply_markup=types.ReplyKeyboardRemove())    
            bot.send_message(webAppMes.chat.id, _("Select an action."), reply_markup=createInlineKeyboardWithFuncs())    
        else: 
            bot.send_message(webAppMes.chat.id, _("Error!"), reply_markup=types.ReplyKeyboardRemove())  
            bot.send_message(webAppMes.chat.id, f"{webAppMes.web_app_data.data}", reply_markup=createInlineKeyboardWithFuncs())  
    except Exception as e:
        msg=bot.send_message(webAppMes.chat.id, _('Oops. Something went wrong'))
        restart(msg)

#Функция перезагрузки бота.
def restart(message):
    chat_id=message.chat.id
    msg=bot.send_message(chat_id, _("Restart."))
    send_welcome(msg)


bot.enable_save_next_step_handlers(delay=0)
bot.load_next_step_handlers()
bot.infinity_polling()