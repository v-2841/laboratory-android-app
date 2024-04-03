import json

from kivy.app import App
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest
from kivy.storage.dictstore import DictStore
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.lang import Builder


store = DictStore('store')
Builder.load_string('''
<ButtonAlignLeft>:
    halign: 'left'
    text_size: self.size
''')


class ButtonAlignLeft(Button):
    pass


class LoginWindow(Screen):
    def __init__(self, **kwargs):
        super(LoginWindow, self).__init__(**kwargs)
        layout = BoxLayout(
            orientation="vertical",
            size_hint=(1, 0.5),
            pos_hint={"center_x": 0.5, "center_y": 0.7},
            padding=20,
            spacing=20,
        )
        layout.add_widget(Label(
            text='Laboratory',
            font_size=32,
            bold=True,
            color=(0.039, 0.729, 0.71),
        ))
        self.username = TextInput(
            hint_text='Логин',
            multiline=False,
            font_size=18,
            write_tab=False,
        )
        self.password = TextInput(
            hint_text='Пароль',
            password=True,
            multiline=False,
            font_size=18,
            write_tab=False,
        )
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(Button(
            text='Войти',
            on_release=self.login,
            font_size=18,
        ))
        self.error = Label(
            text='',
            color=(1, 0, 0),
        )
        layout.add_widget(self.error)
        self.add_widget(layout)

    def login(self, *args):
        data = json.dumps({
            "username": self.username.text,
            "password": self.password.text
        })
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json"}
        UrlRequest(
            "https://laboratory.sytes.net/api/auth/token/login",
            req_body=data,
            req_headers=headers,
            method="POST",
            on_success=self.login_success,
            on_failure=self.login_failure,
        )

    def login_success(self, request, response):
        store.put('token', value=response['auth_token'])
        self.error.text = ''
        self.manager.current = 'list'

    def login_failure(self, request, response):
        self.error.text = 'Неверный логин или пароль'
        self.password.text = ''


class ListWindow(Screen):
    def __init__(self, **kwargs):
        super(ListWindow, self).__init__(**kwargs)
        header = BoxLayout(
            orientation="horizontal",
            size_hint=(1, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.97},
            padding=20,
            spacing=10,
        )
        header.add_widget(Label(
            text='Лаборатория',
            font_size=18,
            bold=True,
            color=(0.039, 0.729, 0.71),
        ))
        header.add_widget(Button(
            text='Выход',
            size_hint_x=None,
        ))
        self.add_widget(header)
        self.error = Label(
            text='',
            color=(1, 0, 0),
            pos_hint={"center_x": 0.5, "center_y": 0.85},
        )
        self.add_widget(self.error)
        self.get_reagents()

    def get_reagents(self):
        if not store.exists('token'):
            return
        UrlRequest(
            "https://laboratory.sytes.net/api/reagents/",
            req_headers={
                "Authorization": f"Token {store.get('token')['value']}",
                "Accept": "application/json",
            },
            method="GET",
            on_success=self.get_reagents_success,
            on_failure=self.get_reagents_failure,
        )

    def get_reagents_success(self, request, response):
        scroll = ScrollView(
            size_hint=(1, 0.85),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            do_scroll_x=False,
            do_scroll_y=True,
        )
        reagents = BoxLayout(
            size_hint_y=None,
            orientation="vertical",
        )
        reagents.height = len(response) * 26
        for reagent in response:
            reagents.add_widget(
                ButtonAlignLeft(
                    text=f"{reagent['id']}. {reagent['name']}",
                    font_size=16,
                    padding=5,
                    shorten=True,
                    shorten_from='right',
                )
            )
        scroll.add_widget(reagents)
        self.add_widget(scroll)

    def get_reagents_failure(self, request, response):
        self.error.text = 'Произошла ошибка'


class MainApp(App):
    def build(self):
        Window.clearcolor = (0.9, 0.9, 0.9, 1)
        screen_manager = ScreenManager()
        screen_manager.add_widget(LoginWindow(name="login"))
        screen_manager.add_widget(ListWindow(name="list"))
        if store.exists('token'):
            screen_manager.current = "list"
        return screen_manager


if __name__ == "__main__":
    MainApp().run()
