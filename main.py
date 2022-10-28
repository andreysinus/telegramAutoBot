
import telebot
import serverFuncs
from telebot import types
import urllib
import configure 

#Инициализация бота
bot = telebot.TeleBot(configure.config['token'])

#Адреса WebApps-ов
webAppNewDamage = "https://mellow-bombolone-bcb5a7.netlify.app/"
webAppPretrip = "https://super-kataifi-b967c7.netlify.app/"

#Настройка "Menu" в боте
bot.set_my_commands([
    telebot.types.BotCommand("/start", "Перезапуск бота"),
    telebot.types.BotCommand("/help", "Помощь")
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


#Клавиатура действий
def createInlineKeyboardWithFuncs():
    inlineKeyboard = types.InlineKeyboardMarkup(row_width=1)
    btns=[
            types.InlineKeyboardButton(text="Предрейсовый осмотр", callback_data="pretrip_inspect"),
            types.InlineKeyboardButton(text="Приёмка автомобиля", callback_data="car_acceptance"),
            types.InlineKeyboardButton(text="Выход", callback_data="to_start")
    ] 
    inlineKeyboard.add(*btns)
    return inlineKeyboard


#Стартовое сообщение
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        msg = bot.reply_to (message, """
        Здравствуйте! \nДля начала работы пройдите авторизацию.
        """, reply_markup='')
        chat_id = message.chat.id
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True) 
        button_phone = types.KeyboardButton(text="Отправить телефонный номер", request_contact=True)
        keyboard.add(button_phone)
        bot.send_message(chat_id, "Нажмите кнопку внизу экрана или отправьте номер телефона (напр. 79998887766) в сообщении:", reply_markup=keyboard)
        bot.register_next_step_handler(msg, process_check_phone)
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)

#Сообщение с помощью
@bot.message_handler(commands=['help'])
def send_help(message):
    try:
        chat_id = message.chat.id
        msg = bot.reply_to (message, """
        Для начала работ необходимо произвести авторизацию с помощью своего мобильного телефона!
        \nДалее требуется выбрать необходимую операцию (например,\"Предрейсовый осмотр\". 
        \nПосле выбора нужно следовать инструкциям бота.
        \nПри технический неполадках обратиться по номеру:\n8 (800) 101-40-64, горячая линия техподдержки АТИМО.
        """, reply_markup='')
        if chat_id in user_dict:
             msg=bot.send_message(chat_id, f"{user_dict[chat_id].name}, выберите действие.", reply_markup=createInlineKeyboardWithFuncs())
        else:
             send_welcome(msg)
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)


#Функция поиска команд в сообщении
def findComands(message):
    if message.text==('/start') or message.text==('/help') :
        return True
    else:
        return False


#Проверка телефонного номера механика
def process_check_phone(message):
    try:
        chat_id = message.chat.id
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if findComands(message)==False:
            if message.text == "Добавить водителя":
                button_phone = types.KeyboardButton(text="Отправить телефонный номер", request_contact=True)
                keyboard.add(button_phone)
                bot.send_message(chat_id, "Нажмите кнопку внизу экрана или отправьте номер телефона (напр. 79998887766) в сообщении:")

                #Поменять при необходимости
                msg=bot.send_message(chat_id, "Команда не доработана.")
                restart(msg)
                return
            
            if message.contact is not None:
                contacts=serverFuncs.checkUser(message.contact.phone_number)
                if (contacts[0]):
                    user= User(message.text)
                    user.name=contacts[1]
                    user.base_address=contacts[2]
                    user_dict[chat_id] = user
                    msg=bot.send_message(chat_id, f"{contacts[1]}, выберите действие.", reply_markup=createInlineKeyboardWithFuncs())
                else:
                    button_phone = types.KeyboardButton(text="Отправить телефонный номер", request_contact=True)
                    msg=bot.send_message(chat_id, "Сотрудник отсутствует в базе, введите номер телефона еще раз.", reply_markup=keyboard)
                    bot.register_next_step_handler(msg, process_check_phone)
            else:
                contacts=serverFuncs.checkUser(message.text)
                if (contacts[0]):
                    user= User(message.text)
                    user.name=contacts[1]
                    user.base_address=contacts[2]
                    user_dict[chat_id] = user
                    msg=bot.send_message(chat_id, f"{contacts[1]}, выберите действие.", reply_markup=createInlineKeyboardWithFuncs())
                else:
                    if (message.text!="/start"):
                        button_phone = types.KeyboardButton(text="Отправить телефонный номер", request_contact=True)
                        msg=bot.send_message(chat_id, "Сотрудник отсутствует в базе, введите номер телефона еще раз.", reply_markup=keyboard)
                        bot.register_next_step_handler(msg, process_check_phone)
                    else:
                        msg=bot.send_message(chat_id, "Перезагрузка.")
                        send_welcome(msg)
        else:
            if message.text=="/help":
                send_help(message)
            else: 
                restart(message);
            return
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)

