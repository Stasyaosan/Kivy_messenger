from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from api import Auth, Api
from db import Connect

session = None


class LoginScreen(Screen):
    def validate_user(self):
        global session
        username = self.ids.username_input.text
        password = self.ids.password_input.text
        auth = Auth(username, password)
        token = auth.get_token()
        session = token['token']
        print(token['token'])
        if token['token'] == 'Error' or token['token'] == '':
            self.show_invalid_login_popup()
        else:
            db = Connect('users.db')
            db.add_token(token['token'])

            api = Api(session)
            try:
                id_user = api.request_post('get_id_user', {'token': token['token']})
                id_user = id_user['id_user']
                chat_list = api.request_post('get_chats', {'token': token['token'], 'id_user': id_user})

                chat_screen = self.manager.get_screen('chats')
                chat_screen.set_chat_list(chat_list)

                self.manager.current = "chats"

            except Exception as e:
                print(f"Ошибка при получении чатов: {e}")
                self.show_invalid_login_popup()

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
            btn.bind(on_press=self.open_chat)
            self.chat_list_layout.add_widget(btn)

    def open_chat(self, instance):
        self.manager.get_screen('chat').set_chat_title(instance.text)
        self.manager.current = 'chat'


class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super(ChatScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.chat_title = Label(text='', font_size='24sp', size_hint=(1, 0.1))
        self.layout.add_widget(self.chat_title)

        self.chat_content = Label(text='Здесь будут сообщения.', size_hint=(1, 0.8))
        self.layout.add_widget(self.chat_content)

        back_btn = Button(text='Назад к списку чатов', size_hint=(1, 0.1))
        back_btn.bind(on_press=self.go_back_to_chats)
        self.layout.add_widget(back_btn)

        self.add_widget(self.layout)

    def set_chat_title(self, chat_title):
        self.chat_title.text = f'Чат: {chat_title}'
        self.chat_content.text = f'Сообщения из {chat_title}'

    def go_back_to_chats(self, instance):
        self.manager.current = 'chats'


class MessengerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(ChatListScreen(name='chats'))  # Добавляем экран для списка чатов
        sm.add_widget(ChatScreen(name='chat'))  # Добавляем экран для конкретного чата
        return sm


if __name__ == '__main__':
    MessengerApp().run()
