import tkinter as tk
from tkinter import messagebox
import threading
import yt_dlp
import vlc

class YoutubeAudioPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Audio Player")
        self.root.geometry("450x250")
        self.root.resizable(False, False)

        # Inisialisasi VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Variabel Status
        self.is_paused = False

        # --- Komponen Antarmuka (GUI) ---
        
        # Label Instruksi
        self.label_url = tk.Label(root, text="Masukkan Link YouTube:", font=("Arial", 11))
        self.label_url.pack(pady=10)

        # Kolom Input Link
        self.entry_url = tk.Entry(root, width=50, font=("Arial", 10))
        self.entry_url.pack(pady=5)

        # Label Status Informasi Lagu
        self.label_status = tk.Label(root, text="Status: Siap", fg="blue", font=("Arial", 10, "italic"), wraplength=400)
        self.label_status.pack(pady=15)

        # Frame untuk Tombol Kontrol
        self.frame_buttons = tk.Frame(root)
        self.frame_buttons.pack(pady=10)

        # Tombol-Tombol
        self.btn_play = tk.Button(self.frame_buttons, text="▶ Play", width=8, bg="#4CAF50", fg="white", command=self.start_play_thread)
        self.btn_play.grid(row=0, column=0, padx=5)

        self.btn_pause = tk.Button(self.frame_buttons, text="⏸ Pause", width=8, bg="#FF9800", fg="white", command=self.pause_audio)
        self.btn_pause.grid(row=0, column=1, padx=5)

        self.btn_stop = tk.Button(self.frame_buttons, text="⏹ Stop", width=8, bg="#f44336", fg="white", command=self.stop_audio)
        self.btn_stop.grid(row=0, column=2, padx=5)

    def start_play_thread(self):
        """Menjalankan proses loading audio di background agar GUI tidak hang/membeku"""
        url = self.entry_url.get().strip()
        if not url:
            messagebox.showwarning("Peringatan", "Silakan masukkan link YouTube terlebih dahulu!")
            return
        
        # Jika sedang pause dan link tidak berubah, tombol play akan melanjutkan lagu
        if self.is_paused:
            self.player.play()
            self.is_paused = False
            self.label_status.config(text="Status: Memutar kembali...", fg="green")
            return

        self.label_status.config(text="Sedang mengambil audio... Harap tunggu.", fg="orange")
        
        # Membuat thread baru agar aplikasi tetap responsif saat mengambil link
        thread = threading.Thread(target=self.play_audio, args=(url,), daemon=True)
        thread.start()

    def play_audio(self, youtube_url):
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                audio_url = info['url']
                title = info.get('title', 'Audio')

            # Memasukkan URL ke pemutar VLC
            media = self.instance.media_new(audio_url)
            self.player.set_media(media)
            self.player.play()

            # Update status di GUI
            self.label_status.config(text=f"Memutar:\n{title}", fg="green")
            self.is_paused = False

        except Exception as e:
            self.label_status.config(text="Status: Gagal memutar audio.", fg="red")
            messagebox.showerror("Error", f"Gagal memproses link YouTube.\nPastikan link valid.\n\nDetail: {e}")

    def pause_audio(self):
        if self.player.is_playing():
            self.player.pause()
            self.is_paused = True
            self.label_status.config(text="Status: Dijeda (Paused)", fg="orange")

    def stop_audio(self):
        self.player.stop()
        self.is_paused = False
        self.label_status.config(text="Status: Dihentikan", fg="blue")

if __name__ == "__main__":
    root = tk.Tk()
    app = YoutubeAudioPlayer(root)
    root.mainloop()