#Обработка выбора функции
@bot.callback_query_handler(func=lambda call: True)
def process_choose_func(call):
    try:
        chat_id=call.message.chat.id
        if call.data == 'car_acceptance':
            msg= bot.send_message(chat_id, "Введите номер автомобиля")
            bot.register_next_step_handler(msg, process_car_accept)
        else:
            if call.data == 'pretrip_inspect':
                msg= bot.send_message(chat_id, "Введите телефон водителя")
                bot.register_next_step_handler(msg, process_car_inspection)
            else:
                if call.data == 'to_start':
                    msg=bot.send_message(chat_id, "Выход")
                    restart(msg)
        return
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)

# Приёмка авто - Проверка авто
def process_car_accept(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        carInfo=serverFuncs.checkGRZ(message.text, user.base_address)
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if findComands(message)==False:
            if (carInfo[1]!=None):
                if (carInfo[2]!=None):
                    keyboard.add("Да", "Нет")
                    user.plates=message.text
                    user.driver=carInfo[2]
                    user.aktNumber=carInfo[3]
                    msg= bot.send_message(chat_id, f"Водитель \"{carInfo[2]}\" сдаёт автомобиль, выданный по акту №{carInfo[3]}?",reply_markup=keyboard )
                    bot.register_next_step_handler(msg, process_car_accept_check)
                else:
                    bot.send_message(chat_id, "Водитель не найден. Проверьте введенные данные")
                    #Replace
                    msg=bot.send_message(chat_id, f"{user.name}, выберите действие.", reply_markup=createInlineKeyboardWithFuncs())
            else:
                bot.send_message(chat_id, "Автомобиль не найден. Проверьте введенные данные")
                #Replace
                msg=bot.send_message(chat_id, f"{user.name}, выберите действие.", reply_markup=createInlineKeyboardWithFuncs())
        else:
            if message.text=="/help":
                send_help(message)
            else: 
                restart(message);
            return
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)


#Приёмка авто - проверка пробега
def process_car_accept_check(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        if findComands(message)==False:
            if message.text=="Да":
                msg=bot.send_message(chat_id, "Введите пробег автомобиля", reply_markup=types.ReplyKeyboardRemove())
                bot.register_next_step_handler(msg, process_car_odometer_check)
            elif message.text=="Нет":
                msg=bot.send_message(chat_id, "Вы отказались от действия", reply_markup=types.ReplyKeyboardRemove())
                msg=bot.send_message(chat_id, f"{user.name}, выберите действие.", reply_markup=createInlineKeyboardWithFuncs())
            else:
                msg = bot.send_message(chat_id, "Команда не найдена")
                restart(msg)
        else:
            if message.text=="/help":
                send_help(message)
            else: 
                restart(message);
            return
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)
        
#Приёмка авто - проверка пробега и открытие WebApp 
def process_car_odometer_check(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]

        #Добавить обработку пробега из базы
        odometerValue=123908
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if findComands(message)==False:
            #Настроить условия
            if int(message.text)>odometerValue-500 and int(message.text)<odometerValue+500 :
                bot.reply_to(message, "Пробег соответствует условиям")
                user.odometer=int(message.text)
                x=urllib.parse.quote(user.plates)
                url=types.WebAppInfo(webAppNewDamage+"?grz="+x+"&telephone="+user.phoneNumber+"&base="+urllib.parse.quote(user.base_address));
                #
                button = types.KeyboardButton(text="Сформировать акт", web_app=url)
                keyboard.add(button)
                msg=bot.send_message(chat_id, "Далее необходимо сформировать акт", reply_markup=keyboard)
            elif message.text!="/start":
                bot.reply_to(message, "Пробег не соответствует условиям")
                msg = bot.send_message(chat_id, "Введите пробег еще раз")
                bot.register_next_step_handler(msg, process_car_odometer_check)
            else:
                restart(message)
        else:
            if message.text=="/help":
                send_help(message)
            else: 
                restart(message);
            return
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)

