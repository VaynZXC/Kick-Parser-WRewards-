from flask import Flask, request, jsonify
from threading import Thread, Event
import time
import requests
from collections import defaultdict
from uuid import uuid4
from collections import deque

# =====> СЕРВЕР <=====


app = Flask(__name__)

last_message  = None
old_ids = deque(maxlen=100)  # Ограничиваем размер для избежания утечки памяти
messages_by_ip = defaultdict(lambda: None)  # Словарь для отслеживания сообщений по IP
 
stop_event = Event()

def add_random_message():
    global last_message
    while not stop_event.is_set():
        message_id = str(uuid4())
        last_message = {'id': message_id, 'message': 'Запуск рандомного сообщения.'}
        print("Добавлено рандомное сообщение.")
        time.sleep(20)
        last_message = None
        time.sleep(900)

@app.route('/post_data', methods=['POST'])
def post_data():
    global last_message
    json_data = request.json
    message = json_data.get('message')
    message_id = str(uuid4())
    last_message  = ({'id': message_id, 'message': message})
    print("Получены данные:", json_data)
    return jsonify({'id': message_id, 'success': True}), 200

@app.route('/get_data', methods=['GET'])
def get_data():
    client_ip = request.remote_addr
    if last_message and messages_by_ip[client_ip] is not None:
        if last_message['id'] not in old_ids:
            messages_by_ip[client_ip] = last_message['id']  # Добавляем ID в список уже обработанных
            return jsonify(last_message), 200
        else:
            return jsonify({'message': 'Сообщений нет или уже было получено.'}), 200


@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    if shutdown_func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    shutdown_func()
    return 'Server shutting down...'

def stop_server():
    try:
        requests.post('http://127.0.0.1:5000/shutdown')
    except ConnectionError:
        print("Не удалось остановить сервер. Возможно, он уже остановлен.")

random_message_thread = Thread(target=add_random_message)
random_message_thread.start()

if __name__ == '__main__':
    try:
        app.run(port=5000)
    finally:
        print("Ожидание завершения вторичного потока...")
        stop_event.set()  # Устанавливаем событие для остановки потока
        stop_server()     # Останавливаем сервер
        random_message_thread.join()  # Ожидаем завершения потока
        print("Сервер и вторичный поток успешно остановлены.")
    