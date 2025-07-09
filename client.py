import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image
import socket
import ssl
import time
import os
import json

SESSION_FILE = "session.json"

class MainScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.server_ip = "80.74.27.52"
        self.server_port = 33333
        self.clear_widgets()
        self.is_logged = False
        self.build_login_ui()
        self.session_check()

    def build_login_ui(self):
        self.clear_widgets()
        self.username_input = TextInput(hint_text='@Юзер', multiline=False)
        self.add_widget(self.username_input)
        self.pass_input1 = TextInput(hint_text='Пароль', multiline=False, password=True)
        self.add_widget(self.pass_input1)
        self.pass_input2 = TextInput(hint_text='Повторите пароль', multiline=False, password=True)
        self.add_widget(self.pass_input2)
        self.status_label = Label(text='Зарегистрируйтесь или войдите')
        self.add_widget(self.status_label)
        btns = GridLayout(cols=2, size_hint_y=None, height=40)
        self.reg_btn = Button(text="Регистрация")
        self.reg_btn.bind(on_press=self.register)
        btns.add_widget(self.reg_btn)
        self.log_btn = Button(text="Вход")
        self.log_btn.bind(on_press=self.login)
        btns.add_widget(self.log_btn)
        self.add_widget(btns)
        self.info_label = Label(text='')
        self.add_widget(self.info_label)
        self.is_logged = False

    def build_logged_ui(self, username):
        self.clear_widgets()
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        user_label = Label(text=f"[b]{username}[/b]", markup=True, size_hint_x=0.8, halign="left", valign="middle")
        user_label.bind(size=user_label.setter('text_size'))
        # Простая “лупа” — эмодзи
        lupa_btn = Button(text="🔍", size_hint_x=0.2)
        header.add_widget(user_label)
        header.add_widget(lupa_btn)
        self.add_widget(header)
        self.ping_label = Label(text="Проверяю пинг...", size_hint_y=None, height=40)
        self.add_widget(self.ping_label)
        self.info_label = Label(text="")
        self.add_widget(self.info_label)
        self.is_logged = True

    def session_check(self):
        if os.path.isfile(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                sess = json.load(f)
            self.build_logged_ui(sess["username"])
            self.ping_server()
        else:
            self.build_login_ui()

    def save_session(self, username):
        with open(SESSION_FILE, "w") as f:
            json.dump({"username": username}, f)
        self.session_check()

    def ssl_socket(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        sock = socket.create_connection((self.server_ip, self.server_port), timeout=3)
        return context.wrap_socket(sock, server_hostname=self.server_ip)

    def register(self, instance):
        username = self.username_input.text.strip()
        p1 = self.pass_input1.text.strip()
        p2 = self.pass_input2.text.strip()
        if p1 != p2 or not p1:
            self.status_label.text = "Пароли не совпадают!"
            return
        try:
            with self.ssl_socket() as s:
                s.sendall(f"REGISTER {username} {p1}".encode())
                data = s.recv(1024)
                if data.strip() == b"registered":
                    self.status_label.text = "Регистрация успешна!"
                    self.save_session(username)
                elif b"exists" in data:
                    self.status_label.text = "Такой пользователь уже есть."
                elif b"user_format" in data:
                    self.status_label.text = "Юзер должен начинаться с @"
                else:
                    self.status_label.text = f"Ошибка регистрации: {data}"
        except Exception as e:
            self.status_label.text = f"Ошибка: {e}"

    def login(self, instance):
        username = self.username_input.text.strip()
        password = self.pass_input1.text.strip()
        try:
            with self.ssl_socket() as s:
                s.sendall(f"LOGIN {username} {password}".encode())
                data = s.recv(1024)
                if data.strip() == b"success":
                    self.status_label.text = "Успешный вход!"
                    self.save_session(username)
                else:
                    self.status_label.text = "Ошибка входа."
        except Exception as e:
            self.status_label.text = f"Ошибка: {e}"

    def ping_server(self):
        try:
            start = time.time()
            with self.ssl_socket() as s:
                s.sendall(b"ping")
                data = s.recv(1024)
                end = time.time()
                if data.strip() == b"pong":
                    ping = int((end - start) * 1000)
                    self.ping_label.text = f"Онлайн! Пинг: {ping} мс"
                else:
                    self.ping_label.text = "Ошибка пинга"
        except Exception as e:
            self.ping_label.text = f"Пинг не удался: {e}"

class PingApp(App):
    def build(self):
        return MainScreen()

if __name__ == "__main__":
    PingApp().run()
