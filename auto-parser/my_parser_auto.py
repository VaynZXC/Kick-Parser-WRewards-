import sys
import time
import datetime
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
import os
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException, InvalidSelectorException
import zipfile


# ---> ALL ACCOUNTS <---


bot = telebot.TeleBot('6807729782:AAEpu9XVa1EJDL1OSqrPvD6pE69XUulQWM4')
bot_token = '6807729782:AAEpu9XVa1EJDL1OSqrPvD6pE69XUulQWM4'
chat_id = '-4129523904'
bot_chat_id = '-4095876207'
message = 'Привет, это тестовое сообщение от моего бота!'

PROXY_HOST ='147.45.87.85'
PROXY_PORT ='8000'
PROXY_USER = 'LoSpoo'
PROXY_PASS = 'a8mJ9q'

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)


def send_telegram_message(bot_token, chat_id, message):
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    try:
        response = requests.get(send_text)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке сообщения в Telegram: {e}")
        return None

class MessageSenderThread(QThread):
    send_random_message_signal = pyqtSignal()
    pochinka_event = pyqtSignal()

    def __init__(self, parent=None):  # 600 секунд = 10 минут
        super(MessageSenderThread, self).__init__(parent)
        self.is_running = True
        self.pochinka_time = False
        
        
    def run(self):
        print('MessageSenderThread начал свою работу')
        while self.is_running:
            if self.pochinka_time == False:
                delay = random.randint(180, 360)
                #delay = random.randint(120, 180)
                time.sleep(delay)
                self.send_random_message_signal.emit()
            
    @pyqtSlot()
    def handle_pochinka(self):
        self.pochinka_time = True
        print('Началась починка, все рандомные сообщения остановлены на 3 минуты.')
        time.sleep(120)
        print('До запуска рандомных сообщений осталась 1 минута.')
        time.sleep(50)
        print('До запуска рандомных сообщений осталась 10 ceкунд.')
        time.sleep(10)
        self.pochinka_time = False
        
    def stop(self):
        self.is_running = False

class DataFetcherThread(QThread):
    stream_is_start_signal = pyqtSignal(str)
    stream_is_over_signal = pyqtSignal(str)
    change_streamer_name_signal = pyqtSignal(str)
    pochinka_signal = pyqtSignal()
    
    def __init__(self, chat_writers, parent=None):
        super(DataFetcherThread, self).__init__(parent)
        self.message_queue = Queue()
        self.chat_writers = chat_writers
        self.parser_started = False
        
        self.wg_messages_sent_count = 0  # Счетчик отправленных WG сообщений

        
    def run(self):
        last_processed_id = None
        print('DataFetcherThread начал работу.')
        
        while True:
            try:
                # Проверка и добавление сообщений в очередь
                response = requests.get('http://188.225.86.91:5000/get_data')
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
                    message_time = datetime.datetime.now()
                    if 'Начался стрим на канале' in message:
                        split_message = message.split()
                        streamer = split_message[4]
                        if streamer.lower() == 'wrewards':
                            streamer_name = 'bro'
                        elif streamer.lower() == 'pkle':
                            streamer_name = 'pkle'
                        elif streamer.lower() == 'watchgamestv':
                            streamer_name = 'ibby'
                        elif streamer.lower() == 'hyuslive':
                            streamer_name = 'hyus'
                        print(message)
                        print(streamer)
                        self.stream_is_start_signal.emit(streamer)
                        self.change_streamer_name_signal.emit(streamer_name)
                    if self.parser_started == True:
                        if 'Раздача поинтов началась.' in message:
                            self.wg_messages_sent = 0
                            for chat_writer in self.chat_writers:
                                chat_writer.set_wg_active(True)
                                chat_writer.send_message_signal.emit('WG')
                            print(f'{[message_time]} Запуск WG сообщения...')
                        if 'Починка' in message:
                            self.pochinka_signal.emit()
                            #for chat_writer in self.chat_writers:
                                #chat_writer.send_message_signal.emit('pochinka')

                        elif 'Стрим на канале' in message:
                            split_message = message.split()
                            streamer = split_message[3]
                            print(message)
                            self.stream_is_over_signal.emit(streamer)
                        elif 'передал рейд' in message:
                            split_message = message.split()
                            streamer = split_message[4]
                            print(message)
                            self.stream_is_over_signal.emit(streamer)
                        
                time.sleep(10)  # Задержка перед следующим запросом
            except Exception as e:
                print(e)

    @pyqtSlot(str)
    def on_wg_message_sent(self, account_name):
        self.wg_messages_sent_count += 1
        #print(f"Бот {account_name} отправил WG сообщение.")
        if self.wg_messages_sent_count == len(self.chat_writers):
            self.wg_messages_sent_count = 0  # Сброс счетчика
            for writer in self.chat_writers:
                writer.set_wg_active(False)  # Отключаем режим WG
            print("Все WG сообщения отправлены.")
        
        
    def stop(self):
        self.parser_started = False

