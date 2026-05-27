"""Общие UI-компоненты для светлой темы"""

from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.metrics import dp
from kivy.utils import get_color_from_hex

def C(h): return get_color_from_hex(h)


class FlatBtn(Button):
    """Прямоугольная кнопка с закруглёнными углами"""
    def __init__(self, bg='#2ECC71', fg='#FFFFFF', radius=10, **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_color  = (0,0,0,0)
        self._bg = C(bg); self._fg = C(fg)
        self.color = self._fg
        self.font_size = dp(15)
        self._r = radius
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[dp(self._r)])


class CircleBtn(Button):
    """Круглая кнопка"""
    def __init__(self, bg='#2ECC71', **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_color  = (0,0,0,0)
        self._bg_hex = bg
        self.color = (1,1,1,1)
        self.font_size = dp(22)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C(self._bg_hex))
            sz = min(self.width, self.height)
            Ellipse(pos=(self.center_x-sz/2, self.center_y-sz/2), size=(sz,sz))

    def set_bg(self, hex_color):
        self._bg_hex = hex_color
        self._draw()


class InputField(TextInput):
    def __init__(self, **kw):
        kw.setdefault('multiline', False)
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(50))
        kw.setdefault('font_size', dp(15))
        kw.setdefault('padding', [dp(14), dp(13)])
        kw.setdefault('background_color', C('#F5F7FA'))
        kw.setdefault('foreground_color', C('#2C3E50'))
        kw.setdefault('cursor_color', C('#2ECC71'))
        kw.setdefault('hint_text_color', C('#BDC3C7'))
        super().__init__(**kw)


class Card(BoxLayout):
    """Белая карточка с тенью-эффектом (закруглённый прямоугольник)"""
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(*C('#FFFFFF'))
            self._rect = RoundedRectangle(radius=[dp(12)])
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self._rect.pos  = self.pos
        self._rect.size = self.size
