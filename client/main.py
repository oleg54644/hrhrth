"""VoIP Phone Client — Kivy"""

import os
os.environ['KIVY_NO_CONSOLELOG'] = '0'

from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '800')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

from screens.login_screen    import LoginScreen
from screens.register_screen import RegisterScreen
from screens.main_screen     import MainScreen
from screens.call_screen     import CallScreen
from screens.contacts_screen import ContactsScreen
from utils.storage           import Storage
from utils.api_client        import APIClient
from utils.ws_client         import WSClient


class PhoneApp(App):
    # Светлая палитра
    C_BG       = get_color_from_hex('#FFFFFF')
    C_SURFACE  = get_color_from_hex('#F5F7FA')
    C_PRIMARY  = get_color_from_hex('#2ECC71')   # зелёный
    C_DANGER   = get_color_from_hex('#E74C3C')   # красный
    C_ACCENT   = get_color_from_hex('#3498DB')   # синий
    C_TEXT     = get_color_from_hex('#2C3E50')
    C_SUBTEXT  = get_color_from_hex('#7F8C8D')
    C_BORDER   = get_color_from_hex('#ECF0F1')

    def build(self):
        Window.clearcolor = self.C_BG

        self.storage    = Storage()
        self.api        = APIClient(self.storage)
        self.ws         = WSClient(self)

        self.sm = ScreenManager(transition=FadeTransition(duration=0.15))
        for name, cls in [
            ('login',    LoginScreen),
            ('register', RegisterScreen),
            ('main',     MainScreen),
            ('call',     CallScreen),
            ('contacts', ContactsScreen),
        ]:
            self.sm.add_widget(cls(name=name))

        saved = self.storage.load()
        if saved.get('token'):
            self.sm.current = 'main'
            self.ws.connect(saved['token'])
        else:
            self.sm.current = 'login'

        return self.sm

    def on_pause(self):   return True
    def on_resume(self):  pass
    def on_stop(self):    self.ws.disconnect()

    # ── Global callbacks called by WSClient ───────────────────────────────
    def on_incoming_call(self, from_number, from_user, call_id):
        from kivy.clock import Clock
        def _show(dt):
            cs = self.sm.get_screen('call')
            cs.show_incoming(from_number, from_user, call_id)
            self.sm.current = 'call'
        Clock.schedule_once(_show, 0)

    def on_call_answered(self, call_id):
        from kivy.clock import Clock
        Clock.schedule_once(
            lambda dt: self.sm.get_screen('call').on_answered(call_id), 0)

    def on_call_hangup(self, call_id):
        from kivy.clock import Clock
        Clock.schedule_once(
            lambda dt: self.sm.get_screen('call').on_remote_hangup(call_id), 0)


if __name__ == '__main__':
    PhoneApp().run()
