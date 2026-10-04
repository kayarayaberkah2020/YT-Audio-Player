from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle
import threading
import yt_dlp

# --- DETEKSI SISTEM OPERASI ANDROID NATIVE ---
IS_ANDROID = False
try:
    from jnius import autoclass
    MediaPlayer = autoclass('android.media.MediaPlayer')
    AudioManager = autoclass('android.media.AudioManager')
    IS_ANDROID = True
except ImportError:
    pass

# Custom Button dengan Sudut Melengkung Modern (Rounded Corners)
class CyberButton(Button):
    def __init__(self, **kwargs):
        super(CyberButton, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.bold = True
        self.font_size = '14sp'
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.custom_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

class WinampCyberPlayer(App):
    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.07, 1)

        if IS_ANDROID:
            self.player = MediaPlayer()
            self.player.setAudioStreamType(AudioManager.STREAM_MUSIC)
        else:
            self.player = None
        self.is_paused = False

        root_scroll = ScrollView(size_hint=(1, 1))
        
        main_layout = BoxLayout(orientation='vertical', padding=25, spacing=18, size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # 1. HEADER TITLE BAR
        title_bar = BoxLayout(size_hint_y=None, height=40)
        title_label = Label(text="CYBER SONIC PLAYER v3.1", font_size='16sp', color=(0, 0.8, 1, 1), bold=True)
        title_bar.add_widget(title_label)
        main_layout.add_widget(title_bar)

        # 2. LCD DISPLAY PANEL
        lcd_container = BoxLayout(orientation='vertical', padding=15, size_hint_y=None, height=110)
        with lcd_container.canvas.before:
            Color(0.1, 0.1, 0.13, 1)
            RoundedRectangle(pos=lcd_container.pos, size=lcd_container.size, radius=[12])
        lcd_container.bind(pos=lambda obj, pos: lcd_container.canvas.before.clear() or lcd_container.canvas.before.add(Color(0.1, 0.1, 0.13, 1)) or lcd_container.canvas.before.add(RoundedRectangle(pos=pos, size=lcd_container.size, radius=[12])))

        self.status_label = Label(
            text="SYSTEM READY\nINTERNAL EXTRACTOR ACTIVE", font_size='13sp', color=(0.2, 1, 0.2, 1),
            bold=True, halign="center", valign="middle", line_height=1.3
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        lcd_container.add_widget(self.status_label)
        main_layout.add_widget(lcd_container)

        # 3. KOTAK INPUT LINK YOUTUBE (Tinggi disesuaikan menjadi lebih lega)
        input_box = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None, height=95)
        input_label = Label(text="PASTE YOUTUBE VIDEO LINK HERE:", font_size='11sp', color=(0.5, 0.5, 0.6, 1), halign="left")
        input_label.bind(size=input_label.setter('text_size'))
        
        self.url_input = TextInput(
            text="", 
            hint_text="https://youtube.com...", 
            multiline=False, 
            size_hint_y=None, 
            height=65,  # PERUBAHAN UTAMA: Kolom dibuat lebih tinggi
            font_size='14sp',  # Ukuran teks input dibuat lebih besar dan proporsional
            background_active='', 
            background_normal='', 
            background_color=(0.12, 0.12, 0.16, 1),
            foreground_color=(0, 0.9, 1, 1), 
            hint_text_color=(0.3, 0.3, 0.4, 1), 
            padding=[12, 22, 12, 12],  # Padding disesuaikan agar teks berada pas di tengah vertikal
            cursor_color=(0, 0.9, 1, 1)
        )
        input_box.add_widget(input_label)
        input_box.add_widget(self.url_input)
        main_layout.add_widget(input_box)

        # 4. GRID KONTROL TOMBOL NAVIGASI
        control_grid = GridLayout(cols=2, rows=2, spacing=12, size_hint_y=None, height=130)
        
        btn_play = CyberButton(text="▶  PLAY AUDIO")
        btn_play.custom_color = (0.1, 0.55, 0.2, 1)
        btn_play.bind(on_press=self.start_stream_thread)
        
        btn_pause = CyberButton(text="⏸  PAUSE")
        btn_pause.custom_color = (0.7, 0.4, 0.05, 1)
        btn_pause.bind(on_press=self.toggle_pause)
        
        btn_stop = CyberButton(text="⏹  STOP")
        btn_stop.custom_color = (0.65, 0.1, 0.1, 1)
        btn_stop.bind(on_press=self.stop_audio)
        
        btn_clear = CyberButton(text="🔄  CLEAR INPUT")
        btn_clear.custom_color = (0.25, 0.25, 0.3, 1)
        btn_clear.bind(on_press=self.clear_input)

        control_grid.add_widget(btn_play)
        control_grid.add_widget(btn_pause)
        control_grid.add_widget(btn_stop)
        control_grid.add_widget(btn_clear)
        main_layout.add_widget(control_grid)

        # 5. DEKORASI PANEL BAWAH
        eq_label = Label(text="───  ▪ ▪ ▪  DIGITAL AUDIO STREAMER  ▪ ▪ ▪  ───", font_size='10sp', color=(0.3, 0.3, 0.4, 1), size_hint_y=None, height=20)
        main_layout.add_widget(eq_label)

        root_scroll.add_widget(main_layout)
        return root_scroll

    def start_stream_thread(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = "ERROR:\nLINK CANNOT BE EMPTY!"
            return
        if self.is_paused:
            if IS_ANDROID and self.player:
                self.player.start()
            self.is_paused = False
            self.status_label.text = "PLAYING..."
            return
        self.status_label.text = "EXTRACTING AUDIO DIRECTLY...\nFROM YOUTUBE SERVER"
        threading.Thread(target=self.extract_and_play, args=(url,), daemon=True).start()

    def extract_and_play(self, youtube_url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'skip_download': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                audio_url = info['url']
                title = info.get('title', 'YOUTUBE AUDIO RETRO')
                
                if IS_ANDROID and self.player:
                    self.player.reset()
                    self.player.setDataSource(audio_url)
                    self.status_label.text = "LOADING AUDIO STREAM..."
                    self.player.prepare()
                    self.player.start()
                else:
                    self.status_label.text = "[SIMULATOR] LINK EXTRACTED OK"
                    print(f"Direct URL: {audio_url}")
                
                self.status_label.text = f"NOW PLAYING:\n{title[:45].upper()}"
                self.is_paused = False
        except Exception as e:
            self.status_label.text = "EXTRACTOR ERROR\nCHECK LINK OR INTERNET"
            print(f"Log Error: {e}")

    def toggle_pause(self, instance):
        if IS_ANDROID and self.player and self.player.isPlaying():
            self.player.pause()
            self.is_paused = True
            self.status_label.text = "AUDIO PAUSED"
        elif self.is_paused:
            if IS_ANDROID and self.player:
                self.player.start()
            self.is_paused = False
            self.status_label.text = "RESUMING PLAYBACK..."

    def stop_audio(self, instance):
        if IS_ANDROID and self.player:
            if self.player.isPlaying() or self.is_paused:
                self.player.stop()
                self.is_paused = False
                self.status_label.text = "PLAYING STOPPED"

    def clear_input(self, instance):
        self.url_input.text = ""
        self.status_label.text = "SYSTEM READY\nINSERT LINK TO START"

    def on_stop(self):
        if IS_ANDROID and self.player:
            self.player.release()

if __name__ == '__main__':
    WinampCyberPlayer().run()
