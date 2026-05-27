import uuid
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Ellipse, Rectangle
from kivy.app import App
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as C


class DialKey(Button):
    def __init__(self, digit, sub='', **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_color  = (0,0,0,0)
        self.color = C('#2C3E50')
        self.font_size = dp(24)
        self.bold = True
        self.markup = True
        sub_part = f'\n[size=10][color=7F8C8D]{sub}[/color][/size]' if sub else ''
        self.text = digit + sub_part
        self.bind(pos=self._draw, size=self._draw)
        self.bind(on_press=self._press_anim)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C('#F0F3F7'))
            sz = min(self.width, self.height) * 0.78
            Ellipse(pos=(self.center_x-sz/2, self.center_y-sz/2), size=(sz,sz))

    def _press_anim(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C('#D5E8D4'))
            sz = min(self.width, self.height) * 0.78
            Ellipse(pos=(self.center_x-sz/2, self.center_y-sz/2), size=(sz,sz))
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._draw(), 0.1)


class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        # White background
        with self.canvas.before:
            Color(*C('#FFFFFF'))
            Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: None, size=lambda *_: None)

        root = BoxLayout(orientation='vertical',
                         padding=[dp(16), dp(12)], spacing=dp(4))

        # ── Top bar ────────────────────────────────────────────────────────
        top = BoxLayout(size_hint_y=None, height=dp(54), spacing=dp(8))

        self.lbl_number = Label(
            text='Ваш номер: …', font_size=dp(13),
            color=C('#7F8C8D'), halign='left', valign='middle')
        self.lbl_number.bind(size=self.lbl_number.setter('text_size'))

        def icon_btn(txt, bg):
            b = Button(text=txt, font_size=dp(18),
                       size_hint=(None,None), size=(dp(44),dp(44)),
                       background_normal='', background_color=(0,0,0,0))
            with b.canvas.before:
                Color(*C(bg))
                RoundedRectangle(pos=b.pos, size=b.size, radius=[dp(10)])
            b.bind(pos=lambda *_,btn=b,c=bg: self._redraw_icon(btn,c),
                   size=lambda *_,btn=b,c=bg: self._redraw_icon(btn,c))
            return b

        btn_contacts = icon_btn('👥', '#E8F8F0')
        btn_contacts.color = C('#2ECC71')
        btn_contacts.bind(on_press=lambda _: setattr(self.manager,'current','contacts'))

        btn_logout = icon_btn('⏏', '#FDEDEC')
        btn_logout.color = C('#E74C3C')
        btn_logout.bind(on_press=self.do_logout)

        top.add_widget(self.lbl_number)
        top.add_widget(btn_contacts)
        top.add_widget(btn_logout)
        root.add_widget(top)

        # ── Number display ─────────────────────────────────────────────────
        self.lbl_input = Label(
            text='', font_size=dp(28), bold=True,
            color=C('#2C3E50'), size_hint_y=None, height=dp(50),
            halign='center')
        self.lbl_input.bind(size=self.lbl_input.setter('text_size'))
        root.add_widget(self.lbl_input)

        # ── Dialpad ────────────────────────────────────────────────────────
        grid = GridLayout(cols=3, size_hint_y=None, spacing=dp(4))
        grid.bind(minimum_height=grid.setter('height'))

        keys = [
            ('1',''),('2','АБВ'),('3','ГДЕ'),
            ('4','ЖЗИ'),('5','КЛМ'),('6','НОП'),
            ('7','РСТ'),('8','УФХ'),('9','ЦЧШ'),
            ('*',''),('0','+'),('#',''),
        ]
        for d,s in keys:
            k = DialKey(d, s, size_hint_y=None, height=dp(72))
            k.bind(on_press=lambda btn,digit=d: self._type(digit))
            grid.add_widget(k)

        root.add_widget(grid)

        # ── Bottom row ─────────────────────────────────────────────────────
        bot = BoxLayout(size_hint_y=None, height=dp(88),
                        spacing=dp(16), padding=[dp(50), dp(8)])

        from utils.ui import CircleBtn
        btn_del = CircleBtn(text='⌫', bg='#ECF0F1',
                            size_hint=(None,None), size=(dp(58),dp(58)))
        btn_del.color = C('#2C3E50')
        btn_del.bind(on_press=lambda _: self._del())

        btn_call = CircleBtn(text='📞', bg='#2ECC71',
                             size_hint=(None,None), size=(dp(72),dp(72)))
        btn_call.bind(on_press=self.do_call)

        btn_empty = Label(size_hint=(None,None), size=(dp(58),dp(58)))

        bot.add_widget(btn_del)
        bot.add_widget(btn_call)
        bot.add_widget(btn_empty)
        root.add_widget(bot)
        root.add_widget(Label())
        self.add_widget(root)

    def _redraw_icon(self, btn, bg):
        btn.canvas.before.clear()
        with btn.canvas.before:
            Color(*C(bg))
            RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(10)])

    def on_enter(self):
        s = App.get_running_app().storage.load()
        if s.get('number'):
            self.lbl_number.text = f'Ваш номер: {s["number"]}'

    def _type(self, d):
        self.lbl_input.text += d

    def _del(self):
        self.lbl_input.text = self.lbl_input.text[:-1]

    def do_call(self, *_):
        number = self.lbl_input.text.strip()
        if not number:
            return
        call_id = str(uuid.uuid4())
        app = App.get_running_app()
        app.ws.send({'type': 'call', 'to': number, 'call_id': call_id})
        cs = self.manager.get_screen('call')
        cs.show_outgoing(number, call_id)
        self.manager.current = 'call'

    def do_logout(self, *_):
        app = App.get_running_app()
        app.ws.disconnect()
        app.storage.clear()
        self.manager.current = 'login'
