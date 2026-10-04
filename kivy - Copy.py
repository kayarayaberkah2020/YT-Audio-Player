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
import requests

# --- PROTEKSI ANTI CRASH: Deteksi Perangkat Android Native ---
IS_ANDROID = False
try:
    from jnius import autoclass
    MediaPlayer = autoclass('android.media.MediaPlayer')
    AudioManager = autoclass('android.media.AudioManager')
    IS_ANDROID = True
except ImportError:
    pass

# Custom Button dengan Efek Sudut Membulat (Rounded Corners) untuk UI Keren
class CyberButton(Button):
    def __init__(self, **kwargs):
        super(CyberButton, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0) # Menghapus warna default Kivy
        self.bold = True
        self.font_size = '14sp'
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.custom_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])

class WinampCyberPlayer(App):
    def build(self):
        # Mengatur warna latar belakang utama (Hitam Arang Cyberpunk)
        Window.clearcolor = (0.05, 0.05, 0.07, 1)

        # Inisialisasi Player Android
        if IS_ANDROID:
            self.player = MediaPlayer()
            self.player.setAudioStreamType(AudioManager.STREAM_MUSIC)
        else:
            self.player = None
        self.is_paused = False

        # Container Utama Berbasis ScrollView agar responsif di HP mana saja
        root_scroll = ScrollView(size_hint=(1, 1))
        
        # Tata letak konten vertikal
        main_layout = BoxLayout(orientation='vertical', padding=25, spacing=18, size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # 1. HEADER / TITLE BAR (Gaya Neon Cyber)
        title_bar = BoxLayout(size_hint_y=None, height=40)
        title_label = Label(
            text="CYBER SONIC PLAYER v2.0", 
            font_size='16sp', 
            color=(0, 0.8, 1, 1), # Biru Cyan Terang
            bold=True
        )
        title_bar.add_widget(title_label)
        main_layout.add_widget(title_bar)

        # 2. LCD DISPLAY PANEL (Desain Dashboard Musik Digital)
        lcd_container = BoxLayout(orientation='vertical', padding=15, size_hint_y=None, height=110)
        with lcd_container.canvas.before:
            Color(0.1, 0.1, 0.13, 1) # Latar panel abu-abu kontras
            RoundedRectangle(pos=lcd_container.pos, size=lcd_container.size, radius=[12])
        lcd_container.bind(pos=lambda obj, pos: lcd_container.canvas.before.clear() or lcd_container.canvas.before.add(Color(0.1, 0.1, 0.13, 1)) or lcd_container.canvas.before.add(RoundedRectangle(pos=pos, size=lcd_container.size, radius=[12])))

        self.status_label = Label(
            text="SYSTEM READY\nINSERT LINK TO START", 
            font_size='13sp', 
            color=(0.2, 1, 0.2, 1), # Hijau Fosfor Digital
            bold=True,
            halign="center",
            valign="middle",
            line_height=1.3
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        lcd_container.add_widget(self.status_label)
        main_layout.add_widget(lcd_container)

        # 3. INPUT SLOT AREA
        input_box = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None, height=80)
        input_label = Label(text="PASTE YOUTUBE VIDEO LINK HERE:", font_size='11sp', color=(0.5, 0.5, 0.6, 1), halign="left")
        input_label.bind(size=input_label.setter('text_size'))
        
        self.url_input = TextInput(
            text="", 
            hint_text="https://youtube.com...", 
            multiline=False, 
            size_hint_y=None, 
            height=48,
            background_active='',
            background_normal='',
            background_color=(0.12, 0.12, 0.16, 1), # Kotak input gelap modern
            foreground_color=(0, 0.9, 1, 1), # Teks Cyan saat mengetik
            hint_text_color=(0.3, 0.3, 0.4, 1),
            padding=[12, 12, 12, 12],
            cursor_color=(0, 0.9, 1, 1)
        )
        input_box.add_widget(input_label)
        input_box.add_widget(self.url_input)
        main_layout.add_widget(input_box)

        # 4. GRID KONTROL TOMBOL UTAMA (Elegan & Berwarna tegas)
        control_grid = GridLayout(cols=2, rows=2, spacing=12, size_hint_y=None, height=130)
        
        # Tombol Play (Hijau)
        btn_play = CyberButton(text="▶  PLAY AUDIO")
        btn_play.custom_color = (0.1, 0.55, 0.2, 1)
        btn_play.bind(on_press=self.start_stream_thread)
        
        # Tombol Pause (Jingga)
        btn_pause = CyberButton(text="⏸  PAUSE")
        btn_pause.custom_color = (0.7, 0.4, 0.05, 1)
        btn_pause.bind(on_press=self.toggle_pause)
        
        # Tombol Stop (Merah)
        btn_stop = CyberButton(text="⏹  STOP")
        btn_stop.custom_color = (0.65, 0.1, 0.1, 1)
        btn_stop.bind(on_press=self.stop_audio)
        
        # Tombol Clear (Abu-abu)
        btn_clear = CyberButton(text="🔄  CLEAR INPUT")
        btn_clear.custom_color = (0.25, 0.25, 0.3, 1)
        btn_clear.bind(on_press=self.clear_input)

        control_grid.add_widget(btn_play)
        control_grid.add_widget(btn_pause)
        control_grid.add_widget(btn_stop)
        control_grid.add_widget(btn_clear)
        main_layout.add_widget(control_grid)

        # 5. RETRO EQUALIZER VISUALIZER DECORATION
        eq_label = Label(
            text="───  ▪ ▪ ▪  DIGITAL SIGNAL PROCESSOR  ▪ ▪ ▪  ───", 
            font_size='10sp', 
            color=(0.3, 0.3, 0.4, 1),
            size_hint_y=None, 
            height=20
        )
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
        self.status_label.text = "ANALYZING VIDEO LINK...\nPLEASE WAIT"
        threading.Thread(target=self.extract_and_play, args=(url,), daemon=True).start()

    def extract_and_play(self, youtube_url):
        try:
            # Menggunakan Server API Publik V2 yang sangat andal
            api_endpoint = "https://download4.cc"
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            payload = {"url": youtube_url, "type": "audio"}
            
            response = requests.post(api_endpoint, json=payload, headers=headers, timeout=15)
            data = response.json()
            
            if response.status_code == 200 and "data" in data:
                task_data = data["data"]
                audio_url = task_data.get("downloadUrl") or task_data.get("url")
                title = task_data.get("title", "CYBER RETRO AUDIO")
                
                if not audio_url:
                    self.status_label.text = "API CONVERSION FAILED\nTRY ANOTHER LINK"
                    return
                
                if IS_ANDROID and self.player:
                    self.player.reset()
                    self.player.setDataSource(audio_url)
                    self.status_label.text = "ESTABLISHING STREAM..."
                    self.player.prepare()
                    self.player.start()
                else:
                    self.status_label.text = "[SIMULATION MODE]\nSTREAM CONNECTED OK!"
                    print(f"Direct Audio Link: {audio_url}")
                
                self.status_label.text = f"NOW PLAYING:\n{title[:45].upper()}"
                self.is_paused = False
            else:
                self.status_label.text = "SERVER BUSY\nPLEASE TRY AGAIN"
        except Exception as e:
            self.status_label.text = "CONNECTION ERROR\nCHECK YOUR INTERNET"

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
                self.status_label.text = "PLAYBACK STOPPED"

    def clear_input(self, instance):
        self.url_input.text = ""
        self.status_label.text = "SYSTEM READY\nINSERT LINK TO START"

    def on_stop(self):
        if IS_ANDROID and self.player:
            self.player.release()

if __name__ == '__main__':
    WinampCyberPlayer().run()
