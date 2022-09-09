import telebot
import serverFuncs
from telebot import types
import urllib
import configure 

bot = telebot.TeleBot(configure.config['token'])

webAppSignature = types.WebAppInfo("https://remarkable-daifuku-2f8ee5.netlify.app/")
webAppNewDamage = "https://mellow-bombolone-bcb5a7.netlify.app/"

bot.set_my_commands([
    telebot.types.BotCommand("/start", "Перезапуск бота"),
    telebot.types.BotCommand("/help", "Помощь")
])
reply_markup=types.ReplyKeyboardRemove()

user_dict = {}
class User:
    def __init__(self, phNumber):
        self.phoneNumber = phNumber
        self.name = None
        self.driver = None
        self.plates = None
        self.aktNumber = None 
        self.odometer = None
        self.crashes=None
        self.base_address=None
#
def send_help(message):
    chat_id=message.chat.id
    bot.send_message(chat_id, "Помощь:")
#Клавиатура действий
def createInlineKeyboardWithFuncs():
    inlineKeyboard = types.InlineKeyboardMarkup(row_width=1)
    btns=[
            types.InlineKeyboardButton(text="Предрейсовый осмотр(не работает)", callback_data="pretrip_inspect"),
            types.InlineKeyboardButton(text="Приёмка автомобиля", callback_data="car_acceptance"),
            types.InlineKeyboardButton(text="Выход", callback_data="to_start")
    ] 
    inlineKeyboard.add(*btns)
    return inlineKeyboard


#
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

#
def process_check_phone(message):
    try:
        chat_id = message.chat.id
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if message.text != "/start":
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
                    keyboard.add(button_phone, "Добавить нового водителя")
                    msg=bot.send_message(chat_id, "Сотрудник отсутствует в базе, введите номер телефона еще раз или добавьте нового.", reply_markup=keyboard)
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
                        keyboard.add(button_phone, "Добавить нового водителя")
                        msg=bot.send_message(chat_id, "Сотрудник отсутствует в базе, введите номер телефона еще раз или добавьте нового.", reply_markup=keyboard)
                        bot.register_next_step_handler(msg, process_check_phone)
                    else:
                        msg=bot.send_message(chat_id, "Перезагрузка.")
                        send_welcome(msg)
        else: 
            msg=bot.send_message(chat_id, "Перезагрузка.")
            send_welcome(msg)
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)

@bot.callback_query_handler(func=lambda call: True)
def process_choose_func(call):
    try:
        chat_id=call.message.chat.id
        if call.data == 'car_acceptance':
            msg= bot.send_message(chat_id, "Введите номер автомобиля")
            bot.register_next_step_handler(msg, process_car_accept)
        else:
            if call.data == 'pretrip_inspect':
                msg=bot.send_message(chat_id, "Тест! Не работает!")
                restart(msg)
            else:
                if call.data == 'to_start':
                    msg=bot.send_message(chat_id, "Выход")
                    restart(msg)
        return
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)

def process_car_accept(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        carInfo=serverFuncs.checkGRZ(message.text, user.base_address)
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        
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
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)



def process_car_accept_check(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        if message.text=="Да":
            msg=bot.send_message(chat_id, "Введите пробег автомобиля", reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, process_car_odometer_check)
        elif message.text=="Нет":
            msg=bot.send_message(chat_id, "Вы отказались от действия", reply_markup=types.ReplyKeyboardRemove())
            msg=bot.send_message(chat_id, f"{user.name}, выберите действие.", reply_markup=createInlineKeyboardWithFuncs())
        else:
            msg = bot.send_message(chat_id, "Команда не найдена")
            restart(msg)
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)
        
def process_car_odometer_check(message):
    #try:
        chat_id=message.chat.id
        user = user_dict[chat_id]

        #Добавить обработку пробега из базы
        odometerValue=123908
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)

        #Настроить условия
        if int(message.text)>odometerValue-500 and int(message.text)<odometerValue+500 :
            bot.reply_to(message, "Пробег соответствует условиям")
            user.odometer=int(message.text)
            #Добавить обработку существующих повреждений
            crash=False
            user.crashes=crash
            if crash == False:
                
                x=urllib.parse.quote(user.plates)
                url=types.WebAppInfo(webAppNewDamage+"?grz="+x+"&telephone="+user.phoneNumber+"&base="+urllib.parse.quote(user.base_address));
                #
                button = types.KeyboardButton(text="Сформировать акт", web_app=url)
                keyboard.add(button)
                msg=bot.send_message(chat_id, "Далее необходимо сформировать акт", reply_markup=keyboard)
            else:
                keyboard.add("Просмотреть", "Добавить", "Не добавлять")
                msg=bot.send_message(chat_id, "У автомобиля есть записанные повреждения, хотите просмотреть или добавить новое?", reply_markup=keyboard)
                bot.register_next_step_handler(msg,process_check_damage)
        elif message.text!="/start":
            bot.reply_to(message, "Пробег не соответствует условиям")
            msg = bot.send_message(chat_id, "Введите пробег еще раз")
            bot.register_next_step_handler(msg, process_car_odometer_check)
        else:
            restart(message)
    #except Exception as e:
    #    msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
    #    restart(msg)


def process_check_damage(message):
    try:
        chat_id=message.chat.id
        user = user_dict[chat_id]
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        if message.text=="Не добавлять":
            button = types.KeyboardButton(text="Поставить подпись", web_app=webAppSignature)
            keyboard.add(button)
            msg = bot.send_message(chat_id, "Далее необходимо поставить подпись на экране, нажав на кнопку \"Поставить подпись\"",reply_markup=keyboard)
        elif message.text=="Повреждения были отправлены":
            msg = bot.send_message(chat_id, "Выполняется добавление повреждений")
        elif message.text=="Просмотреть":
            if user.crashes==True:
                msg = bot.send_message(chat_id, "Пока не работает")
            else:
                msg = bot.send_message(chat_id, "Повреждений нет")
        elif message.text=="/start":
            restart(message)
        else:
            msg = bot.send_message(chat_id, "Команда не найдена")
            restart(msg)
    except Exception as e:
        msg=bot.send_message(chat_id, 'Упс. Что-то пошло не так')
        restart(msg)


@bot.message_handler(content_types="web_app_data")
def webAppAnswer(webAppMes):
    try:
        if webAppMes.web_app_data.data=="Акт был сформирован" :
            bot.send_message(webAppMes.chat.id, f"Акт был сформирован. Выберите действие.", reply_markup=createInlineKeyboardWithFuncs())    
        else: bot.send_message(webAppMes.chat.id, f"Ошибка! {webAppMes.web_app_data.data}", reply_markup=createInlineKeyboardWithFuncs())  
    except Exception as e:
        msg=bot.send_message(webAppMes.chat.id, 'Упс. Что-то пошло не так')
        restart(msg)


def restart(message):
    chat_id=message.chat.id
    msg=bot.send_message(chat_id, "Перезапуск.")
    send_welcome(msg)


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()
bot.infinity_polling()