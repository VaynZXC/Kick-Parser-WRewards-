from flask import Flask, request, jsonify
from threading import Thread, Event
import time
import threading
import requests
from uuid import uuid4
from collections import deque

# =====> СЕРВЕР <=====


app = Flask(__name__)

last_message  = None
old_ids = deque(maxlen=100)  # Ограничиваем размер для избежания утечки памяти

        
random_message_text = 'Запуск рандомного сообщения.'
stop_event = Event()

def add_random_message():
    global last_message
    while not stop_event.is_set():
        message_id = str(uuid4())
        last_message  = ({'id': message_id, 'message': random_message_text})
        print("Добавлено рандомное сообщение.")
        time.sleep(900)
    else:
        time.sleep(10)


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
    if last_message is not None:
        if last_message['id'] not in old_ids:
            old_ids.append(last_message['id'])  # Добавляем ID в список уже обработанных
            return jsonify(last_message), 200
    return jsonify({'message': ''}), 200


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
    