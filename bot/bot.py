import logging
import re, os
import paramiko
from dotenv import load_dotenv
import psycopg2
from psycopg2 import Error
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

load_dotenv()

#токен бота
TOKEN = os.getenv("TOKEN")


# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, encoding="utf-8"
)

logger = logging.getLogger(__name__)

# функция приветствия
def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')

# меню помощи со всеми командами    
def helpCommand(update: Update, context):
    helptext = "/find_phone_number - команда для поиска номеров телефонов \n /find_email - команда для поиска электронных почт \n /verify_password - команда проверки сложности пароля \n \n Команды для SSH подключения: \n /get_release - cбор информации о релизе \n /get_uname - сбор информации об архитектуре процессора, имени хоста системы и версии ядра \n /get_uptime - cбор информации о времени работы \n /get_df - cбор информации о состоянии файловой системы \n /get_free - cбор информации о состоянии оперативной памяти \n /get_mpstat - cбор информации о производительности системы \n /get_w - cбор информации о работающих в данной системе пользователях \n /get_auths - сбор логов о последних 10 входах в систему \n /get_critical - сбор логов о последних 5 критических событиях \n /get_ps - cбор информации о запущенных процессах \n /get_ss - cбор информации об используемых портах \n /get_apt_list - cбор информации об установленных пакетах \n /get_services - cбор информации о запущенных сервисах \n \n Команды для репликации: \n /get_repl_logs - вывод логов о репликации \n /get_emails - вывод данных о email-адресах из таблиц \n /get_phone_numbers - вывод данных о номерах телефонов из таблиц             "
    update.message.reply_text(helptext)

# функция вызова сообщения о готовности к вводу текста, в котором будет поиск номеров телефонов
def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_number'

# функция вызова сообщения о готовности к вводу текста, в котором будет поиск электронных почт
def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска электронных почт: ')

    return 'find_email'

# функция вызова сообщения о готовности к вводу текста, в котором будет простой или сложный пароль
def verifyPasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль: ')

    return 'verify_password'

# функция поиска номеров телефонов в сообщении
def findPhoneNumbers (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) номера телефонов

    phoneNumRegex = re.compile(r'(?:\+7|8)(?: \(\d{3}\) \d{3}-\d{2}-\d{2}|\d{10}|\(\d{3}\)\d{7}| \d{3} \d{3} \d{2} \d{2}| \(\d{3}\) \d{3} \d{2} \d{2}|-\d{3}-\d{3}-\d{2}-\d{2})') # регулярное выражение для номеров

    phoneNumberList = phoneNumRegex.findall(user_input) # Ищем номера телефонов

    if not phoneNumberList: # Обрабатываем случай, когда номеров телефонов нет
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END # Завершаем работу обработчика диалога
    
    phoneNumbers = '' # Создаем строку, в которую будем записывать номера телефонов
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n' # Записываем очередной номер
    
    phoneNumbers += "Информация найдена. Записать её в базу данных? Введите 'да' и информация будет записана, либо введите любой другой текст и она не будет записана"
    
    update.message.reply_text(phoneNumbers) # Отправляем сообщение пользователю
    context.chat_data['phone_numbers'] = phoneNumberList
    return 'find_phone_number2'  # Переход в новый диалог
    

# функция записи номеров телефонов
def findPhoneNumbers2 (update: Update, context):
    user_input = update.message.text # Получаем текст
    if user_input == "да":
        phone_numbers = context.chat_data.get('phone_numbers')
        formatted_phones = ', '.join([f"('{phone}')" for phone in phone_numbers]) # преобразовывает в вид ('8-800-555-35-35'), ('+7-(800)-555-35-35')
        StringForINSERT1 = "INSERT INTO phones (номер) VALUES "
        StringForINSERT2 = ';'
        StringForINSERT = StringForINSERT1 + formatted_phones + StringForINSERT2
        a = DbINSERT(StringForINSERT) 
        if a == None:
            update.message.reply_text("Ошибка при работе с PostgreSQL")
        update.message.reply_text(a)
    else:
        update.message.reply_text("Вы решили не записывать номера телефонов в базу данных") # Отправляем сообщение пользователю
    return ConversationHandler.END # Завершаем работу обработчика диалога

