import threading
import socket
import re
import random
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
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

# Komponen Tombol Cyberpunk dengan Efek Border & State
class CyberButton(Button):
    def __init__(self, bg_color=(0.12, 0.15, 0.22, 1), border_color=(0, 0.85, 1, 0.8), **kwargs):
        super(CyberButton, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.bold = True
        self.font_size = '13sp'
        self.custom_bg = bg_color
        self.custom_border = border_color
        self.bind(pos=self.redraw, size=self.redraw, state=self.redraw)

    def redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Warna saat ditekan sedikit lebih terang
            if self.state == 'down':
                Color(self.custom_bg[0] * 1.5, self.custom_bg[1] * 1.5, self.custom_bg[2] * 1.5, 1)
            else:
                Color(*self.custom_bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
            
            # Glowing border
            Color(*self.custom_border)
            Line(rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], 8), width=1.1)

class WinampCyberPlayer(App):
    def build(self):
        Window.clearcolor = (0.04, 0.05, 0.07, 1)

        if IS_ANDROID:
            self.player = MediaPlayer()
            self.player.setAudioStreamType(AudioManager.STREAM_MUSIC)
        else:
            self.player = None
            
        self.is_paused = False
        self.is_playing = False
        self.eq_event = None

        root_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        main_layout = BoxLayout(orientation='vertical', padding=[20, 25, 20, 25], spacing=16, size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))

        # 1. HEADER TITLE BAR (CYBER BRANDING)
        header_box = BoxLayout(orientation='vertical', size_hint_y=None, height=48, spacing=3)
        title_label = Label(text="⚡ CYBER SONIC PRO", font_size='18sp', color=(0, 0.9, 1, 1), bold=True)
        sub_label = Label(text="ULTRA-LOW LATENCY STREAM ENGINE v4.0", font_size='10sp', color=(0.4, 0.5, 0.65, 1))
        header_box.add_widget(title_label)
        header_box.add_widget(sub_label)
        main_layout.add_widget(header_box)

        # 2. LCD DISPLAY PANEL DENGAN CYBER FRAME
        self.lcd_container = BoxLayout(orientation='vertical', padding=[16, 12, 16, 12], spacing=6, size_hint_y=None, height=130)
        self.lcd_container.bind(pos=self._update_lcd_canvas, size=self._update_lcd_canvas)

        self.lcd_mode = Label(
            text="STATUS: STANDBY // BUFFER: READY", 
            font_size='10sp', 
            color=(0, 0.7, 0.9, 0.8), 
            size_hint_y=None, 
            height=16,
            halign="left"
        )
        self.lcd_mode.bind(size=self.lcd_mode.setter('text_size'))

        self.status_label = Label(
            text="SYSTEM ONLINE\nREADY TO STREAM AUDIO", 
            font_size='13sp', 
            color=(0.15, 1.0, 0.4, 1),
            bold=True, 
            halign="center", 
            valign="middle", 
            line_height=1.2
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))

        # Visual Equalizer Bar Mini
        self.eq_bar = Label(
            text="▪  ▪  ▪  IDLE  ▪  ▪  ▪", 
            font_size='11sp', 
            color=(0, 0.85, 1, 0.7), 
            size_hint_y=None, 
            height=20,
            halign="center"
        )
        self.eq_bar.bind(size=self.eq_bar.setter('text_size'))

        self.lcd_container.add_widget(self.lcd_mode)
        self.lcd_container.add_widget(self.status_label)
        self.lcd_container.add_widget(self.eq_bar)
        main_layout.add_widget(self.lcd_container)

        # 3. KOTAK INPUT LINK YOUTUBE
        input_container = BoxLayout(orientation='vertical', spacing=6, size_hint_y=None, height=90)
        lbl_target = Label(text="INPUT TARGET STREAM URL:", font_size='11sp', color=(0.55, 0.65, 0.75, 1), halign="left")
        lbl_target.bind(size=lbl_target.setter('text_size'))
        
        self.url_input = TextInput(
            hint_text="https://youtu.be/... or paste YouTube URL", 
            multiline=False, 
            size_hint_y=None, 
            height=58,
            font_size='13sp', 
            background_active='', 
            background_normal='', 
            background_color=(0.08, 0.1, 0.14, 1),
            foreground_color=(0.9, 0.95, 1, 1), 
            hint_text_color=(0.35, 0.4, 0.5, 1), 
            padding=[14, 18, 14, 14],
            cursor_color=(0, 0.9, 1, 1)
        )
        input_container.add_widget(lbl_target)
        input_container.add_widget(self.url_input)
        main_layout.add_widget(input_container)

        # 4. GRID KONTROL TOMBOL NAVIGASI
        control_grid = GridLayout(cols=2, rows=2, spacing=12, size_hint_y=None, height=125)
        
        btn_play = CyberButton(
            text="▶   PLAY STREAM", 
            bg_color=(0.06, 0.35, 0.18, 1), 
            border_color=(0.2, 0.9, 0.3, 0.8)
        )
        btn_play.bind(on_press=self.start_stream_thread)
        
        btn_pause = CyberButton(
            text="⏸   PAUSE", 
            bg_color=(0.4, 0.25, 0.05, 1), 
            border_color=(1, 0.7, 0.1, 0.8)
        )
        btn_pause.bind(on_press=self.toggle_pause)
        
        btn_stop = CyberButton(
            text="⏹   STOP", 
            bg_color=(0.4, 0.08, 0.1, 1), 
            border_color=(1, 0.2, 0.25, 0.8)
        )
        btn_stop.bind(on_press=self.stop_audio)
        
        btn_clear = CyberButton(
            text="↺   RESET URL", 
            bg_color=(0.14, 0.18, 0.25, 1), 
            border_color=(0.4, 0.55, 0.8, 0.6)
        )
        btn_clear.bind(on_press=self.clear_input)

        control_grid.add_widget(btn_play)
        control_grid.add_widget(btn_pause)
        control_grid.add_widget(btn_stop)
        control_grid.add_widget(btn_clear)
        main_layout.add_widget(control_grid)

        # 5. FOOTER STATUS
        footer_label = Label(
            text="AUDIO ENGINE RUNNING // KIVY & YT-DLP CORE", 
            font_size='9sp', 
            color=(0.3, 0.38, 0.45, 1), 
            size_hint_y=None, 
            height=25
        )
        main_layout.add_widget(footer_label)

        root_scroll.add_widget(main_layout)
        return root_scroll

    def _update_lcd_canvas(self, instance, value):
        self.lcd_container.canvas.before.clear()
        with self.lcd_container.canvas.before:
            Color(0.06, 0.07, 0.1, 1)
            RoundedRectangle(pos=self.lcd_container.pos, size=self.lcd_container.size, radius=[10])
            Color(0, 0.6, 0.9, 0.5)
            Line(rounded_rectangle=(self.lcd_container.pos[0], self.lcd_container.pos[1], 
                                    self.lcd_container.size[0], self.lcd_container.size[1], 10), width=1.2)

    # --- EQUALIZER VISUALIZER EFFECT ---
    def _animate_eq(self, dt):
        chars = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        eq_str = "".join([random.choice(chars) + " " for _ in range(14)])
        self.eq_bar.text = f"♬  {eq_str} ♬"
        self.eq_bar.color = (0, 0.9, 1, 1)

    def _start_visualizer(self):
        if not self.eq_event:
            self.eq_event = Clock.schedule_interval(self._animate_eq, 0.15)

    def _stop_visualizer(self, idle_text="▪  ▪  ▪  IDLE  ▪  ▪  ▪"):
        if self.eq_event:
            self.eq_event.cancel()
            self.eq_event = None
        self.eq_bar.text = idle_text
        self.eq_bar.color = (0, 0.6, 0.8, 0.5)

    # --- UPDATE UI SECARA THREAD-SAFE ---
    def set_status(self, text, color=(0.15, 1.0, 0.4, 1), mode_info="STATUS: ACTIVE"):
        def _update(dt):
            self.status_label.text = text
            self.status_label.color = color
            self.lcd_mode.text = mode_info
        Clock.schedule_once(_update)

    # --- CEK INTERNET RINGAN ---
    def check_internet(self):
        try:
            # Cek socket cepat ke DNS Google (port 53) timeout 2.5 detik
            socket.setdefaulttimeout(2.5)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except (socket.timeout, OSError):
            return False

    def start_stream_thread(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.set_status("INPUT ERROR:\nPLEASE PASTE YOUTUBE LINK", color=(1, 0.3, 0.3, 1), mode_info="ERR // NO_URL")
            return

        if self.is_paused:
            if IS_ANDROID and self.player:
                self.player.start()
            self.is_paused = False
            self.is_playing = True
            self._start_visualizer()
            self.set_status("STREAM RESUMED", mode_info="STATE: PLAYING")
            return

        self.set_status("INITIALIZING...\nVERIFYING CONNECTION & LINK", color=(0, 0.85, 1, 1), mode_info="STATE: RESOLVING")
        threading.Thread(target=self.extract_and_play, args=(url,), daemon=True).start()

    def extract_and_play(self, youtube_url):
        # 1. Pengecekan koneksi internet aktif
        if not self.check_internet():
            self.set_status("NETWORK ERROR:\nNO INTERNET CONNECTION DETECTED", color=(1, 0.25, 0.25, 1), mode_info="ERR // OFFLINE")
            self._stop_visualizer("DISCONNECTED")
            return

        self.set_status("EXTRACTING AUDIO STREAM...\nPLEASE WAIT A MOMENT", color=(1, 0.8, 0.2, 1), mode_info="ENGINE: YT-DLP ACTIVE")

        # 2. Opsi yt-dlp yang dioptimalkan agar tidak dicekal YouTube
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'socket_timeout': 12,
            'nocheckcertificate': True,
            # Emulasi klien resmi untuk bypass proteksi bot
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36'
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                if not info:
                    raise Exception("Gagal mengekstrak data dari URL")

                audio_url = info.get('url')
                title = info.get('title', 'LIVE AUDIO STREAM')

                if IS_ANDROID and self.player:
                    self.set_status("BUFFERING MEDIA STREAM...", color=(0, 0.85, 1, 1), mode_info="BUFFERING // ANDROID")
                    self.player.reset()
                    self.player.setDataSource(audio_url)
                    self.player.prepare()
                    self.player.start()
                else:
                    print(f"\n[STREAM OK] Audio Direct URL:\n{audio_url}\n")

                self.is_playing = True
                self.is_paused = False
                Clock.schedule_once(lambda dt: self._start_visualizer())
                self.set_status(f"NOW PLAYING:\n{title[:42].upper()}", color=(0.15, 1.0, 0.4, 1), mode_info="PLAYING // HI-RES STREAM")

        except Exception as e:
            err_str = str(e).lower()
            if "unsupported url" in err_str or "not a valid" in err_str:
                self.set_status("INVALID URL:\nNOT A SUPPORTED YOUTUBE LINK", color=(1, 0.3, 0.3, 1), mode_info="ERR // INVALID_URL")
            elif "timed out" in err_str:
                self.set_status("TIMEOUT ERROR:\nCONNECTION TOO SLOW OR BLOCKED", color=(1, 0.3, 0.3, 1), mode_info="ERR // TIMEOUT")
            else:
                self.set_status("STREAM ERROR:\nVIDEO UNAVAILABLE OR GEO-BLOCKED", color=(1, 0.3, 0.3, 1), mode_info="ERR // EXTRACTOR_FAILED")
            
            Clock.schedule_once(lambda dt: self._stop_visualizer("STREAM FAILED"))
            print(f"[ERROR LOG] yt-dlp fail: {e}")

    def toggle_pause(self, instance):
        if IS_ANDROID and self.player and self.player.isPlaying():
            self.player.pause()
            self.is_paused = True
            self.is_playing = False
            self._stop_visualizer("⏸ PAUSED")
            self.set_status("AUDIO PAUSED", color=(1, 0.7, 0.1, 1), mode_info="STATE: PAUSED")
        elif self.is_paused:
            if IS_ANDROID and self.player:
                self.player.start()
            self.is_paused = False
            self.is_playing = True
            self._start_visualizer()
            self.set_status("RESUMING PLAYBACK...", color=(0.15, 1.0, 0.4, 1), mode_info="STATE: PLAYING")

    def stop_audio(self, instance):
        if IS_ANDROID and self.player:
            if self.player.isPlaying() or self.is_paused:
                self.player.stop()
        self.is_playing = False
        self.is_paused = False
        self._stop_visualizer("⏹ STOPPED")
        self.set_status("PLAYBACK STOPPED\nSYSTEM IDLE", color=(0.4, 0.6, 0.8, 1), mode_info="STATE: IDLE")

    def clear_input(self, instance):
        self.url_input.text = ""
        self.set_status("SYSTEM READY\nPASTE NEW URL TO STREAM", color=(0.15, 1.0, 0.4, 1), mode_info="STANDBY // READY")

    def on_stop(self):
        self._stop_visualizer()
        if IS_ANDROID and self.player:
            self.player.release()

if __name__ == '__main__':
    WinampCyberPlayer().run()