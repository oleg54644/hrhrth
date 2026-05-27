from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.app import App
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as C
from kivy.clock import Clock
from utils.ui import CircleBtn


class CallScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._call_id    = None
        self._caller_user = None
        self._timer       = None
        self._secs        = 0
        self._muted       = False

        # Gradient-like background (light blue-grey)
        with self.canvas.before:
            Color(*C('#EBF5FB'))
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd_bg, size=self._upd_bg)

        root = BoxLayout(orientation='vertical',
                         padding=[dp(24), dp(40)], spacing=dp(8))

        # Avatar circle
        self.lbl_avatar = Label(text='👤', font_size=dp(72),
                                size_hint_y=None, height=dp(100))
        root.add_widget(self.lbl_avatar)

        # Caller number
        self.lbl_who = Label(text='', font_size=dp(30), bold=True,
                             color=C('#2C3E50'), size_hint_y=None, height=dp(44))
        root.add_widget(self.lbl_who)

        # Status / timer
        self.lbl_status = Label(text='', font_size=dp(15), color=C('#5D6D7E'),
                                size_hint_y=None, height=dp(30))
        root.add_widget(self.lbl_status)

        root.add_widget(Label())

        # Controls row (mute / speaker)
        ctrl = BoxLayout(size_hint_y=None, height=dp(70),
                         spacing=dp(20), padding=[dp(50), 0])

        self.btn_mute = CircleBtn(text='🎤', bg='#D6EAF8',
                                  size_hint=(None,None), size=(dp(56),dp(56)))
        self.btn_mute.color = C('#2C3E50')
        self.btn_mute.bind(on_press=self.toggle_mute)

        self.btn_spk = CircleBtn(text='🔊', bg='#D6EAF8',
                                 size_hint=(None,None), size=(dp(56),dp(56)))
        self.btn_spk.color = C('#2C3E50')

        ctrl.add_widget(self.btn_mute)
        ctrl.add_widget(self.btn_spk)
        root.add_widget(ctrl)

        # ── Incoming buttons ───────────────────────────────────────────────
        self.row_inc = BoxLayout(size_hint_y=None, height=dp(90),
                                 spacing=dp(40), padding=[dp(60), 0])

        btn_rej = CircleBtn(text='📵', bg='#E74C3C',
                            size_hint=(None,None), size=(dp(70),dp(70)))
        btn_rej.bind(on_press=self.do_reject)

        btn_ans = CircleBtn(text='📞', bg='#2ECC71',
                            size_hint=(None,None), size=(dp(70),dp(70)))
        btn_ans.bind(on_press=self.do_answer)

        self.row_inc.add_widget(btn_rej)
        self.row_inc.add_widget(btn_ans)
        root.add_widget(self.row_inc)

        # ── Hangup button ──────────────────────────────────────────────────
        self.row_single = BoxLayout(size_hint_y=None, height=dp(90),
                                    padding=[0, dp(8)])
        self.row_single.add_widget(Label())
        btn_hup = CircleBtn(text='📵', bg='#E74C3C',
                            size_hint=(None,None), size=(dp(70),dp(70)))
        btn_hup.bind(on_press=self.do_hangup)
        self.row_single.add_widget(btn_hup)
        self.row_single.add_widget(Label())
        root.add_widget(self.row_single)

        root.add_widget(Label(size_hint_y=None, height=dp(20)))
        self.add_widget(root)
        self._hide_all()

    def _upd_bg(self, *_):
        self._bg.pos  = self.pos
        self._bg.size = self.size

    def _hide_all(self):
        self.row_inc.opacity    = 0
        self.row_single.opacity = 0

    # ── Public API ─────────────────────────────────────────────────────────

    def show_outgoing(self, number, call_id):
        self._call_id     = call_id
        self._caller_user = None
        self.lbl_who.text    = number
        self.lbl_status.text = 'Вызов…'
        self.row_inc.opacity    = 0
        self.row_single.opacity = 1

    def show_incoming(self, from_number, from_user, call_id):
        self._call_id      = call_id
        self._caller_user  = from_user
        self.lbl_who.text    = from_number
        self.lbl_status.text = 'Входящий звонок'
        self.row_inc.opacity    = 1
        self.row_single.opacity = 0

    def show_error(self, msg):
        self.lbl_status.text = f'⚠ {msg}'
        Clock.schedule_once(lambda dt: self._go_back(), 2)

    # ── Button handlers ────────────────────────────────────────────────────

    def do_answer(self, *_):
        app = App.get_running_app()
        app.ws.send({'type': 'answer',
                     'caller_user': self._caller_user,
                     'call_id': self._call_id})
        self.row_inc.opacity    = 0
        self.row_single.opacity = 1
        self.lbl_status.text    = '00:00'
        self._start_timer()

    def do_reject(self, *_):
        App.get_running_app().ws.send({'type': 'reject',
                                       'other_user': self._caller_user,
                                       'call_id': self._call_id})
        self._go_back()

    def do_hangup(self, *_):
        App.get_running_app().ws.send({'type': 'hangup',
                                       'other_user': self._caller_user,
                                       'call_id': self._call_id})
        self._go_back()

    def toggle_mute(self, *_):
        self._muted = not self._muted
        self.btn_mute.text     = '🔇' if self._muted else '🎤'
        self.btn_mute._bg_hex  = '#FADBD8' if self._muted else '#D6EAF8'
        self.btn_mute._draw()

    # ── Callbacks from app ─────────────────────────────────────────────────

    def on_answered(self, call_id):
        self.lbl_status.text = '00:00'
        self._start_timer()

    def on_remote_hangup(self, call_id):
        self._go_back()

    # ── Timer ──────────────────────────────────────────────────────────────

    def _start_timer(self):
        self._secs  = 0
        self._timer = Clock.schedule_interval(self._tick, 1)

    def _tick(self, dt):
        self._secs += 1
        m, s = divmod(self._secs, 60)
        self.lbl_status.text = f'{m:02}:{s:02}'

    def _go_back(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self._hide_all()
        self.manager.current = 'main'
