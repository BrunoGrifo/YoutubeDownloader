@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo  YouTube Downloader - Build Script
echo ========================================
echo.

REM Step 1: Install Python dependencies
echo [1/4] Installing Python dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause & exit /b 1
)
REM Always grab the newest yt-dlp - YouTube breaks older versions every few weeks.
python -m pip install --upgrade yt-dlp
if errorlevel 1 (
    echo ERROR: yt-dlp upgrade failed.
    pause & exit /b 1
)
echo Done.
echo.

REM Step 2: Download ffmpeg static binary for Windows
echo [2/4] Downloading ffmpeg static binary...

if not exist "bin" mkdir bin

python -c ^
"import urllib.request, sys; ^
url = 'https://github.com/BtbN/ffmpeg-builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip'; ^
print('Downloading ffmpeg (this may take a minute)...'); ^
urllib.request.urlretrieve(url, 'bin/ffmpeg_temp.zip'); ^
print('Download complete.')"

if errorlevel 1 (
    echo ERROR: Failed to download ffmpeg.
    pause & exit /b 1
)

python -c ^
"import zipfile, shutil, os; ^
z = zipfile.ZipFile('bin/ffmpeg_temp.zip'); ^
members = [m for m in z.namelist() if m.endswith('bin/ffmpeg.exe')]; ^
src = members[0]; ^
f_in = z.open(src); ^
f_out = open('bin/ffmpeg.exe', 'wb'); ^
shutil.copyfileobj(f_in, f_out); ^
f_in.close(); f_out.close(); z.close(); ^
os.remove('bin/ffmpeg_temp.zip'); ^
print('ffmpeg.exe extracted successfully.')"

if errorlevel 1 (
    echo ERROR: Failed to extract ffmpeg.exe.
    pause & exit /b 1
)
echo Done.
echo.

REM Step 3: Download Deno JS runtime for Windows
REM YouTube now requires a JavaScript runtime to solve its player challenge;
REM without it yt-dlp downloads fail with HTTP 403 Forbidden.
echo [3/4] Downloading Deno JS runtime...

python -c ^
"import urllib.request; ^
url = 'https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip'; ^
print('Downloading deno (this may take a minute)...'); ^
urllib.request.urlretrieve(url, 'bin/deno_temp.zip'); ^
print('Download complete.')"

if errorlevel 1 (
    echo ERROR: Failed to download deno.
    pause & exit /b 1
)

python -c ^
"import zipfile, shutil, os; ^
z = zipfile.ZipFile('bin/deno_temp.zip'); ^
f_in = z.open('deno.exe'); ^
f_out = open('bin/deno.exe', 'wb'); ^
shutil.copyfileobj(f_in, f_out); ^
f_in.close(); f_out.close(); z.close(); ^
os.remove('bin/deno_temp.zip'); ^
print('deno.exe extracted successfully.')"

if errorlevel 1 (
    echo ERROR: Failed to extract deno.exe.
    pause & exit /b 1
)
echo Done.
echo.

REM Step 4: Run PyInstaller
echo [4/4] Building .exe with PyInstaller...

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "YouTubeDownloader" ^
    --add-data "bin/ffmpeg.exe;bin" ^
    --add-data "bin/deno.exe;bin" ^
    --hidden-import "customtkinter" ^
    --hidden-import "yt_dlp" ^
    --collect-all "customtkinter" ^
    main.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    pause & exit /b 1
)

echo.
echo ========================================
echo  Build complete!
echo  Output: dist\YouTubeDownloader.exe
echo ========================================
pause
