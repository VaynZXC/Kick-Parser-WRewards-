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
import requests
import telebot
from queue import Queue
import json
import os
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains


# ---> ALL ACCOUNTS <---


bot = telebot.TeleBot('6807729782:AAEpu9XVa1EJDL1OSqrPvD6pE69XUulQWM4')
bot_token = '6807729782:AAEpu9XVa1EJDL1OSqrPvD6pE69XUulQWM4'
chat_id = '-4129523904'
bot_chat_id = '-4095876207'
message = 'Привет, это тестовое сообщение от моего бота!'


def send_telegram_message(bot_token, chat_id, message):
    send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={message}'
    try:
        response = requests.get(send_text)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при отправке сообщения в Telegram: {e}")
        return None

class ChatWriterThread(QThread):
    loaded_signal = pyqtSignal()
    finished_signal = pyqtSignal(str)
    
    def __init__(self, cookie_file_path, account_name='bot', parent=None):
        super(ChatWriterThread, self).__init__(parent)
        self.is_running = True
        self.cookie_file_path = cookie_file_path
        self.account_name = account_name

        self.not_find_element = 0

    def run(self):            
        with self.get_chromedriver(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', 
        ) as self.driver:
            print(f'Окно браузера запущено. [{self.account_name}]')

            site1 = f'https://www.twitch.tv/kishimy2'
            site2 = f'https://www.wrewards.com/advent-calendar'
            
            self.driver.get(site1)
            
            with open(self.cookie_file_path, 'r') as cookies_file:
                cookies = json.load(cookies_file)
                for cookie in cookies:
                    if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                        cookie['sameSite'] = 'None'
                    self.driver.add_cookie(cookie)
                print(f'Подключены cookies. [{self.account_name}]')
            
            time.sleep(1)
            self.driver.get(site1)
            time.sleep(3)
            self.driver.execute_script("window.open('');")

            second_tab = self.driver.window_handles[1]
            self.driver.switch_to.window(second_tab)
            
            self.driver.get(site2)
            
            # Логинимся в аккаунт
            try:
                button = self.driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div[1]/div[3]/a')
                button.click()
            except NoSuchElementException:
                print('Кнопки login не найдено.')
                self.not_find_element += 1
            try:
                button = self.driver.find_element(By.XPATH, '//*[@id="chakra-modal--body-:Rahium6:"]/div/form/div[7]/a')
                button.click()
            except NoSuchElementException:
                print('Кнопки login2 не найдено.')
                self.not_find_element += 1
            time.sleep(3)
            
            # Переходим в вкладку календарь
            self.driver.get(site2)

            # time.sleep(5)  
            # try:
            #     video_element = self.driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[7]')
            #     if video_element:
            #         print(f'Окно в углу найдено.')
            # except NoSuchElementException:
            #     print('Окна в углу не найдено.')
            # try:
            #     close_btn = self.driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[7]/div/div/button[2]')
            #     close_btn.click()
            #     print(f'Окно в углу закрыто.')
            # except NoSuchElementException:
            #     print('Окна в углу не найдено.')
                
            time.sleep(5)
            # Находим элемент в календаре
            try:
                element = self.driver.find_element(By.CLASS_NAME, "react-flip-card")
                actions = ActionChains(self.driver)
                actions.move_to_element(element).perform()
                element.click()
                print(f'Аккаунт {self.account_name} забрал награду.')
            except NoSuchElementException:
                print('Карточки с наградой не найдено.')
                send_telegram_message(bot_token, chat_id, f'Аккаунт {self.account_name} уже забрал бонус дня.')
                
            time.sleep(5)
            # Находим элемент с количеством поинтов на аккаунте
            try:
                element1 = self.driver.find_element(By.XPATH, '//*[@id="menu-button-:rk:"]/span/div[2]')
                element1.click()
                time.sleep(1)
                element2 = self.driver.find_element(By.XPATH, '//*[@id="menu-list-:r2:"]/div[2]/div[1]/div/div')
                points = element2.text
                
                print(f'На аккануте {self.account_name} сейчас {points} поинтов.')
                
                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open('points.txt', 'a') as file:
                    # Записываем информацию. Можно добавить дату/время, если требуется.
                    file.write(f'{current_time}: {self.account_name} - {points} points.\n') 
            except NoSuchElementException:
                print('Поинты не найдены.')
            
            if self.not_find_element == 0:
                pass
            else:
                print(f'Во время работы {self.account_name} не был найден один из элементов.')
                send_telegram_message(bot_token, chat_id, f'Во время вредя работы {self.account_name} не был найден один из элементов.')
                
            time.sleep(3)
            self.driver.quit()  # Предполагаем, что это правильный способ закрыть ваш веб-драйвер
            self.finished_signal.emit(self.account_name)
            self.is_running = False  # Это должно быть последней строкой в методе run

        
    def get_chromedriver(self, use_proxy=False, user_agent=None):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
        if user_agent:
            chrome_options.add_argument(f'--user-agent={user_agent}')

        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--disable-proxy-certificate-handler")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument("--window-size=1650,1000")

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
        
        self.threads_queue = Queue()  # Очередь для управления потоками
        
        cookies_directory  = f'cookies/'
        self.chat_writers_loaded = 0
        self.total_chat_writers =  len([name for name in os.listdir(cookies_directory ) if os.path.isfile(os.path.join(cookies_directory , name))])
        self.active_threads = []
        self.current_thread = None
        
  
    def login_button_act(self):
        self.sound_mixer.music.load('sound/main.mp3')
        self.sound_mixer.music.play()
        self.sound_mixer.music.set_volume(0.5)
        
        self.selected_button_id = self.button_group.checkedId()
        
        self.description.setText('Если парсер вдруг прекратит работу, просто перезапуститее его.')
    
        self.start_parser_update_page()
        self.start_accounts()
         
    def start_accounts(self):
        self.active_threads.clear()
        accounts_names = {
            1: 'kishimy',
            2: 'LilPing',
            3: 'silkin_bola',
            4: 'klizmavpopu',
            5: 'Rvuanus',
            6: 'Dryahlayapisda',
            7: 'kraynyayaprote',
            8: 'HrushkaSvinka',
            9: 'Ebitessami',
            10: 'Mimik',
            11: 'OsakaSan',
            12: 'KhandaMama',
            13: 'Bomjson',
            14: 'Maliklitor',
            15: 'VaynPussyKiller',
            16: 'doneskiy_grover',
            17: 'OkoyoLily',
            18: 'CripMechnik',
            19: 'GENADIY_NAGIBATOR228',
            20: 'Syskonojka',
            21: 'Farmaseft',
            22: 'Jeenchuryki',
            23: 'Geshka_gorin',
            24: 'LegendNudist',
            25: 'MyBallsIsSpicy',
            26: 'GreenSupport',
            27: 'OlejaZadrot',
            28: 'Tehniccc',
            29: '6kTitan',
            30: 'fastrapira',
        }  
        
        for i in range(1, self.total_chat_writers + 1):
            cookie_file_path = f'cookies/cookies_{i}.json'
            account_name = accounts_names.get(i)
            thread = ChatWriterThread(cookie_file_path, account_name)
            self.active_threads.append(thread)  # Добавьте поток в список активных потоков
            self.threads_queue.put(thread)
            
        self.run_next_bot()
        
    def run_next_bot(self):
        QtCore.QCoreApplication.processEvents()
        
        if not self.threads_queue.empty():
            self.current_thread = self.threads_queue.get()
            self.current_thread.finished_signal.connect(self.on_chat_writer_finished)
            self.current_thread.start()
                  
    def on_chat_writer_finished(self, account_name):
        print(f"....")
        self.run_next_bot()  # Запускаем следующего бота

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
        
        with open('points.txt', 'a') as file:
            # Записываем информацию. Можно добавить дату/время.
            current_time = datetime.datetime.now().strftime('%Y-%m-%d')
            file.write(f'Статистика по аккаунтам за {current_time}.\n')
        
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
            
    def close_button_act(self):
        for thread in self.active_threads:
            thread.stop()
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