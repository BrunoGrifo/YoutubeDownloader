import sys
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import yt_dlp


def get_ffmpeg_path() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "bin", "ffmpeg.exe")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Video Downloader")
        self.geometry("460x380")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self._format = tk.StringVar(value="mp3")
        self._quality = tk.StringVar(value="720p")
        self._is_downloading = False
        self._quality_buttons = []

        self._build_ui()

    def _build_ui(self):
        # Title
        ctk.CTkLabel(
            self,
            text="YouTube Video Downloader",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(18, 0))

        # URL entry
        self.url_entry = ctk.CTkEntry(
            self,
            placeholder_text="Paste YouTube URL here...",
            width=420,
            height=38,
        )
        self.url_entry.pack(pady=(12, 0), padx=20)

        # Format toggle row
        fmt_frame = ctk.CTkFrame(self, fg_color="transparent")
        fmt_frame.pack(pady=(12, 0))

        self.btn_mp3 = ctk.CTkButton(
            fmt_frame,
            text="MP3",
            width=100,
            command=lambda: self._set_format("mp3"),
        )
        self.btn_mp3.pack(side="left", padx=6)

        self.btn_video = ctk.CTkButton(
            fmt_frame,
            text="Video",
            width=100,
            command=lambda: self._set_format("video"),
        )
        self.btn_video.pack(side="left", padx=6)

        # Quality radio buttons
        qual_frame = ctk.CTkFrame(self, fg_color="transparent")
        qual_frame.pack(pady=(10, 0))

        for q in ("480p", "720p", "1080p"):
            rb = ctk.CTkRadioButton(
                qual_frame,
                text=q,
                variable=self._quality,
                value=q,
            )
            rb.pack(side="left", padx=12)
            self._quality_buttons.append(rb)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, width=420)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(18, 0), padx=20)

        # Status label
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(pady=(6, 0))

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(14, 0))

        self.btn_download = ctk.CTkButton(
            btn_frame,
            text="Download",
            width=160,
            height=42,
            command=self._on_download,
        )
        self.btn_download.pack(side="left", padx=8)

        self.btn_download_as = ctk.CTkButton(
            btn_frame,
            text="Download As...",
            width=160,
            height=42,
            command=self._on_download_as,
        )
        self.btn_download_as.pack(side="left", padx=8)

        self._set_format("mp3")

    def _set_format(self, fmt: str):
        self._format.set(fmt)
        is_mp3 = fmt == "mp3"

        active_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]
        inactive_color = ("gray30", "gray25")

        self.btn_mp3.configure(fg_color=active_color if is_mp3 else inactive_color)
        self.btn_video.configure(fg_color=inactive_color if is_mp3 else active_color)

        state = "disabled" if is_mp3 else "normal"
        for rb in self._quality_buttons:
            rb.configure(state=state)

    def _on_download(self):
        save_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self._start_download(save_dir)

    def _on_download_as(self):
        if self._format.get() == "mp3":
            filetypes = [("MP3 Audio", "*.mp3")]
            default_ext = ".mp3"
        else:
            filetypes = [("MP4 Video", "*.mp4")]
            default_ext = ".mp4"

        path = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            filetypes=filetypes,
            initialdir=os.path.expanduser("~"),
        )
        if path:
            save_dir = os.path.dirname(path)
            self._start_download(save_dir, explicit_path=path)

    def _start_download(self, save_dir: str, explicit_path: str = None):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please paste a YouTube URL first.")
            return
        if self._is_downloading:
            return

        self._is_downloading = True
        self._set_ui_downloading(True)
        self.progress_bar.set(0)
        self._update_status("Starting download...")

        if explicit_path:
            base = os.path.splitext(explicit_path)[0]
            output_template = base + ".%(ext)s"
        else:
            output_template = os.path.join(save_dir, "%(title)s.%(ext)s")

        opts = self._get_ydl_opts(output_template)

        threading.Thread(
            target=self._download_thread,
            args=(url, opts, save_dir),
            daemon=True,
        ).start()

    def _get_ydl_opts(self, output_template: str) -> dict:
        fmt = self._format.get()
        quality = self._quality.get()
        ffmpeg_path = get_ffmpeg_path()

        if fmt == "mp3":
            format_str = "bestaudio/best"
            postprocessors = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
        else:
            height = quality.replace("p", "")
            format_str = (
                f"bestvideo[ext=mp4][height<={height}]+bestaudio[ext=m4a]"
                f"/bestvideo[height<={height}]+bestaudio"
                f"/best[height<={height}]"
            )
            postprocessors = []

        opts = {
            "format": format_str,
            "outtmpl": output_template,
            "ffmpeg_location": ffmpeg_path,
            "postprocessors": postprocessors,
            "progress_hooks": [self._progress_hook],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        if fmt == "video":
            opts["merge_output_format"] = "mp4"
        return opts

    def _download_thread(self, url: str, opts: dict, save_dir: str):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.after(0, self._on_download_complete, save_dir, None)
        except Exception as e:
            self.after(0, self._on_download_complete, save_dir, str(e))

    def _progress_hook(self, d: dict):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("_speed_str", "")
            eta = d.get("_eta_str", "")

            if total and total > 0:
                progress = downloaded / total
                status = f"Downloading...  {speed}  ETA: {eta}"
            else:
                progress = 0
                status = f"Downloading...  {speed}"

            self.after(0, self.progress_bar.set, progress)
            self.after(0, self._update_status, status)

        elif d["status"] == "finished":
            self.after(0, self.progress_bar.set, 1.0)
            self.after(0, self._update_status, "Processing...")

    def _on_download_complete(self, save_dir: str, error):
        self._is_downloading = False
        self._set_ui_downloading(False)

        if error:
            self.progress_bar.set(0)
            self._update_status("Download failed.")
            messagebox.showerror("Download Failed", f"An error occurred:\n\n{error}")
            return

        self._update_status("Download complete!")

        dialog = ctk.CTkToplevel(self)
        dialog.title("Done")
        dialog.geometry("300x130")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="Download complete!", font=ctk.CTkFont(size=14)
        ).pack(pady=(24, 12))

        row = ctk.CTkFrame(dialog, fg_color="transparent")
        row.pack()

        ctk.CTkButton(
            row,
            text="Open Folder",
            width=120,
            command=lambda: (os.startfile(save_dir), dialog.destroy()),
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            row,
            text="OK",
            width=80,
            command=dialog.destroy,
        ).pack(side="left", padx=8)

    def _set_ui_downloading(self, downloading: bool):
        state = "disabled" if downloading else "normal"
        for widget in (
            self.btn_download,
            self.btn_download_as,
            self.url_entry,
            self.btn_mp3,
            self.btn_video,
        ):
            widget.configure(state=state)
        if not downloading:
            self._set_format(self._format.get())

    def _update_status(self, text: str):
        self.status_label.configure(text=text)


if __name__ == "__main__":
    app = App()
    app.mainloop()
