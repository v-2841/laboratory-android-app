import json

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.network.urlrequest import UrlRequest
from kivy.storage.dictstore import DictStore


store = DictStore('store')


class LoginWindow(Screen):
    def login(self, *args):
        data = json.dumps({
            "username": self.ids.username.text,
            "password": self.ids.password.text
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
        self.ids.error.text = ''
        self.manager.current = 'list'

    def login_failure(self, request, response):
        self.ids.error.text = 'Произошла ошибка'
        self.ids.password.text = ''


class ListWindow(Screen):
    pass


class LaboratoryApp(App):
    def build(self):
        Builder.load_file('main.kv')
        screen_manager = ScreenManager()
        screen_manager.add_widget(LoginWindow(name='login'))
        screen_manager.add_widget(ListWindow(name='list'))
        if store.exists('token'):
            screen_manager.current = 'list'
        else:
            screen_manager.current = 'login'
        return screen_manager


if __name__ == "__main__":
    Window.size = (300, 620)
    LaboratoryApp().run()
