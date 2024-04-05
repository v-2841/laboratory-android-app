import json
import webbrowser

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.network.urlrequest import UrlRequest
from kivy.storage.dictstore import DictStore
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import NoTransition, Screen, ScreenManager


store = DictStore('store')


class LoginWindow(Screen):
    def login(self, *args):
        self.ids.processing.text = 'Соединение с сервером...'
        self.ids.error.text = ''
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
            on_error=self.login_error,
        )

    def login_success(self, request, response):
        store.put('token', value=response['auth_token'])
        self.ids.processing.text = ''
        self.ids.error.text = ''
        self.ids.password.text = ''
        self.manager.current = 'list'
        self.manager.get_screen('list').get_reagents()

    def login_failure(self, request, response):
        self.ids.processing.text = ''
        errors = ''
        for field in response:
            for error in response[field]:
                if field == 'username':
                    errors += f"Имя пользователя: {error}\n"
                elif field == 'password':
                    errors += f"Пароль: {error}\n"
                elif field == 'non_field_errors':
                    errors += f"{error}\n"
                else:
                    errors += f"{field}: {error}\n"
        self.ids.error.text = errors
        self.ids.password.text = ''

    def login_error(self, request, error):
        self.ids.processing.text = ''
        self.ids.error.text = 'Не удалось подключиться к серверу'
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
            font_size=dp(16),
        )
        popup.open()

    def logout(self, *args):
        store.delete('token')
        self.manager.current = 'login'

    def get_reagents(self, *args):
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
            on_failure=self.get_reagents_failure,
            on_error=self.get_reagents_error,
        )

    def get_reagents_success(self, request, response):
        self.reagents = response
        self.create_buttons(reagents=self.reagents)
        self.display_buttons(self.all_reagents_buttons)

    def create_buttons(self, reagents):
        self.all_reagents_buttons = []
        width = self.manager.width - self.ids.reagents_list.padding[0] * 2
        height = (self.manager.height - self.ids.header.height) / 20
        text_size_x = (self.manager.width
                       - self.ids.reagents_list.padding[0] * 2)
        for reagent in reagents:
            self.all_reagents_buttons.append(Button(
                text=f"{reagent['id']}. {reagent['name']}",
                size_hint=(None, None),
                width=width,
                height=height,
                shorten=True,
                shorten_from='right',
                padding=dp(5),
                text_size=(text_size_x, None),
                halign='left',
                valign='center',
                background_normal='',
                background_color=(0.8, 0.8, 0.8, 1),
                on_press=self.reagent_info,
                color=(0, 0, 0, 1),
                font_size=dp(18),
            ))

    def display_buttons(self, buttons):
        self.ids.reagents_list.clear_widgets()
        for button in buttons:
            self.ids.reagents_list.add_widget(button)

    def reagent_info(self, *args):
        reagent_id = int(args[0].text.split('.')[0])
        popup = Popup(
            size_hint=(None, None),
            size=(self.manager.width * 0.8, self.manager.height * 0.3),
        )
        for reagent in self.reagents:
            if reagent['id'] == reagent_id:
                popup.title = reagent['name']
                popup.content = Label(
                    text=(self.reagent_info_text(reagent)),
                    font_size=dp(16),
                )
                popup.open()

    def search(self, *args):
        if self.ids.search_field.text == '':
            self.ids.fbutton.unbind(on_press=self.erase)
            self.ids.fbutton.bind(on_press=self.about)
            self.ids.fimage.source = 'img/about.png'
            if not hasattr(self, 'all_reagents_buttons'):
                return
            self.display_buttons(self.all_reagents_buttons)
            return
        self.ids.fbutton.unbind(on_press=self.about)
        self.ids.fbutton.bind(on_press=self.erase)
        self.ids.fimage.source = 'img/eraser.png'
        searched_reagents = []
        for button in self.all_reagents_buttons:
            if self.ids.search_field.text.lower() in button.text.lower():
                searched_reagents.append(button)
        self.display_buttons(searched_reagents)

    def erase(self, *args):
        self.ids.search_field.text = ''

    def reagent_info_text(self, reagent):
        return (
            f"Индекс: {reagent['index']}\n"
            + f"Марка: {reagent['grade'] if reagent['grade'] else '-'}\n"
            + "Дата производства: "
            + f"{self.date_format(reagent['manufacture_date'])}\n"
            + f"Срок годности: {self.date_format(reagent['expiration_date'])}"
        )

    def date_format(self, date):
        if not date:
            return '-'
        date = date.split('-')
        return f'{date[2]}.{date[1]}.{date[0]} г.'

    def get_reagents_failure(self, request, response):
        store.delete('token')
        self.manager.current = 'login'
        self.manager.get_screen('login').ids.error.text = str(response)

    def get_reagents_error(self, request, error):
        self.ids.reagents_list.clear_widgets()
        error = Label(
            text='Не удалось подключиться к серверу',
            font_size=dp(16),
            color=(1, 0, 0, 1),
            size_hint=(1, None),
        )
        self.ids.reagents_list.add_widget(error)
        button = Button(
            text='Повторить попытку',
            font_size=dp(18),
            size_hint=(None, None),
            width=dp(220),
            height=dp(34),
            pos_hint=({'center_x': 0.5}),
            on_press=self.get_reagents,
        )
        self.ids.reagents_list.add_widget(button)


class LaboratoryApp(App):
    def build(self):
        self.icon = 'img/logo.png'
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
    LaboratoryApp().run()
