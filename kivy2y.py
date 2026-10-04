from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
import threading
import requests

# --- FIX ANTI CRASH: Deteksi Sistem Operasi Terlebih Dahulu ---
IS_ANDROID = False
try:
    from jnius import autoclass
    MediaPlayer = autoclass('android.media.MediaPlayer')
    AudioManager = autoclass('android.media.AudioManager')
    IS_ANDROID = True
except ImportError:
    # Jika dijalankan di PC atau mode simulasi Pydroid, gunakan pustaka fallback alternatif
    try:
        from kivy.core.audio import SoundLoader
    except:
        pass

class WinampRetroPlayer(App):
    def build(self):
        Window.clearcolor = (0.08, 0.08, 0.1, 1)

        # Inisialisasi pemutar media berdasarkan perangkat
        if IS_ANDROID:
            self.player = MediaPlayer()
            self.player.setAudioStreamType(AudioManager.STREAM_MUSIC)
        else:
            self.player = None
            
        self.is_paused = False

        root_scroll = ScrollView(size_hint=(1, 1))
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15, size_hint_y=None)
        main_layout.bind(minimum_height=main_layout.setter('height'))
        
        # 1. TITLE BAR
        title_bar = BoxLayout(size_hint_y=None, height=35)
        title_label = Label(text="=== WINAMP 2.x [STABLE] ===", font_size=14, color=(0, 0.8, 1, 1), bold=True)
        title_bar.add_widget(title_label)
        main_layout.add_widget(title_bar)

        # 2. LCD DISPLAY PANEL
        lcd_panel = BoxLayout(orientation='vertical', padding=10, size_hint_y=None, height=100)
        # FIX: Menghapus typo parameter 'Rasa=True' yang membuat program crash
        self.status_label = Label(
            text="WINAMP READY", font_size=13, color=(0, 1, 0, 1), bold=True, 
            halign="center", valign="middle"
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        lcd_panel.add_widget(self.status_label)
        main_layout.add_widget(lcd_panel)

        # 3. INPUT SLOT
        input_label = Label(text="YOUTUBE LINK INPUT SLOT:", font_size=11, color=(0.6, 0.6, 0.6, 1), size_hint_y=None, height=20)
        main_layout.add_widget(input_label)
        
        self.url_input = TextInput(
            text="", hint_text="PASTE YOUTUBE URL HERE...", multiline=False, size_hint_y=None, height=50,
            background_color=(0.15, 0.15, 0.18, 1), foreground_color=(0, 0.9, 1, 1), 
            hint_text_color=(0.4, 0.4, 0.4, 1), cursor_color=(0, 0.9, 1, 1)
        )
        main_layout.add_widget(self.url_input)

        # 4. KONTROL TOMBOL
        control_grid = GridLayout(cols=4, spacing=8, size_hint_y=None, height=60)
        
        btn_play = Button(text="PLAY", background_color=(0.15, 0.5, 0.15, 1), color=(1, 1, 1, 1), bold=True)
        btn_play.bind(on_press=self.start_stream_thread)
        
        btn_pause = Button(text="PAUSE", background_color=(0.6, 0.4, 0.1, 1), color=(1, 1, 1, 1), bold=True)
        btn_pause.bind(on_press=self.toggle_pause)
        
        btn_stop = Button(text="STOP", background_color=(0.5, 0.1, 0.1, 1), color=(1, 1, 1, 1), bold=True)
        btn_stop.bind(on_press=self.stop_audio)
        
        btn_eject = Button(text="CLEAR", background_color=(0.3, 0.3, 0.35, 1), color=(1, 1, 1, 1), bold=True)
        btn_eject.bind(on_press=self.clear_input)

        control_grid.add_widget(btn_play)
        control_grid.add_widget(btn_pause)
        control_grid.add_widget(btn_stop)
        control_grid.add_widget(btn_eject)
        main_layout.add_widget(control_grid)

        eq_label = Label(text="[ O O O O O O ]  10-BAND EQ  [ O O O O O O ]", font_size=10, color=(0.4, 0.4, 0.4, 1), size_hint_y=None, height=20)
        main_layout.add_widget(eq_label)

        root_scroll.add_widget(main_layout)
        return root_scroll

    def start_stream_thread(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = "*** ERROR: NO URL ***"
            return
        if self.is_paused:
            if IS_ANDROID and self.player:
                self.player.start()
            self.is_paused = False
            self.status_label.text = "PLAYING..."
            return
        self.status_label.text = "CONNECTING TO COBALT..."
        threading.Thread(target=self.extract_and_play, args=(url,), daemon=True).start()

    def extract_and_play(self, youtube_url):
        try:
            # Menggunakan endpoint API Cobalt V1 resmi
            api_endpoint = "https://cobalt.tools"
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            payload = {"url": youtube_url, "downloadMode": "audio", "audioFormat": "mp3"}
            
            response = requests.post(api_endpoint, json=payload, headers=headers, timeout=15)
            data = response.json()
            
            if response.status_code == 200 and "url" in data:
                audio_url = data["url"]
                title = data.get("filename", "RETRO AUDIO TRACK")
                
                if IS_ANDROID and self.player:
                    self.player.reset()
                    self.player.setDataSource(audio_url)
                    self.status_label.text = "STREAM LOADING..."
                    self.player.prepare()
                    self.player.start()
                else:
                    # Mode Fallback untuk Simulasi PC/Pydroid internal
                    self.status_label.text = "[SIMULATOR MODE] STREAM OK"
                    print(f"Direct Audio Link: {audio_url}")
                
                self.status_label.text = f"PLAYING:\n{title[:40].upper()}"
                self.is_paused = False
            else:
                error_msg = data.get("text", "SERVER BUSY")
                self.status_label.text = f"*** API ERR: {error_msg.upper()} ***"
        except Exception as e:
            self.status_label.text = "*** CONNECTION ERROR ***"

    def toggle_pause(self, instance):
        if IS_ANDROID and self.player and self.player.isPlaying():
            self.player.pause()
            self.is_paused = True
            self.status_label.text = "PAUSED"
        elif self.is_paused:
            if IS_ANDROID and self.player:
                self.player.start()
            self.is_paused = False
            self.status_label.text = "PLAYING..."

    def stop_audio(self, instance):
        if IS_ANDROID and self.player:
            if self.player.isPlaying() or self.is_paused:
                self.player.stop()
                self.is_paused = False
                self.status_label.text = "STOPPED"

    def clear_input(self, instance):
        self.url_input.text = ""
        self.status_label.text = "WINAMP READY"

    def on_stop(self):
        if IS_ANDROID and self.player:
            self.player.release()

if __name__ == '__main__':
    WinampRetroPlayer().run()
