import threading
import socket
import json
import os
import random
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp  # PENTING: Untuk auto-scaling layar HP
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
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

PLAYLIST_FILE = "playlist_cyber.json"

# --- KOMPONEN UI CUSTOM DENGAN SKALA DP ---
class CyberButton(Button):
    def __init__(self, bg_color=(0.1, 0.12, 0.18, 1), border_color=(0, 0.8, 1, 0.6), **kwargs):
        super(CyberButton, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.bold = True
        self.custom_bg = bg_color
        self.custom_border = border_color
        self.bind(pos=self.redraw, size=self.redraw, state=self.redraw)

    def redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'down':
                Color(min(1.0, self.custom_bg[0] * 1.5), min(1.0, self.custom_bg[1] * 1.5), min(1.0, self.custom_bg[2] * 1.5), 1)
            else:
                Color(*self.custom_bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)]) 
            
            Color(*self.custom_border)
            Line(rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], dp(10)), width=dp(1.2))

class GraphicSpectrum(BoxLayout):
    def __init__(self, **kwargs):
        super(GraphicSpectrum, self).__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(45) # Skala tinggi visualizer
        self.bars = 20
        self.heights = [4.0] * self.bars
        self.bind(pos=self.draw_bars, size=self.draw_bars)

    def set_levels(self, new_heights):
        self.heights = new_heights
        self.draw_bars()

    def draw_bars(self, *args):
        self.canvas.clear()
        total_w = self.width
        gap = dp(4)
        bar_w = max(dp(2), (total_w - (self.bars + 1) * gap) / self.bars)
        
        with self.canvas:
            for i in range(self.bars):
                bx = self.x + gap + i * (bar_w + gap)
                bh = max(dp(4), (self.heights[i] / 100.0) * (self.height - dp(4)))
                by = self.y + dp(2)
                
                r = (i / self.bars) * 0.2
                g = 0.8 + (i / self.bars) * 0.2
                b = 0.4 + (i / self.bars) * 0.6
                Color(r, g, b, 0.9)
                RoundedRectangle(pos=(bx, by), size=(bar_w, bh), radius=[dp(2)])

