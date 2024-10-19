import json

from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import AsyncImage
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox

import config
from api import Auth, Api
from db import Connect
from kivy.core.window import Window
from functools import partial

Window.clearcolor = (0.1, 0.3, 0.5, 1)

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
            # реализовать валидацию токена
            db = Connect('users.db')
            db.add_token(token['token'])
            api = Api(session)
            # try:
            id_user = api.request_post('get_id_user', {'token': token['token']})
            id_user = id_user['id_user']

            chat_list = api.request_post('get_chats', {'token': token['token'], 'id_user': id_user})
            del api
            chat_screen = self.manager.get_screen('chats')
            chat_screen.set_chat_list(chat_list)
            self.manager.current = "chats"
            # except Exception as e:
            #     print(f"Ошибка при получении чатов: {e}")
            #     self.show_invalid_login_popup()

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

        self.create_chat_btn = Button(text='Создать чат', size_hint=(1, 0.1))
        self.create_chat_btn.bind(on_press=self.show_create_chat_popup)
        self.layout.add_widget(self.create_chat_btn)

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
        messages = api.request_post('get_messages', {'id_chat': chat_id, 'count': 30})
        del api
        chat_screen = self.manager.get_screen('chat')
        chat_screen.set_chat_title(instance.text)
        chat_screen.set_chat_content_layout(messages)
        self.manager.current = 'chat'

    def show_create_chat_popup(self, instance):
        content = BoxLayout(orientation='vertical')
        self.chat_name_input = TextInput(hint_text='Введите название чата', multiline=False, size_hint=(1, 0.1))
        content.add_widget(self.chat_name_input)
        self.chat_description_input = TextInput(hint_text='Введите описание чата', multiline=True, size_hint=(1, 0.3))
        content.add_widget(self.chat_description_input)

        create_btn = Button(text='Создать', size_hint=(1, 0.05))
        create_btn.bind(on_press=self.create_chat)
        content.add_widget(create_btn)

        self.create_chat_popup = Popup(
            title='Создать чат',
            content=content,
            size_hint=(0.6, 0.7)
        )
        self.create_chat_popup.open()

    def create_chat(self, instance):
        chat_name = self.chat_name_input.text
        chat_description = self.chat_description_input.text
        if 1 <= len(chat_name) <= 100:
            if len(chat_description) <= 1000:
                api = Api(session)
                id_creator = api.request_post('get_id_user', {'token': session})['id_user']
                response = api.request_post('create_chat', {'id_creator': id_creator, 'title': chat_name,
                                                            'description': chat_description})
                del api
                if response['status'] == 'ok':
                    self.refresh_chat_list()
                self.create_chat_popup.dismiss()

    def refresh_chat_list(self):
        api = Api(session)
        id_user = api.request_post('get_id_user', {'token': session})['id_user']
        chat_list = api.request_post('get_chats', {'token': session, 'id_user': id_user})
        self.set_chat_list(chat_list)