#Предрейсовый осмотр - ввод номера телефона водителя
def process_car_inspection(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        if findComands(message)==False:
            if message.text!="Назад" or message.text!="Отмена":
                driverInfo=serverFuncs.getDriver(message.text)
                if driverInfo==True:
                    user.voditel=message.text
                    msg=bot.send_message(chat_id, f"Введите номер автомобиля.")
                    bot.register_next_step_handler(msg, process_car_inspection_grz)
                else: 
                    msg=bot.send_message(chat_id, f"Водитель не найден, введите другой номер телефона.")
                    bot.register_next_step_handler(msg, process_car_inspection)
            else:
                msg=bot.send_message(chat_id, f"{user.name}, выберите действие.", reply_markup=createInlineKeyboardWithFuncs())
        else:
            if message.text=="/help":
                send_help(message)
            else: 
                restart(message);
            return

    except Exception as e:
         msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
         restart(msg)

#Предрейсовый осмотр - ввод номера автомобиля
def process_car_inspection_grz(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        if findComands(message)==False:
            if message.text!="Назад" or message.text!="Отмена":
                carInfo=serverFuncs.getCar(message.text)
                if carInfo==True:
                    user.plates=message.text
                    msg=bot.send_message(chat_id, f"Введите пробег.")
                    bot.register_next_step_handler(msg, process_car_inspection_odometer)
                else: 
                    msg=bot.send_message(chat_id, f"Авто не найден, введите другой номер.")
                    bot.register_next_step_handler(msg, process_car_inspection_grz)
            else:
                msg=bot.send_message(chat_id, f"{user.name}, выберите действие.", reply_markup=createInlineKeyboardWithFuncs())
        else:
            if message.text=="/help":
                send_help(message)
            else: 
                restart(message);
            return
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)


#Предрейсовый осмотр - ввод пробега и вывод кнопок с WebApp 
def process_car_inspection_odometer(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if findComands(message)==False:
            if message.text!="Назад" or message.text!="Отмена":
                carInfo=serverFuncs.getOdometer(user.plates)
                if carInfo[0]==True and (carInfo[1]<int(message.text)+100 and carInfo[1]>int(message.text)-100):
                    x=urllib.parse.quote(user.plates)
                    url=types.WebAppInfo(webAppPretrip+"?grz="+x+"&mechPhone="+user.phoneNumber+"&driverPhone="+user.voditel+"&odo="+carInfo[1]+"&base="+urllib.parse.quote(user.base_address));
                    button = types.KeyboardButton(text="Проверка авто", web_app=url)
                    keyboard.add(button)
                    msg=bot.send_message(chat_id, f"Для прохождения листа проверок нажмите на кнопку \"Проверка авто\"", reply_markup=keyboard)
                else: 
                    msg=bot.send_message(chat_id, f"Пробег не корректный, введите заново.")
                    bot.register_next_step_handler(msg, process_car_inspection_odometer)
            else:
                msg=bot.send_message(chat_id, f"{user.name}, выберите действие.", reply_markup=createInlineKeyboardWithFuncs())
        else:
            if message.text=="/help":
                send_help(message)
            else: 
                restart(message);
            return
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)


#Обработка результата WebApps-ов
@bot.message_handler(content_types="web_app_data")
def webAppAnswer(webAppMes):
    try:
        if webAppMes.web_app_data.data=="Акт был сформирован" :
            bot.send_message(webAppMes.chat.id, f"Акт был сформирован. Выберите действие.", reply_markup=createInlineKeyboardWithFuncs())    
        else: bot.send_message(webAppMes.chat.id, f"Ошибка! {webAppMes.web_app_data.data}", reply_markup=createInlineKeyboardWithFuncs())  
    except Exception as e:
        msg=bot.send_message(webAppMes.chat.id, 'Упс. Что-то пошло не так')
        restart(msg)

#Функция перезагрузки бота.
def restart(message):
    chat_id=message.chat.id
    msg=bot.send_message(chat_id, "Перезапуск.")
    send_welcome(msg)


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
bot.infinity_polling()