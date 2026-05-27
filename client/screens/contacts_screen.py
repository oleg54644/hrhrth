import uuid
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.app import App
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as C
from utils.ui import FlatBtn, InputField


class ContactRow(BoxLayout):
    def __init__(self, c, on_call, on_del, **kw):
        super().__init__(orientation='horizontal',
                         size_hint_y=None, height=dp(62),
                         padding=[dp(12), dp(8)], spacing=dp(10), **kw)
        with self.canvas.before:
            Color(*C('#FFFFFF'))
            self._r = RoundedRectangle(radius=[dp(10)])
        self.bind(pos=self._u, size=self._u)

        self.add_widget(Label(text='👤', font_size=dp(26),
                              size_hint=(None,None), size=(dp(40),dp(40))))

        info = BoxLayout(orientation='vertical')
        n = Label(text=c.get('name',''), font_size=dp(14), bold=True,
                  color=C('#2C3E50'), halign='left', valign='middle')
        n.bind(size=n.setter('text_size'))
        num = Label(text=c.get('number',''), font_size=dp(12),
                    color=C('#7F8C8D'), halign='left', valign='middle')
        num.bind(size=num.setter('text_size'))
        info.add_widget(n); info.add_widget(num)
        self.add_widget(info)

        bc = Button(text='📞', font_size=dp(20),
                    size_hint=(None,None), size=(dp(42),dp(42)),
                    background_normal='', background_color=C('#E8F8F0'),
                    color=C('#2ECC71'))
        bc.bind(on_press=lambda _: on_call(c))
        self.add_widget(bc)

        bd = Button(text='🗑', font_size=dp(18),
                    size_hint=(None,None), size=(dp(42),dp(42)),
                    background_normal='', background_color=C('#FDEDEC'),
                    color=C('#E74C3C'))
        bd.bind(on_press=lambda _: on_del(c))
        self.add_widget(bd)

    def _u(self, *_):
        self._r.pos=self.pos; self._r.size=self.size


class ContactsScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)

        with self.canvas.before:
            Color(*C('#F5F7FA'))
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg,'pos',self.pos),
                  size=lambda *_: setattr(self._bg,'size',self.size))

        root = BoxLayout(orientation='vertical',
                         padding=dp(16), spacing=dp(10))

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(50))
        btn_back = Button(text='←', font_size=dp(22),
                          size_hint=(None,None), size=(dp(44),dp(44)),
                          background_normal='', background_color=(0,0,0,0),
                          color=C('#2C3E50'))
        btn_back.bind(on_press=lambda _: setattr(self.manager,'current','main'))
        hdr.add_widget(btn_back)
        hdr.add_widget(Label(text='Контакты', font_size=dp(20), bold=True,
                             color=C('#2C3E50')))
        hdr.add_widget(Label(size_hint_x=None, width=dp(44)))
        root.add_widget(hdr)

        # Add row
        add = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.tf_name = InputField(hint_text='Имя', height=dp(48))
        self.tf_num  = InputField(hint_text='Номер (напр. 100-1234)', height=dp(48))
        btn_add = Button(text='+', font_size=dp(24),
                         size_hint=(None,None), size=(dp(48),dp(48)),
                         background_normal='', background_color=C('#2ECC71'),
                         color=(1,1,1,1))
        btn_add.bind(on_press=self.add_contact)
        add.add_widget(self.tf_name); add.add_widget(self.tf_num)
        add.add_widget(btn_add)
        root.add_widget(add)

        sv = ScrollView()
        self.lst = GridLayout(cols=1, spacing=dp(6), size_hint_y=None,
                               padding=[0,dp(4)])
        self.lst.bind(minimum_height=self.lst.setter('height'))
        sv.add_widget(self.lst)
        root.add_widget(sv)
        self.add_widget(root)

    def on_enter(self): self._refresh()

    def _refresh(self):
        self.lst.clear_widgets()
        contacts = App.get_running_app().storage.load().get('contacts', [])
        if not contacts:
            self.lst.add_widget(Label(
                text='Нет контактов\nДобавьте первый!',
                font_size=dp(14), color=C('#BDC3C7'),
                halign='center', size_hint_y=None, height=dp(80)))
            return
        for c in contacts:
            self.lst.add_widget(
                ContactRow(c, on_call=self._call, on_del=self._delete))

    def add_contact(self, *_):
        name = self.tf_name.text.strip()
        num  = self.tf_num.text.strip()
        if not num: return
        app = App.get_running_app()
        data = app.storage.load()
        contacts = data.get('contacts', [])
        contacts = [c for c in contacts if c['number'] != num]
        contacts.append({'name': name or num, 'number': num})
        data['contacts'] = contacts
        app.storage.save(data)
        self.tf_name.text = ''; self.tf_num.text = ''
        self._refresh()

    def _call(self, c):
        call_id = str(uuid.uuid4())
        app = App.get_running_app()
        app.ws.send({'type': 'call', 'to': c['number'], 'call_id': call_id})
        cs = self.manager.get_screen('call')
        cs.show_outgoing(c['number'], call_id)
        self.manager.current = 'call'

    def _delete(self, c):
        app = App.get_running_app()
        data = app.storage.load()
        data['contacts'] = [x for x in data.get('contacts',[])
                            if x['number'] != c['number']]
        app.storage.save(data)
        self._refresh()
