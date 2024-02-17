import imaplib
import email
from email.header import decode_header
import os

# Данные для входа
username = 'twitch-vaynzxc@mail.ru'
password = 'LfcJ1PKefyNyxsbMqXje'

# Функция для получения ID последнего обработанного сообщения
def get_last_message_id(last_message_id_file):
    if os.path.exists(last_message_id_file):
        with open(last_message_id_file, 'r') as file:
            return file.read().strip()
    return "0"

# Функция для сохранения ID последнего обработанного сообщения
def save_last_message_id(message_id):
    with open(last_message_id_file, 'w') as file:
        file.write(str(message_id))


streamers = ['Hyuslive', 'WatchGamesTV', 'WRewards', 'pkle']
last_message_id_file = 'mail-parser\last_message.txt'

# Подключение к серверу IMAP Mail.ru
mail = imaplib.IMAP4_SSL('imap.mail.ru')
mail.login(username, password)

# Выбор почтового ящика
mail.select('inbox')

# Получение ID последнего сообщения, которое было обработано
last_message_id = get_last_message_id(last_message_id_file)

# Поиск сообщений
typ, data = mail.search(None, 'ALL')
messages = data[0].split()

# Начальное значение для нового последнего ID
new_last_message_id = last_message_id

# Перебор всех сообщений
for num in reversed(messages):
    # Преобразование байтового литерала в строку и сравнение с последним сохраненным ID
    num_str = num.decode('utf-8')
    if int(num_str) <= int(last_message_id):
        # Пропускаем обработанные сообщения
        continue

    # Обработка новых сообщений
    typ, msg_data = mail.fetch(num, '(RFC822)')
    raw_email = msg_data[0][1]
    email_message = email.message_from_bytes(raw_email)
    decoded_header = decode_header(email_message['Subject'])
    subject, charset = decoded_header[0]
    if charset is not None:
        subject = subject.decode(charset)

    # Ваши действия с новым сообщением
    print(f'Новое сообщение: {subject}')

    # Обновляем значение нового последнего ID
    new_last_message_id = max(new_last_message_id, int(num_str))

# Сохранение ID последнего обработанного сообщения для следующей проверки
save_last_message_id(last_message_id_file, new_last_message_id)

# Закрытие соединения
mail.close()
mail.logout()