# функция поиска почт в сообщении
def findEmail (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий(или нет) электронные почты

    EmailRegex = re.compile(r'\b([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)\b') #это регулярное выражение для почт

    EmailList = EmailRegex.findall(user_input) # Ищем электронные почты

    if not EmailList: # Обрабатываем случай, когда электронных почт нет
        update.message.reply_text('Электронные почты не найдены')
        return ConversationHandler.END # Завершаем работу обработчика диалога
    
    Emails = '' # Создаем строку, в которую будем записывать электронные почты
    for i in range(len(EmailList)):
        Emails += f'{i+1}. {EmailList[i]}\n' # Записываем очередной номер электронной почты
    
    Emails += "Информация найдена. Записать её в базу данных? Введите 'да' и информация будет записана, либо введите любой другой текст и она не будет записана"

    update.message.reply_text(Emails) # Отправляем сообщение пользователю
    context.chat_data['email_numbers'] = EmailList
    return 'find_email2' # Переход в новый диалог

# функция записи почт
def findEmail2 (update: Update, context):
    user_input = update.message.text # Получаем текст
    if user_input == "да":
        email_numbers = context.chat_data.get('email_numbers')
        formatted_email = ', '.join([f"('{email}')" for email in email_numbers]) # преобразовывает в вид ('pt@ya.ru'), ('start@google.com')
        StringForINSERT1 = "INSERT INTO emails (почта) VALUES "
        StringForINSERT2 = ';'
        StringForINSERT = StringForINSERT1 + formatted_email + StringForINSERT2
        a = DbINSERT(StringForINSERT) 
        if a == None:
            update.message.reply_text("Ошибка при работе с PostgreSQL")
        update.message.reply_text(a)
    else:
        update.message.reply_text("Вы решили не записывать номера почт в базу данных") # Отправляем сообщение пользователю
    return ConversationHandler.END # Завершаем работу обработчика диалога


# функция верификации пароля
def verifyPassword (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий пароль

    PasswordRegex = re.compile(r'((?=.*[0-9])(?=.*[!@#$%^&*])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*]{8,})') #это регулярное выражение для сложного пароля

    PasswordStatus = PasswordRegex.match(user_input) # верифицируем пароль

    if PasswordStatus: # если верификация прошла по всем пунктам
        PasswordStatusText = "Сложный пароль"
    else: # иначе
        PasswordStatusText = "Простой пароль"
    
    update.message.reply_text(PasswordStatusText) # Отправляем сообщение пользователю
    return ConversationHandler.END # Завершаем работу обработчика диалога

# функция эхо
def echo(update: Update, context):
    update.message.reply_text(update.message.text)

# функция подключения к linux машине. Подключение будет осуществляться после того, как мы будем знать какую конкретно linux команду нужно применить
def ParamikoConnection (my_linux_command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=os.getenv('RM_HOST'), username=os.getenv('RM_USERNAME'), password=os.getenv('RM_PASSWORD'), port=os.getenv('RM_PORT')) 
    stdin, stdout, stderr = client.exec_command(my_linux_command)  # применяем команду
    data = stdout.read() + stderr.read() # записываем в data всё что прочитали вместе с ошибками
    decoded_data = data.decode("utf-8")
    client.close() # закрытие соединения
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[:-1] # приведение текста в нормальный читаемый вид
    cut = decoded_data[:4095] #обрезка количества символов на тот случай если переменная привысит лимит (телеграмм просто её не выведет)
    return cut

def DbSELECT (my_db_command): #вывод таблиц
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"), database=os.getenv("DB_DATABASE"))
        cursor = connection.cursor()
        cursor.execute(my_db_command)
        data = cursor.fetchall()
        PyStr = ''
        for row in data:
            PyStr += str(row)[1:-1].replace(",", ":").replace("'", "") + '\n'
        logging.info("Команда успешно выполнена")
        cursor.close()
        connection.close()
        return (PyStr)
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
          

def DbINSERT (my_db_command): #ввод данных в таблицу
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"), database=os.getenv("DB_DATABASE"))
        cursor = connection.cursor()
        cursor.execute(my_db_command) # "INSERT INTO phones (номер) VALUES ('8-800-555-35-35', '+7-(800)-555-35-35');"
        connection.commit()
        logging.info("Команда успешно выполнена")
        a = "Команда успешно выполнена"
        cursor.close()
        connection.close()
        return(a)
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

#
# Сбор информации о системе. О релизе системы
def get_release(update: Update, context):
    update.message.reply_text(ParamikoConnection('lsb_release -a'))
# Сбор информации о системе. Об архитектуры процессора, имени хоста системы и версии ядра. 
def get_uname(update: Update, context):
    update.message.reply_text(ParamikoConnection('uname -a'))
# Сбор информации о системе. О времени работы.
def get_uptime(update: Update, context):
    update.message.reply_text(ParamikoConnection('uptime'))
# Сбор информации о состоянии файловой системы.
def get_df(update: Update, context):
    update.message.reply_text(ParamikoConnection('df -h'))
# Сбор информации о состоянии оперативной памяти. 
def get_free(update: Update, context):
    update.message.reply_text(ParamikoConnection('free -h'))
# Сбор информации о производительности системы. 
def get_mpstat(update: Update, context):
    update.message.reply_text(ParamikoConnection('mpstat'))
# Сбор информации о работающих в данной системе пользователях.
def get_w(update: Update, context):
    update.message.reply_text(ParamikoConnection('w'))
# Сбор логов. Последние 10 входов в систему.
def get_auths(update: Update, context):
    update.message.reply_text(ParamikoConnection('last -n 10'))
# Сбор логов. Последние 5 критических события.
def get_critical(update: Update, context):
    update.message.reply_text(ParamikoConnection('journalctl -p crit -n 5'))
# Сбор информации о запущенных процессах. 
def get_ps(update: Update, context):
    update.message.reply_text(ParamikoConnection('ps'))
# Сбор информации об используемых портах.
def get_ss(update: Update, context):
    update.message.reply_text(ParamikoConnection('ss'))
# Сбор информации о запущенных сервисах.
def get_services(update: Update, context):
    update.message.reply_text(ParamikoConnection('systemctl'))
# Вывод логов о репликации из /var/log/postgresql/
def get_repl_logs(update: Update, context):
    update.message.reply_text(ParamikoConnection('docker logs devops_bot_db_1 | egrep -i "repl"'))
# вывод данных из таблиц email адресов
def get_emails(update: Update, context):
    update.message.reply_text(DbSELECT('SELECT * FROM emails;'))
# вывод данных из таблиц номеров телефонов
def get_phone_numbers(update: Update, context):
    update.message.reply_text(DbSELECT('SELECT * FROM phones;'))

# функция вопроса о режиме сбора информации об установленных пакетах. 
def getAptListCommand(update: Update, context):
    update.message.reply_text('Выберете режим работы: \n 1. Вывод всех пакетов; \n 2. Поиск информации о пакете, название которого будет запрошено у пользователя. \n \n Введите 1 или 2')

    return 'get_apt_list'

# функция сбора информации об установленных пакетах
def getAptList (update: Update, context):
    user_input = update.message.text # Получаем текст, содержащий 1 или 2
    if user_input == '1':
        resultAptList = ParamikoConnection('apt list --installed')
        update.message.reply_text(resultAptList) # Отправляем сообщение пользователю
        return ConversationHandler.END # Завершаем работу обработчика диалога
    elif user_input == '2':
        resultAptList = 'Введите название пакета:'
        update.message.reply_text(resultAptList) # Отправляем сообщение пользователю
        return 'get_apt_list2'
    else :
        resultAptList = 'Вы ввели неправильный номер, попробуйте применить команду ещё раз и введите правильный номер'
        update.message.reply_text(resultAptList) # Отправляем сообщение пользователю
        return ConversationHandler.END # Завершаем работу обработчика диалога

def getAptList2 (update: Update, context): # функция только для случаев, когда user_input = 2
    user_input = update.message.text # Получаем текст
    commandAptList2 = 'apt list --installed | grep ' + user_input
    update.message.reply_text(ParamikoConnection(commandAptList2)) # Отправляем сообщение пользователю
    return ConversationHandler.END # Завершаем работу обработчика диалога

#основная функция, которая запускается самой первой
def main():
	# Создайте программу обновлений и передайте ей токен вашего бота
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик номеров телефонов
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'find_phone_number2': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers2)],
        },
        fallbacks=[]
    )

    # Обработчик электронных почт
    convHandlerFindEmails = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'find_email2': [MessageHandler(Filters.text & ~Filters.command, findEmail2)],
        },
        fallbacks=[]
    )

    # Обработчик верификации паролей
    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )

    # Команда линукс которой надо 2 раза что-то сказать
    # Сбор информации об установленных пакетах
    convHandlerAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, getAptList)],
            'get_apt_list2': [MessageHandler(Filters.text & ~Filters.command, getAptList2)],
        },
        fallbacks=[]
    )

	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmails)
    dp.add_handler(convHandlerVerifyPassword)
    # Обработчики команд для взаимодействия с удалённым Linux сервером
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(convHandlerAptList)
    # Обработчики команд для взаимодействия с Master сервером
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
	
	# Регистрируем обработчик текстовых сообщений (эхо режим)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
