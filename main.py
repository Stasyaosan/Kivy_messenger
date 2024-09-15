from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.label import Label


class LoginScreen(Screen):
    def validate_user(self):
        username = self.ids.usernameinput.text
        password = self.ids.passwordinput.text

        if username == "admin" and password == "1234":
            self.manager.current = "home"
        else:
            self.showinvalid_login_popup()

    def show_invalid_login_popup(self):
        popup = Popup(title='Invalid Login',
                      content=Label(text='Incorrect username or password.'),
                      size_hint=(0.6, 0.4))
        popup.open()


class HomeScreen(Screen):
    pass


class LoginApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(HomeScreen(name='home'))
        return sm


if __name__ == '__main__':
    LoginApp().run()
