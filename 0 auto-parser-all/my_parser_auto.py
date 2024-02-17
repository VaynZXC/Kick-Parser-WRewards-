import sys
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QButtonGroup
from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal
from settings import *
import settings
from pygame import mixer
from style import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import requests
import json
import random
import telebot
from queue import Queue


# ---> ALL ACCOUNTS <---


bot = telebot.TeleBot('6807729782:AAEpu9XVa1EJDL1OSqrPvD6pE69XUulQWM4')
bot_token = '6807729782:AAEpu9XVa1EJDL1OSqrPvD6pE69XUulQWM4'
chat_id = '-4129523904'
bot_chat_id = '-4095876207'
message = 'Привет, это тестовое сообщение от моего бота!'


class DataFetcherThread(QThread):
    def __init__(self, chat_writers, parent=None):
        super(DataFetcherThread, self).__init__(parent)
        self.message_queue = Queue()
        self.chat_writers = chat_writers

        
    def run(self):
        last_processed_id = None
        print('DataFetcherThread начал работу.')
        while True:
            # Проверка и добавление сообщений в очередь
            response = requests.get('http://127.0.0.1:5000/get_data')
            if response.status_code == 200:
                data = response.json()
                message = data.get('message')
                message_id = data.get('id')
                if message_id != last_processed_id:
                    last_processed_id = message_id
                    self.message_queue.put((message, message_id))
            else:
                print(f'[DataFetcher]: Ошибка при получении данных с сервера')

            # Обработка сообщений из очереди
            if not self.message_queue.empty():
                message, _ = self.message_queue.get()
                if 'Раздача поинтов началась.' in message:
                    print('Запуск WG сообщения...')
                    for chat_writer in self.chat_writers:
                        chat_writer.set_wg_active(True)
                        chat_writer.send_message_signal.emit('WG')
                elif 'Запуск рандомного сообщения.' in message:
                    print('Запуск рандомного сообщения...')
                    for chat_writer in self.chat_writers:
                        chat_writer.set_wg_active(False)
                        chat_writer.send_message_signal.emit('random')
            
            time.sleep(10)  # Задержка перед следующим запросом


class ChatWriterThread(QThread):
    loaded_signal = pyqtSignal()
    send_message_signal = pyqtSignal(str)
    wg_active = pyqtSignal(bool)
    
    def __init__(self, cookie_file_path, streamer=None, streamer_name=None, account_name='bot', parent=None):
        super(ChatWriterThread, self).__init__(parent)
        self.is_running = True
        self.streamer = streamer
        self.cookie_file_path = cookie_file_path
        self.account_name = account_name
        self.random_messages = self.load_random_messages()
        self.send_message_signal.connect(self.send_message_on_kick)
        self.streamer_name = streamer_name

        
    @pyqtSlot(bool)
    def set_wg_active(self, state):
        self.wg_active = state
        
    def load_random_messages(self):
        with open('phrases/phrases.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
        return [line.strip() for line in lines]
            
    def select_random_message(self):
        random_message = random.choice(self.random_messages).format(streamer_name=self.streamer_name)
        return random_message

    used_messages = []

    @pyqtSlot(str)
    def send_message_on_kick(self, message):
        self.chat_input = self.driver.find_element(By.ID, "message-input")
        if hasattr(self, 'chat_input'):
            try:
                if message == 'random':
                    if not self.wg_active:
                        message = self.select_random_message()
                        delay = random.randint(10, 20)
                        time.sleep(delay)
                    else:
                        return
                delay = random.randint(2, 5)
                time.sleep(delay)
                self.chat_input.click()
                self.chat_input.send_keys(message)
                self.chat_input.send_keys(Keys.ENTER)
                print(f'С аккаунта {self.account_name} отправлено сообщение - {message}')
            except Exception as e:
                print(e)
                print(f'Не удалось отправить сообщение. {self.account_name}')
        else:
            print(f'Chat input не инициализирован. {self.account_name}')
        
    def run(self):            
        with self.get_chromedriver(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 
        ) as self.driver:
            print(f'Окно браузера запущено. {self.account_name}')
            
            print(self.streamer_name)
            
            #site = f'https://kick.com/sam'
            site = f'https://kick.com/{self.streamer}'
            self.driver.get(site)
            print(f'Сайт прогружен. {self.account_name}')
            
            #Загрузка кук из файла
            with open(self.cookie_file_path, 'r') as cookies_file:
                cookies = json.load(cookies_file)
                for cookie in cookies:
                    if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                        cookie['sameSite'] = 'None'
                    self.driver.add_cookie(cookie)

            print(f'Подключены cookies. {self.account_name}')
            self.driver.get(site)
            print(f'Драйвер готов к работе. {self.account_name}')
            self.loaded_signal.emit()  
            
            while self.is_running:
                time.sleep(1)
             
    def get_chromedriver(self, use_proxy=False, user_agent=None):
        chrome_options = webdriver.ChromeOptions()
    
        if user_agent:
            chrome_options.add_argument(f'--user-agent={user_agent}')

        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--disable-proxy-certificate-handler")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--allow-running-insecure-content')


        s = Service(executable_path='chromdriver/chromedriver.exe')

        driver = webdriver.Chrome(service= s, options=chrome_options)
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            'source': '''
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_JSON;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Object;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy;
        '''
        })

        return driver
        
    def stop(self):
        self.is_running = False
                
