import threading
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.app import App
from kivy.metrics import dp
from kivy.clock import Clock
from utils.ui import FlatBtn, InputField, C


class RegisterScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation='vertical', padding=dp(32), spacing=dp(12))

        root.add_widget(Label(size_hint_y=None, height=dp(30)))
        root.add_widget(Label(text='Регистрация', font_size=dp(26), bold=True,
                              color=C('#2C3E50'), size_hint_y=None, height=dp(42)))
        root.add_widget(Label(
            text='Вам будет выдан случайный номер телефона',
            font_size=dp(13), color=C('#7F8C8D'),
            size_hint_y=None, height=dp(28)))
        root.add_widget(Label(size_hint_y=None, height=dp(8)))

        self.tf_server = InputField(hint_text='Адрес сервера (http://1.2.3.4:8080)')
        self.tf_user   = InputField(hint_text='Логин (только латиница)')
        self.tf_pass   = InputField(hint_text='Пароль', password=True)
        self.tf_pass2  = InputField(hint_text='Повторите пароль', password=True)

        for w in (self.tf_server, self.tf_user, self.tf_pass, self.tf_pass2):
            root.add_widget(w)

        self.lbl_status = Label(text='', font_size=dp(13),
                                color=C('#E74C3C'),
                                size_hint_y=None, height=dp(28),
                                halign='center')
        self.lbl_status.bind(size=self.lbl_status.setter('text_size'))
        root.add_widget(self.lbl_status)

        btn = FlatBtn(text='Зарегистрироваться', size_hint_y=None, height=dp(52))
        btn.bind(on_press=self.do_register)
        root.add_widget(btn)

        back = FlatBtn(text='← Назад', bg='#95A5A6', size_hint_y=None, height=dp(46))
        back.bind(on_press=lambda _: setattr(self.manager, 'current', 'login'))
        root.add_widget(back)

        root.add_widget(Label())
        self.add_widget(root)

    def do_register(self, *_):
        server   = self.tf_server.text.strip() or 'http://localhost:8080'
        username = self.tf_user.text.strip().lower()
        pwd      = self.tf_pass.text.strip()
        pwd2     = self.tf_pass2.text.strip()

        if not username or not pwd:
            self._status('Заполните все поля', error=True); return
        if pwd != pwd2:
            self._status('Пароли не совпадают', error=True); return
        if len(pwd) < 4:
            self._status('Пароль минимум 4 символа', error=True); return

        self._status('Регистрация…', error=False)
        app = App.get_running_app()
        app.storage.save({'server': server})

        def _thread():
            data, err = app.api.register(username, pwd)
            Clock.schedule_once(lambda dt: self._done(data, err, server), 0)

        threading.Thread(target=_thread, daemon=True).start()

    def _done(self, data, err, server):
        if err:
            self._status(f'Ошибка: {err}', error=True); return
        app = App.get_running_app()
        app.storage.save({
            'server': server,
            'token': data['token'],
            'username': data['username'],
            'number': data['number'],
        })
        app.ws.connect(data['token'])
        self._status(f'✅ Ваш номер: {data["number"]}', error=False)
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'main'), 1.5)

    def _status(self, msg, error=True):
        self.lbl_status.color = C('#E74C3C') if error else C('#27AE60')
        self.lbl_status.text  = msg
