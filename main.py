import json
import webbrowser

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.storage.dictstore import DictStore
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager


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
    def __init__(self, **kwargs):
        super(ListWindow, self).__init__(**kwargs)
        self.get_reagents()

    def open_website(self, *args):
        webbrowser.open('https://laboratory.sytes.net/')

    def about(self, *args):
        popup = Popup()
        popup.title = 'О программе'
        popup.size_hint = (None, None)
        popup.size = (self.manager.width * 0.8, self.manager.height * 0.3)
        popup.content = Label(
            text=('Laboratory\nAuthor: Vitaliy Pavlov\n\n'
                  + 'github:\nv-2841/laboratory-android-app'),
            font_size=12,
        )
        popup.open()

    def logout(self, *args):
        store.delete('token')
        self.manager.current = 'login'

    def get_reagents(self):
        self.reagents = []
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
        )

    def get_reagents_success(self, request, response):
        self.reagents = response
        for reagent in self.reagents:
            self.ids.reagents_list.add_widget(
                Button(
                    text=f"{reagent['id']}. {reagent['name']}",
                )
            )

    def search(self, *args):
        if self.ids.search_field.text == '':
            self.ids.fbutton.unbind(on_press=self.erase)
            self.ids.fbutton.bind(on_press=self.about)
            self.ids.fimage.source = 'img/about.png'
            return
        self.ids.fbutton.unbind(on_press=self.about)
        self.ids.fbutton.bind(on_press=self.erase)
        self.ids.fimage.source = 'img/eraser.png'

    def erase(self, *args):
        self.ids.search_field.text = ''


class LaboratoryApp(App):
    def build(self):
        Builder.load_file('main.kv')
        screen_manager = ScreenManager(transition=NoTransition())
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