class WinampCyberPlayer(App):
    def build(self):
        Window.clearcolor = (0.03, 0.04, 0.06, 1)

        if IS_ANDROID:
            self.player = MediaPlayer()
            self.player.setAudioStreamType(AudioManager.STREAM_MUSIC)
        else:
            self.player = None
            
        self.is_paused = False
        self.is_playing = False
        self.current_title = "SYSTEM STANDBY"
        self.eq_event = None
        self.playlist = self.load_playlist_data()

        # 1. ROOT LAYOUT
        main_layout = BoxLayout(orientation='vertical', padding=[dp(16), dp(16), dp(16), dp(16)], spacing=dp(14))

        # 2. HEADER
        header_box = BoxLayout(size_hint_y=None, height=dp(35))
        title_label = Label(text="CAR AUDIO ENGINE", font_size='18sp', color=(0, 0.9, 1, 1), bold=True, halign="left")
        title_label.bind(size=title_label.setter('text_size'))
        header_box.add_widget(title_label)
        main_layout.add_widget(header_box)

        # 3. NOW PLAYING PANEL LCD
        self.lcd_container = BoxLayout(orientation='vertical', padding=[dp(16), dp(16), dp(16), dp(16)], spacing=dp(8), size_hint_y=None, height=dp(140))
        self.lcd_container.bind(pos=self._update_lcd_canvas, size=self._update_lcd_canvas)

        self.lcd_mode = Label(text="READY TO STREAM", font_size='11sp', color=(0, 0.8, 1, 0.8), size_hint_y=None, height=dp(18), halign="left")
        self.lcd_mode.bind(size=self.lcd_mode.setter('text_size'))

        self.status_label = Label(
            text="INSERT LINK OR\nSELECT PLAYLIST", 
            font_size='15sp', 
            color=(0.1, 1.0, 0.3, 1),
            bold=True, 
            halign="center", 
            valign="middle"
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))

        self.spectrum = GraphicSpectrum()

        self.lcd_container.add_widget(self.lcd_mode)
        self.lcd_container.add_widget(self.status_label)
        self.lcd_container.add_widget(self.spectrum)
        main_layout.add_widget(self.lcd_container)

        # 4. KONTROL MEDIA GRID (Teks murni, tanpa simbol aneh)
        control_grid = GridLayout(cols=3, spacing=dp(12), size_hint_y=None, height=dp(55))
        
        btn_play = CyberButton(text="PLAY", bg_color=(0.05, 0.45, 0.2, 1), border_color=(0.1, 0.9, 0.3, 0.8), font_size='15sp')
        btn_play.bind(on_press=self.start_stream_thread)
        
        btn_pause = CyberButton(text="PAUSE", bg_color=(0.45, 0.3, 0.05, 1), border_color=(1, 0.8, 0.1, 0.8), font_size='15sp')
        btn_pause.bind(on_press=self.toggle_pause)
        
        btn_stop = CyberButton(text="STOP", bg_color=(0.5, 0.1, 0.1, 1), border_color=(1, 0.2, 0.2, 0.8), font_size='15sp')
        btn_stop.bind(on_press=self.stop_audio)

        control_grid.add_widget(btn_play)
        control_grid.add_widget(btn_pause)
        control_grid.add_widget(btn_stop)
        main_layout.add_widget(control_grid)

        # 5. INPUT & SAVE URL ROW
        input_container = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50))
        
        self.url_input = TextInput(
            hint_text="Paste YouTube URL...", 
            multiline=False,
            font_size='13sp', 
            background_active='', background_normal='', 
            background_color=(0.08, 0.1, 0.15, 1),
            foreground_color=(0.9, 0.95, 1, 1), 
            hint_text_color=(0.4, 0.5, 0.6, 1), 
            padding=[dp(12), dp(14), dp(12), dp(12)]
        )
        with self.url_input.canvas.after:
            Color(0, 0.6, 0.8, 0.5)
            self.input_border = Line(rounded_rectangle=(self.url_input.x, self.url_input.y, self.url_input.width, self.url_input.height, dp(8)), width=dp(1.2))
        self.url_input.bind(pos=self._update_input_border, size=self._update_input_border)

        btn_add_playlist = CyberButton(text="SAVE", size_hint_x=0.3, bg_color=(0.1, 0.25, 0.45, 1), font_size='14sp')
        btn_add_playlist.bind(on_press=self.add_current_to_playlist)

        input_container.add_widget(self.url_input)
        input_container.add_widget(btn_add_playlist)
        main_layout.add_widget(input_container)

        # 6. PLAYLIST AREA (Mengisi sisa layar penuh ke bawah)
        pl_header = Label(text="SAVED PLAYLIST :", font_size='12sp', color=(0.5, 0.6, 0.7, 1), bold=True, size_hint_y=None, height=dp(25), halign="left")
        pl_header.bind(size=pl_header.setter('text_size'))
        main_layout.add_widget(pl_header)

        # ScrollView ini yang membuat UI panjang ke bawah berfungsi!
        playlist_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.playlist_container = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        self.playlist_container.bind(minimum_height=self.playlist_container.setter('height'))
        
        playlist_scroll.add_widget(self.playlist_container)
        main_layout.add_widget(playlist_scroll)

        self.refresh_playlist_ui()
        return main_layout

    def _update_input_border(self, *args):
        self.input_border.rounded_rectangle = (self.url_input.x, self.url_input.y, self.url_input.width, self.url_input.height, dp(8))

    def _update_lcd_canvas(self, *args):
        self.lcd_container.canvas.before.clear()
        with self.lcd_container.canvas.before:
            Color(0.06, 0.08, 0.1, 1)
            RoundedRectangle(pos=self.lcd_container.pos, size=self.lcd_container.size, radius=[dp(12)])
            Color(0, 0.7, 1, 0.7)
            Line(rounded_rectangle=(self.lcd_container.x, self.lcd_container.y, self.lcd_container.width, self.lcd_container.height, dp(12)), width=dp(1.5))

    def _update_spectrum_tick(self, dt):
        if self.is_playing and not self.is_paused:
            new_levels = [random.randint(15, 95) for _ in range(self.spectrum.bars)]
        else:
            new_levels = [3.0] * self.spectrum.bars
        self.spectrum.set_levels(new_levels)

    def _start_visualizer(self):
        if not self.eq_event:
            self.eq_event = Clock.schedule_interval(self._update_spectrum_tick, 0.12)

    def _stop_visualizer(self):
        if self.eq_event:
            self.eq_event.cancel()
            self.eq_event = None
        self.spectrum.set_levels([3.0] * self.spectrum.bars)

    def set_status(self, text, color=(0.1, 1.0, 0.3, 1), mode_info="STATUS: ACTIVE"):
        def _update(dt):
            self.status_label.text = text
            self.status_label.color = color
            self.lcd_mode.text = mode_info
        Clock.schedule_once(_update)

    def check_internet(self):
        try:
            socket.setdefaulttimeout(3.0)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except:
            return False

    def start_stream_thread(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.set_status("ERROR: PASTE URL FIRST", color=(1, 0.3, 0.3, 1), mode_info="ERR // EMPTY_URL")
            return

        if self.is_paused:
            if IS_ANDROID and self.player:
                self.player.start()
            self.is_paused = False
            self.is_playing = True
            self._start_visualizer()
            self.set_status(f"RESUMED:\n{self.current_title[:35]}", mode_info="STATE: PLAYING")
            return

        self.set_status("CONNECTING...", color=(0, 0.8, 1, 1), mode_info="ENGINE // YT-DLP")
        threading.Thread(target=self.extract_and_play, args=(url,), daemon=True).start()

    def extract_and_play(self, youtube_url):
        if not self.check_internet():
            self.set_status("NETWORK ERROR:\nNO INTERNET", color=(1, 0.3, 0.3, 1), mode_info="ERR // OFFLINE")
            Clock.schedule_once(lambda dt: self._stop_visualizer())
            return

        self.set_status("BYPASSING SECURITY...\nPLEASE WAIT", color=(1, 0.8, 0.2, 1), mode_info="FETCHING MEDIA")

        # --- BYPASS GEO-BLOCK & PO TOKEN YOUTUBE ---
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best', # m4a terbaik untuk android
            'noplaylist': True, 
            'quiet': True,
            'no_warnings': True,
            'skip_download': True, 
            'socket_timeout': 15, 
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'client': ['android', 'ios', 'tv'], # Memaksa request dari client mobile/tv (Bypass Geo-Block)
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'
            }
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                if not info: raise Exception("No data")

                audio_url = info.get('url')
                self.current_title = info.get('title', 'LIVE AUDIO STREAM').upper()

                if IS_ANDROID and self.player:
                    self.set_status("BUFFERING...", color=(0, 0.8, 1, 1), mode_info="BUFFERING")
                    self.player.reset()
                    self.player.setDataSource(audio_url)
                    self.player.prepare()
                    self.player.start()
                else:
                    print("AUDIO URL:", audio_url)

                self.is_playing = True
                self.is_paused = False
                Clock.schedule_once(lambda dt: self._start_visualizer())
                self.set_status(f"{self.current_title[:45]}", color=(0.1, 1.0, 0.3, 1), mode_info="PLAYING // HI-FI")

        except Exception as e:
            err_msg = str(e).lower()
            if "sign in" in err_msg or "bot" in err_msg:
                self.set_status("YOUTUBE BLOCKED:\nBOT PROTECTION ACTIVE", color=(1, 0.3, 0.3, 1), mode_info="ERR // BLOCKED")
            elif "geo" in err_msg or "country" in err_msg:
                self.set_status("ERROR: GEO-BLOCKED\nTRY DIFFERENT SONG", color=(1, 0.3, 0.3, 1), mode_info="ERR // REGION")
            else:
                self.set_status("ERROR: EXTRACT FAILED\nCHECK LINK", color=(1, 0.3, 0.3, 1), mode_info="ERR // FAILED")
            Clock.schedule_once(lambda dt: self._stop_visualizer())
            print("LOG ERROR YT-DLP:", e)

    def toggle_pause(self, instance):
        if IS_ANDROID and self.player and self.player.isPlaying():
            self.player.pause()
            self.is_paused = True
            self.is_playing = False
            self.set_status("PLAYBACK PAUSED", color=(1, 0.7, 0.1, 1), mode_info="STATE: PAUSED")
        elif self.is_paused:
            if IS_ANDROID and self.player: self.player.start()
            self.is_paused = False
            self.is_playing = True
            self.set_status(f"{self.current_title[:45]}", color=(0.1, 1.0, 0.3, 1), mode_info="STATE: PLAYING")

    def stop_audio(self, instance):
        if IS_ANDROID and self.player:
            if self.player.isPlaying() or self.is_paused:
                self.player.stop()
        self.is_playing = False
        self.is_paused = False
        self._stop_visualizer()
        self.set_status("STOPPED // IDLE", color=(0.4, 0.6, 0.8, 1), mode_info="STATE: IDLE")

    def load_playlist_data(self):
        if os.path.exists(PLAYLIST_FILE):
            try:
                with open(PLAYLIST_FILE, 'r') as f: return json.load(f)
            except: pass
        return []

    def save_playlist_data(self):
        try:
            with open(PLAYLIST_FILE, 'w') as f: json.dump(self.playlist, f)
        except: pass

    def add_current_to_playlist(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.set_status("CANNOT SAVE: EMPTY URL", color=(1, 0.4, 0.4, 1), mode_info="ERR // NO_DATA")
            return
        
        for item in self.playlist:
            if item['url'] == url:
                self.set_status("ALREADY IN PLAYLIST", color=(1, 0.7, 0.2, 1), mode_info="PLAYLIST // EXIST")
                return

        title_display = self.current_title if self.current_title != "SYSTEM STANDBY" else url[:30] + "..."
        self.playlist.append({"title": title_display, "url": url})
        self.save_playlist_data()
        self.refresh_playlist_ui()
        self.set_status("SAVED TO PLAYLIST", color=(0.1, 1.0, 0.3, 1), mode_info="PLAYLIST // SAVED")
        self.url_input.text = "" 

    def remove_from_playlist(self, item_index):
        if 0 <= item_index < len(self.playlist):
            self.playlist.pop(item_index)
            self.save_playlist_data()
            self.refresh_playlist_ui()

    def play_from_playlist(self, url):
        self.url_input.text = url
        self.start_stream_thread(None)

    def refresh_playlist_ui(self):
        self.playlist_container.clear_widgets()
        if not self.playlist:
            empty_lbl = Label(text="No saved streams.", font_size='13sp', color=(0.4, 0.5, 0.6, 1), size_hint_y=None, height=dp(40))
            self.playlist_container.add_widget(empty_lbl)
            return

        for idx, item in enumerate(self.playlist):
            row = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(50)) 
            
            btn_item = CyberButton(
                text=f"{item['title'][:40]}", 
                size_hint_x=0.8,
                bg_color=(0.07, 0.1, 0.15, 1),
                border_color=(0.2, 0.4, 0.6, 0.5),
                font_size='13sp'
            )
            btn_item.bind(on_press=lambda inst, u=item['url']: self.play_from_playlist(u))

            btn_del = CyberButton(
                text="DEL", 
                size_hint_x=0.2,
                bg_color=(0.4, 0.1, 0.1, 1),
                border_color=(0.8, 0.2, 0.2, 0.8),
                font_size='13sp'
            )
            btn_del.bind(on_press=lambda inst, i=idx: self.remove_from_playlist(i))

            row.add_widget(btn_item)
            row.add_widget(btn_del)
            self.playlist_container.add_widget(row)

    def on_stop(self):
        self._stop_visualizer()
        if IS_ANDROID and self.player:
            self.player.release()

if __name__ == '__main__':
    WinampCyberPlayer().run()