class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super(ChatScreen, self).__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        self.button_setting = Button(text='Настройки', size_hint=(0.2, 0.05))
        self.button_setting.bind(on_press=self.show_setting_chat_popup)
        self.layout.add_widget(self.button_setting)

        self.chat_title = Label(text='', font_size='24sp', size_hint=(1, 0.1))
        self.layout.add_widget(self.chat_title)

        self.chat_content_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.chat_content_layout.bind(minimum_height=self.chat_content_layout.setter('height'))
        self.scroll_view = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
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
        # self.chat_content_layout.text = f'Сообщения из {chat_title}'

    def send_message(self, instance):
        global chat_id_global
        message_text = self.message_input.text.strip()
        if message_text:
            api = Api(session)
            id_user = api.request_post('get_id_user', {'token': session})['id_user']
            data = {'token': session, 'id_user': id_user, 'text_message': message_text, 'id_chat': chat_id_global}
            response = api.request_post('add_message', data)
            del api
            if response['status'] == 'ok':
                msg_text = f'{id_user}: {message_text}'
                # label = Label(text=msg_text, size_hint_y=None,height=40)
                # self.chat_content_layout.add_widget(label)

                message_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
                message_label = Label(text=msg_text, size_hint=(0.8, 1))
                message_box.add_widget(message_label)

                delete_button = Button(text='Удалить', size_hint=(0.2, 1))
                delete_button.bind(on_press=partial(self.delete_message, response['id_message'], message_box))
                message_box.add_widget(delete_button)
                self.chat_content_layout.add_widget(message_box)
                self.scroll_view.scroll_y = 0
                self.message_input.text = ''

    def set_chat_content_layout(self, messages):
        self.chat_content_layout.clear_widgets()

        for message in messages:

            if message['file'] == '':
                message_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
                msg_text = f"{message['user']}: {message['text']}"
                message_label = Label(text=msg_text, size_hint=(0.8, 1))
                message_box.add_widget(message_label)
            else:
                message_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=200)
                aimg = AsyncImage(source=config.URL_SITE + message['file'], fit_mode="scale-down")
                message_box.add_widget(aimg)

            delete_button = Button(text='Удалить', size_hint=(0.2, 1))
            delete_button.bind(on_press=partial(self.delete_message, message['id'], message_box))
            message_box.add_widget(delete_button)

            self.chat_content_layout.add_widget(message_box)

    def delete_message(self, message_id, message_box, instance):
        api = Api(session)
        d = {'id_message': message_id}
        response = api.request_post('delete_message', d)
        if response['status'] == 'ok':
            self.chat_content_layout.remove_widget(message_box)
        else:
            popup = Popup(
                title='Ошибка удаления',
                content=Label(text='Не удалось удалить сообщение'),
                size_hint=(0.6, 0.4)
            )

    def show_setting_chat_popup(self, instance):
        content = BoxLayout(orientation='vertical')

        self.name_chat_input = TextInput(hint_text='Нзвание чата', size_hint=(1, 0.05), multiline=False)
        self.description_chat_input = TextInput(hint_text='Описание чата', size_hint=(1, 0.07), multiline=False)
        content.add_widget(self.name_chat_input)
        content.add_widget(self.description_chat_input)

        user_layout = GridLayout(cols=1, size_hint=(1, 0.5))
        user_layout.bind(minimum_height=user_layout.setter('height'))
        api = Api(session)
        users = api.request_post('get_users', {})
        id_creator = int(api.request_post('get_id_user', {})['id_user'])
        self.users_checkbox = []

        response = api.request_post('get_users_from_chat', {'id_chat': chat_id_global})
        id_users_chat = []
        for user in json.loads(response['users']):
            id_users_chat.append(user['pk'])

        for id_user, login_user in users.items():
            if id_creator == int(id_user):
                continue
            box = BoxLayout(orientation='horizontal')
            checkbox = CheckBox()
            if int(id_user) in id_users_chat:
                checkbox.active = True
            else:
                checkbox.active = False
            label = Label(text=login_user, size_hint=(0.8, 0.5))
            box.add_widget(checkbox)
            box.add_widget(label)
            user_layout.add_widget(box)
            self.users_checkbox.append({'checkbox': checkbox, 'id_user': id_user})

        scroll_view = ScrollView(size_hint=(1, 0.4))
        scroll_view.add_widget(user_layout)
        content.add_widget(scroll_view)

        update_btn = Button(text='Обновить', size_hint_y=None)
        update_btn.bind(on_press=self.update_chat)
        content.add_widget(update_btn)

        self.setting_chat_popup = Popup(
            title='Настройки чата',
            content=content,
            size_hint=(0.6, 0.95)
        )
        self.setting_chat_popup.open()

    def update_chat(self, instance):
        for user in self.users_checkbox:
            if user['checkbox'].active:
                id_user = user['id_user']
                api = Api(session)
                response = api.request_post('add_user_to_chat', {'id_user': id_user, 'id_chat': chat_id_global})
                if response['status'] == 'ok':
                    self.setting_chat_popup.dismiss()
            else:
                id_user = user['id_user']
                api = Api(session)
                response = api.request_post('delete_user_to_chat', {'id_user': id_user, 'id_chat': chat_id_global})

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
