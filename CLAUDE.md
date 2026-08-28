# CLAUDE.md

Context for Claude Code when working in this repo.

## What this is

A single-file Windows desktop app that downloads YouTube videos (MP4) or audio
(MP3). Ships as one portable `dist\YouTubeDownloader.exe` — the end user needs no
Python, ffmpeg, or Deno. Distributed via GitHub Releases; the README download
badge points at `releases/latest/download/YouTubeDownloader.zip`.

- Repo: `git@github.com:BrunoGrifo/YoutubeDownloader.git` (branch `main`)
- Platform: Windows 10/11 x64 only. Build machine also Windows.

## Files

| File | Role |
|---|---|
| `main.py` | Entire app: `customtkinter` UI + `yt-dlp` download logic + threading |
| `requirements.txt` | `customtkinter==5.2.2`, `yt-dlp`, `pyinstaller` |
| `build.bat` | 5-step build: deps → ffmpeg → deno → PyInstaller → zip. **User runs this by double-clicking.** |
| `YouTubeDownloader.spec` | PyInstaller spec (gitignored via `*.spec`; `build.bat` invokes PyInstaller by CLI flags, not this spec) |
| `bin/` | Generated: `ffmpeg.exe`, `deno.exe` (gitignored) |
| `dist/` | Generated: `YouTubeDownloader.exe`, `YouTubeDownloader.zip` (gitignored) |

## Architecture notes

- **Threading**: downloads run in a daemon thread; all widget updates routed to
  the main thread via `self.after(0, fn)`.
- **ffmpeg** bundled because yt-dlp needs it to merge video+audio (720p/1080p)
  and to make MP3. Runtime path resolved via `sys._MEIPASS` → `bin/ffmpeg.exe`.
- **Deno** bundled because YouTube now requires solving a JS player challenge;
  without a JS runtime, downloads fail with `HTTP 403 Forbidden`. Passed to
  yt-dlp via `opts["js_runtimes"] = {"deno": {"path": ...}}`.
- **Download As...**: downloads to a temp dir first, then `shutil.move`s to the
  chosen path — avoids Windows Defender locking the file during yt-dlp renames.
- PyInstaller needs `--collect-all customtkinter` (theme JSON) or the app
  crashes on launch.

## Common tasks

### Dev setup
```powershell
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```
```bash
# macOS / Linux (run from source only)
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -r requirements.txt && python3 main.py
```
`main.py` `get_ffmpeg_path`/`get_deno_path` hardcode `ffmpeg.exe`/`deno.exe` —
Windows-oriented; a real macOS build needs those made OS-aware. `build.bat` is
Windows-only and PyInstaller can't cross-compile, so the released zip is always
built on Windows.

### Build the exe
Double-click `build.bat` (activate `.venv` first so deps land in the venv).
Output: `dist\YouTubeDownloader.exe` + `dist\YouTubeDownloader.zip`.

### Release
1. `build.bat`
2. `gh release create vX.Y.Z dist\YouTubeDownloader.zip --title "vX.Y.Z" --notes "..."`
3. Asset MUST be named `YouTubeDownloader.zip` and the release MUST be published
   (not draft) and non-prerelease, or the README button breaks.
4. Reuse a tag / refresh only the exe: `gh release upload vX.Y.Z dist\YouTubeDownloader.zip --clobber`

Existing tags: `v1.0.0`, `v1.1.0`. Latest release: `v1.1.0`.

## Gotchas / when downloads break

- Symptom `HTTP Error 403: Forbidden` → yt-dlp is stale or Deno missing.
  `build.bat` step 1 always runs `pip install --upgrade yt-dlp`. Rebuild + release.
- `requirements.txt` pins `customtkinter==5.2.2` — don't bump casually, the UI
  color/theme code (`ctk.ThemeManager.theme["CTkButton"]["fg_color"]`) depends on
  its internals.
- Build machine currently has Python 3.14; app targets 3.10+.