class ChatWriterThread(QThread):
    loaded_signal = pyqtSignal()
    send_message_signal = pyqtSignal(str)
    wg_active = pyqtSignal(bool)
    wg_message_sent_signal = pyqtSignal(str)
    
    def __init__(self, cookie_file_path, streamer=None, streamer_name=None, account_name='bot', parent=None):
        super(ChatWriterThread, self).__init__(parent)
        self.is_running = True
        self.streamer = streamer
        self.cookie_file_path = cookie_file_path
        self.account_name = account_name
        self.used_messages_file_path = f'phrases/used_messages/used_messages_{self.account_name}.txt'
        self.used_messages = self.load_used_messages()
        self.random_messages = self.load_random_messages()
        self.send_message_signal.connect(self.send_message_on_kick)
        self.streamer_name = streamer_name
        self.wg_active = False
        self.is_ready = False
        

    def run(self):            
        with self.get_chromedriver(
            #use_proxy = True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 
        ) as self.driver:
            print(f'Окно браузера запущено. [{self.account_name}]')
            
            print(self.streamer_name)
            
            #site = f'https://kick.com/Suzuraya1'
            site = f'https://kick.com/{self.streamer}'
            self.driver.get(site) 
            try:
                button2 = self.driver.find_element(By.XPATH, '//*[@id="app"]/span/div/div[3]/button[1]')
                button2.click()
            except NoSuchElementException:
                print('Кнопки 1 не найдено.')
                
            #Загрузка кук из файла
            self.add_cookies()
            while self.is_ready == False:
                status = self.check_cookies(site)
                if status == True:
                    self.is_ready = True
                else:
                    self.add_cookies()
                    
            time.sleep(3)
            self.avatar_element.click()
            time.sleep(3)
            try:
                menu_item = self.driver.find_element(By.XPATH, '//*[@id="headlessui-menu-items-4"]/div[1]/a')
                if menu_item:   
                    print(f'Открываю вторую вкладку. [{self.account_name}]')
                    url = menu_item.get_attribute('href')
                    self.driver.execute_script("window.open(arguments[0]);", url)
            except NoSuchElementException:
                print(f'Вкладки "Канал" не найдено.')
            
            first_tab = self.driver.window_handles[0]
            self.driver.switch_to.window(first_tab)
            self.loaded_signal.emit()  
            
            while self.is_running:
                time.sleep(1)
                


    def check_cookies(self, site):
        self.driver.get(site)
        time.sleep(5)
        try:
            self.avatar_element = self.driver.find_element(By.XPATH, '//*[@id="headlessui-menu-button-3"]/div/img')
            if self.avatar_element:
                return True   
        except NoSuchElementException:
            print(f'Аватарка не найдна. [{self.account_name}]')
            return False
        
    def add_cookies(self):
        with open(self.cookie_file_path, 'r') as cookies_file:
            cookies = json.load(cookies_file)
            for cookie in cookies:
                if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                    cookie['sameSite'] = 'None'
                self.driver.add_cookie(cookie)
            print(f'Подключены cookies. [{self.account_name}]')
        
    @pyqtSlot(bool)
    def set_wg_active(self, state):
        self.wg_active = state
        
    def load_random_messages(self):
        try:
            with open('phrases/phrases.txt', 'r', encoding='utf-8') as file:
                random_messages = [(index, line.strip()) for index, line in enumerate(file)]
            return random_messages
        except FileNotFoundError:
            print("Файл с фразами не найден.")
            return []
        
    def load_used_messages(self):
        try:
            with open(self.used_messages_file_path, 'r', encoding='utf-8') as file:
                used_message_indices = {int(line.strip()) for line in file.readlines()}
            return used_message_indices
        except FileNotFoundError:
            return set()
        except ValueError as e:
            print(f"Ошибка в файле использованных сообщений: {e}")
            return set()

    def update_used_messages(self, message_index):
        self.used_messages.add(message_index)
        with open(self.used_messages_file_path, 'a', encoding='utf-8') as file:
            file.write(f'{message_index}\n')
            
    def select_random_message(self):
        available_messages = [(index, msg) for index, msg in self.random_messages if index not in self.used_messages]
        # Проверка, что есть доступные сообщения
        if not available_messages:
            self.used_messages.clear()
            try:
                os.remove(self.used_messages_file_path)
            except FileNotFoundError:
                print(f"Файл {self.used_messages_file_path} не был найден для удаления.")
            available_messages = [msg for index, msg in self.random_messages]
        #print(available_messages)
        message_index, random_message = random.choice(available_messages)
        self.update_used_messages(message_index)
        return random_message.format(streamer_name=self.streamer_name)

    @pyqtSlot(str)
    def send_message_on_kick(self, message):
        self.chat_input = self.driver.find_element(By.ID, "message-input")
        
        if hasattr(self, 'chat_input'):
            try:
                if message == 'random':
                    if not self.wg_active:
                        message = self.select_random_message()
                        delay = random.randint(5, 10)
                        time.sleep(delay)
                    else:
                        return
                if message == 'WG' and self.wg_active:   
                    #print(f'[ТЕСТ] Точка пройдена...')
                    delay = random.randint(1, 2)
                    time.sleep(delay)
                # if message == 'pochinka':   
                #     message = '!join'
                #     delay = random.randint(2, 3)
                #     time.sleep(delay)
                    
                self.chat_input.click()
                self.chat_input.send_keys(message)
                self.chat_input.send_keys(Keys.ENTER)
                
                print(f'С аккаунта {self.account_name} отправлено сообщение - {message}')
                if message == 'WG' and self.wg_active:   
                    self.wg_message_sent_signal.emit(self.account_name)
                    
            except Exception as e:
                print(e)
                print(f'Не удалось отправить сообщение. [{self.account_name}]')
                send_telegram_message(bot_token, chat_id, f'Не удалось отправить сообщение с аккаута {self.account_name}')
        else:
            print(f'Chat input не инициализирован. [{self.account_name}]')
        
             
    def get_chromedriver(self, use_proxy=False, user_agent=None):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
        if user_agent:
            chrome_options.add_argument(f'--user-agent={user_agent}')

        if use_proxy:      
            plugin_file = 'proxy_auth_plugin.zip'

            with zipfile.ZipFile(plugin_file, 'w') as zp:
                zp.writestr('manifest.json', manifest_json)
                zp.writestr('background.js', background_js)

            chrome_options.add_extension(plugin_file)

        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--disable-proxy-certificate-handler")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--allow-running-insecure-content')


        s = Service(executable_path='chromdriver/chromedriver.exe')

        driver = webdriver.Chrome(options=chrome_options)
        
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
        self.driver.quit()
                
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
        
        
        cookies_directory  = f'cookies/'
        self.chat_writers_loaded = 0
        self.total_chat_writers =  len([name for name in os.listdir(cookies_directory ) if os.path.isfile(os.path.join(cookies_directory , name))])
        #self.total_chat_writers =  1
        self.threads = None
        
        
        self.data_fetcher_thread = DataFetcherThread(self.threads, self)
        self.data_fetcher_thread.stream_is_start_signal.connect(self.stream_is_start)
        self.data_fetcher_thread.stream_is_over_signal.connect(self.stop_parser_on_stream_over)
        self.data_fetcher_thread.change_streamer_name_signal.connect(self.change_streamer_name)
        self.data_fetcher_thread.start()
        
        self.random_message_sender_thread = MessageSenderThread()
        self.random_message_sender_thread.send_random_message_signal.connect(self.send_random_message_to_all_accounts)
        self.data_fetcher_thread.pochinka_signal.connect(self.random_message_sender_thread.handle_pochinka)
 
    def login_button_act(self):
        self.sound_mixer.music.load('sound/main.mp3')
        self.sound_mixer.music.play()
        self.sound_mixer.music.set_volume(0.5)
        
        self.selected_button_id = self.button_group.checkedId()
        
        if self.selected_button_id == 1:
            self.streamer = 'wrewards'
            #self.streamer_name = 'sam'
            self.streamer_name = 'bro'
        elif self.selected_button_id == 2:
            self.streamer = 'pkle'
            self.streamer_name = 'pkle'
        elif self.selected_button_id == 3:
            self.streamer = 'watchgamestv'
            self.streamer_name = 'ibby'
        elif self.selected_button_id == 4:
            self.streamer = 'hyuslive'
            self.streamer_name = 'hyus'
            #self.streamer_name = 'bro'
        elif self.selected_button_id == 0:
            self.streamer = 'watchgamestv'
            self.streamer_name = 'ibby'
        
        self.description.setText('Если парсер вдруг прекратит работу, просто перезапуститее его.')
                        
        print(self.selected_button_id)
        print(self.streamer)
    
        self.start_parser_update_page()
        self.start_chat_writers()
         
    def start_chat_writers(self):
        if self.threads and any(thread.is_running for thread in self.threads):
            return
    
        self.threads = []
        
        self.accounts_names = {
            1: 'kishimy',
            2: 'lilping',
            3: 'silkin_bola',
            4: 'klizmavpopu',
            5: 'rvuanus',
            6: 'dryahlayapisda',
            7: 'osakasona',
            8: 'hrushkasvinka',
            9: 'ebitessami',
            10: 'mimik',
        }  
        if self.total_chat_writers <= 10:
            for i in range(1, self.total_chat_writers + 1):
                cookie_file_path = f'cookies/cookies_{i}.json'
                account_name = self.accounts_names.get(i)
                thread = ChatWriterThread(cookie_file_path, self.streamer, self.streamer_name, account_name)
                
                thread.wg_message_sent_signal.connect(self.data_fetcher_thread.on_wg_message_sent)
                
                thread.loaded_signal.connect(self.on_chat_writer_loaded)
                self.new_message_signal.connect(thread.send_message_on_kick)
                thread.start()
                self.threads.append(thread)
        else:
            print('-----------------------------------------------------------')
            print('')
            print('       =====> Превышено кол-во аккаунтов <=====')
            print('')
            print('Обратите внимание на то, что бы их кол-во не превышало 10.')
            print('')
            print('-----------------------------------------------------------')
            raise Exception
                  
    def on_chat_writer_loaded(self):
        self.chat_writers_loaded += 1
        if self.chat_writers_loaded == self.total_chat_writers:
            print("=====> Все ChatWriterThread успешно загружены. <=====")
            self.data_fetcher_thread.chat_writers = self.threads
            self.data_fetcher_thread.parser_started = True
            self.start_message_sender()

    @pyqtSlot(str)
    def stream_is_start(self, streamer):
        self.streamer = streamer
        self.start_chat_writers()
        self.start_parser_update_page()

    @pyqtSlot(str)
    def stop_parser_on_stream_over(self, streamer):
        print('Работа приложения остановлена, так как стрим завершен.')
        self.stop_parser_update_page()

    @pyqtSlot(str)
    def change_streamer_name(self, streamer_name):
        if self.threads:
            print(f'Меням имя стримера на {streamer_name}.')
            for thread in self.threads:
                thread.streamer_name = streamer_name

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
        
        self.data_fetcher_thread.parser_started == True
        
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
     
        if self.threads:
            for thread in self.threads:
                thread.is_running = False
            
        self.data_fetcher_thread.parser_started == False

    def send_random_message_to_all_accounts(self):
        if self.threads:
            print(f'Сигнал о отправке рандомного сообщения был отправлен.')
            for thread in self.threads:
                thread.set_wg_active(False)
            self.new_message_signal.emit('random')

    def start_message_sender(self):
        self.random_message_sender_thread.start()
        
    def send_accounts_data(self):
        pass
        
    def stop_message_sender(self):
        print('message_sender_thread приостановил свою работу')
        self.random_message_sender_thread.stop()
        self.random_message_sender_thread.wait()  # Ожидаем завершения потока


    def close_button_act(self):
        if self.threads is not None:
            for thread in self.threads:
                thread.is_running = False
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    parserapp = ParserApp()
    parserapp.show()
    sys.exit(app.exec_())