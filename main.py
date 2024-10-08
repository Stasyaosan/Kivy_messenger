from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from api import Auth, Api
from db import Connect
from functools import partial

session = None
chat_id_global = None

class LoginScreen(Screen):
    def validate_user(self):
        global session
        username = self.ids.username_input.text
        password = self.ids.password_input.text

        auth = Auth(username, password)
        token = auth.get_token()
        session = token['token']

        if token['token'] == 'Error' or token['token'] == '':
            self.show_invalid_login_popup()
        else:
            db = Connect('users.db')
            db.add_token(token['token'])

            api = Api(session)
            id_user = api.request_post('get_id_user', {'token': token['token']})
            id_user = id_user['id_user']
            chat_list = api.request_post('get_chats', {'token': token['token'], 'id_user': id_user})

            chat_screen = self.manager.get_screen('chats')
            chat_screen.set_chat_list(chat_list)

            self.manager.current = "chats"


    def show_invalid_login_popup(self):
        popup = Popup(title='Invalid Login',
                      content=Label(text='Incorrect username or password.'),
                      size_hint=(0.6, 0.4))
        popup.open()


class HomeScreen(Screen):
    pass


class ChatListScreen(Screen):
    def __init__(self, **kwargs):
        super(ChatListScreen, self).__init__(**kwargs)

        self.layout = BoxLayout(orientation='vertical')

        self.header = Label(text='Список чатов', font_size='24sp', size_hint=(1, 0.1))
        self.layout.add_widget(self.header)

        self.scroll_view = ScrollView(size_hint=(1, 0.9))
        self.chat_list_layout = GridLayout(cols=1, size_hint_y=None)
        self.chat_list_layout.bind(minimum_height=self.chat_list_layout.setter('height'))
        self.scroll_view.add_widget(self.chat_list_layout)
        self.layout.add_widget(self.scroll_view)

        self.add_widget(self.layout)

    def set_chat_list(self, chats):
        self.chat_list_layout.clear_widgets()  # Очищаем старый список

        for chat in chats:
            btn = Button(text=chat['title'], size_hint_y=None, height=40)
            btn.bind(on_press=partial(self.open_chat, chat['id']))
            self.chat_list_layout.add_widget(btn)

    def open_chat(self, chat_id, instance):
        global chat_id_global
        chat_id_global = chat_id
        api = Api(session)
        d = {'id_chat': chat_id, 'count': 10}
        messages = api.request_post('get_messages', d)

        chat_screen = self.manager.get_screen('chat')
        chat_screen.set_chat_title(instance.text)
        chat_screen.set_chat_content(messages)

        self.manager.current = 'chat'


class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super(ChatScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.chat_title = Label(text='', font_size='24sp', size_hint=(1, 0.1))
        self.layout.add_widget(self.chat_title)

        self.scroll_view = ScrollView(size_hint=(1, 0.7))
        self.chat_content_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.chat_content_layout.bind(minimum_height=self.chat_content_layout.setter('height'))
        self.scroll_view.add_widget(self.chat_content_layout)
        self.layout.add_widget(self.scroll_view)

        self.message_box = BoxLayout(size_hint=(1, 0.2), orientation='horizontal')

        self.message_input = TextInput(hint_text='Введите сообщение...', size_hint=(0.8, 1), multiline=False)
        self.message_box.add_widget(self.message_input)

        self.send_button = Button(text='Отправить', size_hint=(0.2, 1))
        self.send_button.bind(on_press=self.send_message)
        self.message_box.add_widget(self.send_button)

        self.layout.add_widget(self.message_box)

        back_btn = Button(text='Назад к списку чатов', size_hint=(1, 0.1))
        back_btn.bind(on_press=self.go_back_to_chats)
        self.layout.add_widget(back_btn)

        self.add_widget(self.layout)

    def set_chat_title(self, chat_title):
        self.chat_title.text = f'Чат: {chat_title}'

    def set_chat_content(self, messages):
        self.chat_content_layout.clear_widgets()

        for message in messages:
            msg_text = f"{message['user']}: {message['text']}"
            label = Label(text=msg_text, size_hint_y=None, height=40)
            self.chat_content_layout.add_widget(label)

    def go_back_to_chats(self, instance):
        self.manager.current = 'chats'

    def send_message(self, instance):
        global chat_id_global
        message_text = self.message_input.text.strip()
        if message_text:
            api = Api(session)
            id_user = api.request_post('get_id_user',{'token': session})['id_user']
            data = {'token': session, 'id_user': id_user, 'text_message': message_text, 'id_chat': chat_id_global}
            response = api.request_post('add_message', data)
            if response['status'] == 'ok':
                msg_text = f'{id_user}: {message_text}'
                label = Label(text=msg_text, size_hint_y=None,height=40)
                self.chat_content_layout.add_widget(label)
                self.scroll_view.scroll_y = 0
                self.message_input.text = ''
            else:
                pass



class LoginApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ChatListScreen(name='chats'))  # Добавляем экран для списка чатов
        sm.add_widget(ChatScreen(name='chat'))  # Добавляем экран для конкретного чата
        return sm


if __name__ == '__main__':
    LoginApp().run()
