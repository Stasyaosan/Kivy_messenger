import config
import requests
import json

class Api:
    def __init__(self, token):
        self.token = token

    def request_post(self, method, params=None):
        url = f'{config.URL}{method}'

        if params != None:
            params['token'] = self.token

            data = requests.post(url, data=params)
        else:
            data = requests.post(url)

        return json.loads(data.text)


class Auth:
    def __init__(self, login, password):
        self.login = login
        self.password = password

    def get_token(self):
        try:
            url = f'{config.URL}auth/'
            token = requests.post(url, data={'login': self.login, 'password': self.password})
            return json.loads(token.text)
        except:
            return 'Error'

token = Auth('qwe@qwe.ru', 'qwe@qwe.ru').get_token()
api = Api(token['token'])
print(api.request_post('get_chats', {'id_user': 13}))
