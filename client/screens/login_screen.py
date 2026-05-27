import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import App
from kivy.metrics import dp
from kivy.clock import Clock
from utils.ui import FlatBtn, InputField, C


class LoginScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(32), spacing=dp(14))

        root.add_widget(Label(size_hint_y=None, height=dp(50)))

        # Logo
        root.add_widget(Label(text='📞', font_size=dp(56),
                              size_hint_y=None, height=dp(70)))
        root.add_widget(Label(text='VoIP Phone', font_size=dp(26), bold=True,
                              color=C('#2C3E50'), size_hint_y=None, height=dp(40)))
        root.add_widget(Label(text='Войдите в аккаунт', font_size=dp(13),
                              color=C('#7F8C8D'), size_hint_y=None, height=dp(28)))
        root.add_widget(Label(size_hint_y=None, height=dp(10)))

        # Server
        self.tf_server = InputField(hint_text='Адрес сервера (напр. http://1.2.3.4:8080)')
        saved = App.get_running_app().storage.load() if App.get_running_app() else {}
        self.tf_server.text = saved.get('server', '')
        root.add_widget(self.tf_server)

        # Credentials
        self.tf_user = InputField(hint_text='Логин')
        self.tf_pass = InputField(hint_text='Пароль', password=True)
        root.add_widget(self.tf_user)
        root.add_widget(self.tf_pass)

        self.lbl_err = Label(text='', color=C('#E74C3C'), font_size=dp(13),
                             size_hint_y=None, height=dp(24))
        root.add_widget(self.lbl_err)

        btn_login = FlatBtn(text='Войти', size_hint_y=None, height=dp(52))
        btn_login.bind(on_press=self.do_login)
        root.add_widget(btn_login)

        btn_reg = FlatBtn(text='Создать аккаунт', bg='#3498DB',
                          size_hint_y=None, height=dp(48))
        btn_reg.bind(on_press=lambda _: setattr(self.manager, 'current', 'register'))
        root.add_widget(btn_reg)

        root.add_widget(Label())
        self.add_widget(root)

    def do_login(self, *_):
        server   = self.tf_server.text.strip() or 'http://localhost:8080'
        username = self.tf_user.text.strip().lower()
        password = self.tf_pass.text.strip()

        if not username or not password:
            self.lbl_err.text = 'Введите логин и пароль'
            return

        self.lbl_err.text = 'Подключение…'
        app = App.get_running_app()
        app.storage.save({'server': server})    # save server first

        def _thread():
            data, err = app.api.login(username, password)
            Clock.schedule_once(lambda dt: self._done(data, err, server), 0)

        threading.Thread(target=_thread, daemon=True).start()

    def _done(self, data, err, server):
        if err:
            self.lbl_err.text = f'Ошибка: {err}'
            return
        app = App.get_running_app()
        app.storage.save({
            'server': server,
            'token': data['token'],
            'username': data['username'],
            'number': data['number'],
        })
        app.ws.connect(data['token'])
        self.manager.current = 'main'
