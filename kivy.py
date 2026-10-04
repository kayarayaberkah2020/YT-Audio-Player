from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
import threading
import requests

# Menggunakan jnius untuk mengakses Android Native MediaPlayer
from jnius import autoclass

MediaPlayer = autoclass('android.media.MediaPlayer')
AudioManager = autoclass('android.media.AudioManager')

class WinampRetroPlayer(App):
    def build(self):
        Window.clearcolor = (0.1, 0.1, 0.12, 1)
        self.player = MediaPlayer()
        self.player.setAudioStreamType(AudioManager.STREAM_MUSIC)
        self.is_paused = False

        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # 1. TITLE BAR RETRO
        title_bar = BoxLayout(size_hint_y=None, height=30)
        title_label = Label(text="=== WINAMP 2.x [LIGHTWEIGHT] ===", font_size=12, color=(0, 0.9, 1, 1), bold=True)
        title_bar.add_widget(title_label)
        main_layout.add_widget(title_bar)

        # 2. LCD DISPLAY PANEL
        lcd_panel = BoxLayout(orientation='vertical', padding=10, size_hint_y=None, height=120)
        self.status_label = Label(text="WINAMP READY", font_size=13, color=(0, 1, 0, 1), bold=True, halign="center", valign="middle")
        self.status_label.bind(size=self.status_label.setter('text_size'))
        lcd_panel.add_widget(self.status_label)
        main_layout.add_widget(lcd_panel)

        # 3. KOTAK INPUT LINK
        self.url_input = TextInput(
            text="", hint_text="INSERT YOUTUBE URL HERE...", multiline=False, size_hint_y=None, height=45,
            background_color=(0.15, 0.15, 0.18, 1), foreground_color=(0, 0.9, 1, 1), hint_text_color=(0.4, 0.4, 0.4, 1), cursor_color=(0, 0.9, 1, 1)
        )
        main_layout.add_widget(self.url_input)

        # 4. RETRO KONTROL TOMBOL
        control_grid = GridLayout(cols=4, spacing=5, size_hint_y=None, height=55)
        btn_play = Button(text="[ PLAY ]", background_color=(0.2, 0.5, 0.2, 1), bold=True)
        btn_play.bind(on_press=self.start_stream_thread)
        
        btn_pause = Button(text="[ PAUSE ]", background_color=(0.6, 0.4, 0.1, 1), bold=True)
        btn_pause.bind(on_press=self.toggle_pause)
        
        btn_stop = Button(text="[ STOP ]", background_color=(0.5, 0.1, 0.1, 1), bold=True)
        btn_stop.bind(on_press=self.stop_audio)
        
        btn_eject = Button(text="[ EJECT ]", background_color=(0.3, 0.3, 0.35, 1), bold=True)
        btn_eject.bind(on_press=self.clear_input)

        control_grid.add_widget(btn_play)
        control_grid.add_widget(btn_pause)
        control_grid.add_widget(btn_stop)
        control_grid.add_widget(btn_eject)
        main_layout.add_widget(control_grid)

        eq_label = Label(text="[ O O O O O O ]  10-BAND EQ  [ O O O O O O ]", font_size=10, color=(0.5, 0.5, 0.5, 1))
        main_layout.add_widget(eq_label)
        return main_layout

    def start_stream_thread(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = "*** ERROR: NO URL ***"
            return
        if self.is_paused:
            self.player.start()
            self.is_paused = False
            self.status_label.text = "PLAYING..."
            return
        self.status_label.text = "FETCHING API DATA..."
        threading.Thread(target=self.extract_and_play, args=(url,), daemon=True).start()

    def extract_and_play(self, youtube_url):
        try:
            # API Cobalt publik gratis untuk mengurai video ke audio mentah secara instan
            api_endpoint = "https://cobalt.tools"
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            payload = {"url": youtube_url, "downloadMode": "audio"}
            
            response = requests.post(api_endpoint, json=payload, headers=headers, timeout=15)
            data = response.json()
            
            if response.status_code == 200 and "url" in data:
                audio_url = data["url"]
                title = data.get("filename", "RETRO AUDIO TRACK")
                
                self.player.reset()
                self.player.setDataSource(audio_url)
                self.status_label.text = "LOADING STREAM..."
                self.player.prepare()
                self.player.start()
                
                self.status_label.text = f"PLAYING:\n{title[:40].upper()}"
                self.is_paused = False
            else:
                self.status_label.text = "*** API SERVER BUSY ***"
        except Exception as e:
            self.status_label.text = "*** TRACK CONVERT ERROR ***"

    def toggle_pause(self, instance):
        if self.player.isPlaying():
            self.player.pause()
            self.is_paused = True
            self.status_label.text = "PAUSED"
        elif self.is_paused:
            self.player.start()
            self.is_paused = False
            self.status_label.text = "PLAYING..."

    def stop_audio(self, instance):
        if self.player.isPlaying() or self.is_paused:
            self.player.stop()
            self.is_paused = False
            self.status_label.text = "STOPPED"

    def clear_input(self, instance):
        self.url_input.text = ""
        self.status_label.text = "WINAMP READY"

    def on_stop(self):
        self.player.release()

if __name__ == '__main__':
    WinampRetroPlayer().run()