class ParserApp(QWidget, settings.Ui_MainWindow):
    new_message_signal = pyqtSignal(str)
    
    def __init__(self):
        super(ParserApp, self).__init__()   
        self.setupUi(self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        normal_cursor_path = 'cursor/Glib Cur v3 (Rounded)/Normal Select.cur'
        normal_cursor_pixmap = QtGui.QPixmap(normal_cursor_path)
        normal_cursor = QtGui.QCursor(normal_cursor_pixmap, 0, 0)
        self.setCursor(normal_cursor)
        text_cursor_path = 'cursor/Glib Cur v3 (Rounded)/beam.cur'
        text_cursor_pixmap = QtGui.QPixmap(text_cursor_path )
        self.setupUi(self)
        self.setFixedSize(self.size())
        
        self.sound_mixer = mixer
        self.sound_mixer.init()
        
        self.label.setText('All accounts')
        
        self.stop_button.lower()
        self.stop_button.clicked.connect(self.stop_parser_update_page)
        self.in_progress.lower()
        
        self.live_hyus.lower()
        self.live_pkle.lower()
        self.live_watchgamestv.lower()
        self.live_wrewards.lower()
        
        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.wrewards_radio, 1)
        self.button_group.addButton(self.pkle_radio, 2)
        self.button_group.addButton(self.watchgamestv_radio, 3)
        self.button_group.addButton(self.hyus_radio, 4)
        
        self.selected_button_id = self.button_group.checkedId()
        self.streamer = None
        self.streamer_name = None
        
        self.login_button.clicked.connect(self.login_button_act)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: white; /* Исходный цвет */
                border: 1px solid #8f8f91; /* Граница, если нужно */
            }
            QPushButton:hover {
                background-color: #dcdcdc; /* Цвет при наведении */
            }
        """)
        self.close_button.clicked.connect(self.close_button_act)
        self.wrap_button.clicked.connect(self.wrap_button_act)
        
        
        self.chat_writers_loaded = 0
        self.total_chat_writers = 10
    
        
 
    def login_button_act(self):
        self.sound_mixer.music.load('sound/main.mp3')
        self.sound_mixer.music.play()
        self.sound_mixer.music.set_volume(0.5)
        
        self.selected_button_id = self.button_group.checkedId()
        
        if self.selected_button_id == 1:
            self.streamer = 'wrewards'
            self.streamer_name = 'sam'
        elif self.selected_button_id == 2:
            self.streamer = 'pkle'
            self.streamer_name = 'pkle'
        elif self.selected_button_id == 3:
            self.streamer = 'watchgamestv'
            self.streamer_name = 'ibby'
        elif self.selected_button_id == 4:
            self.streamer = 'hyuslive'
            self.streamer_name = 'hyus'
        
        self.description.setText('Если парсер вдруг прекратит работу, просто перезапуститее его.')
                        
        print(self.selected_button_id)
        print(self.streamer)
    
        self.start_parser_update_page()
        self.start_chat_writers()
    
        
    def start_chat_writers(self):
        self.threads = []
        
        accounts_names = {
            1: '[papagrifin]',
            2: '[kichimy]',
            3: '[suzuraya]',
            4: '[lilping]',
            5: '[crispychicken]',
            6: '[tanziro]',
            7: '[lucashenko]',
            8: '[19sqgang]',
            9: '[legofanubis]',
            10: '[toshiguya]'
        }  
        for i in range(1, self.total_chat_writers + 1):
            cookie_file_path = f'E:/Programirivanie/Python/WRewardsParse/cookies/cookies_{i}.json'
            account_name = accounts_names.get(i)
            thread = ChatWriterThread(cookie_file_path, self.streamer, self.streamer_name, account_name)
            thread.loaded_signal.connect(self.on_chat_writer_loaded)
            self.new_message_signal.connect(thread.send_message_on_kick)
            thread.start()
            self.threads.append(thread)
                  
    def on_chat_writer_loaded(self):
        self.chat_writers_loaded += 1
        if self.chat_writers_loaded == self.total_chat_writers:
            print("=====> Все ChatWriterThread успешно загружены. <=====")
            self.data_fetcher_thread = DataFetcherThread(self.threads, self)
            self.data_fetcher_thread.start()

    def start_parser_update_page(self):
        self.login_button.lower()
        self.live_hyus.lower()
        self.live_pkle.lower()
        self.live_watchgamestv.lower()
        self.live_wrewards.lower()
        self.pkle.lower()
        self.pkle_radio.lower()
        self.wrewards.lower()
        self.wrewards_radio.lower()
        self.hyus.lower()
        self.hyus_radio.lower()
        self.watchgamestv.lower()
        self.watchgamestv_radio.lower()
        
        self.stop_button.raise_()
        self.in_progress.raise_()
        
    def stop_parser_update_page(self):
        self.sound_mixer.music.load('sound/main.mp3')
        self.sound_mixer.music.play()
        self.sound_mixer.music.set_volume(0.5)
        
        self.login_button.raise_()
        self.pkle.raise_()
        self.pkle_radio.raise_()
        self.wrewards.raise_()
        self.wrewards_radio.raise_()
        self.hyus.raise_()
        self.hyus_radio.raise_()
        self.watchgamestv.raise_()
        self.watchgamestv_radio.raise_()
        
        self.stop_button.lower()
        self.in_progress.lower()
     
        for thread in self.threads:
            thread.is_running = False  # Сигнализируем потоку о необходимости завершения
            thread.wait()  # Дожидаемся завершения потока
        
    def close_button_act(self):
        self.close()      

    def wrap_button_act(self):
        self.showMinimized()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self.oldPos is not None:
            delta = event.globalPos() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

    def closeEvent(self, event):
        # Остановка потоков перед закрытием приложения
        if hasattr(self, 'wg_message_thread'):
            self.wg_message_thread.stop()
            self.wg_message_thread.wait()

        if hasattr(self, 'random_message_thread'):
            self.random_message_thread.stop()
            self.random_message_thread.wait()

        super(ParserApp, self).closeEvent(event)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    parserapp = ParserApp()
    parserapp.show()
    sys.exit(app.exec_())