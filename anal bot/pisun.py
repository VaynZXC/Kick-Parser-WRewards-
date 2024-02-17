
# ---> ПЕРВЫЙ БОТ <---

import requests
import time

bot_token = '6807729782:AAEpu9XVa1EJDL1OSqrPvD6pE69XUulQWM4'
chat_id = '-4095876207'
message = 'Привет, это тестовое сообщение от моего бота!'
message2 = 'Раздача поинтов началась.'


def send_telegram_message(bot_token, chat_id, message):
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    response = requests.get(send_text)
    return response.json()
        
def send_data_to_server(message):
    data = {'message': message}
    response = requests.post('http://127.0.0.1:5000/post_data', json=data)
    if response.status_code == 200:
        print("Данные успешно отправлены на сервер")
    else:
        print("Ошибка при отправке данных на сервер")

while True:
    send_telegram_message(bot_token, chat_id, message)
    send_data_to_server(message)
    time.sleep(30)
    send_telegram_message(bot_token, chat_id, message2)
    send_data_to_server(message2)
    time.sleep(30)