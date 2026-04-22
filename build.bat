@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo  YouTube Downloader - Build Script
echo ========================================
echo.

REM Step 1: Install Python dependencies
echo [1/3] Installing Python dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause & exit /b 1
)
echo Done.
echo.

REM Step 2: Download ffmpeg static binary for Windows
echo [2/3] Downloading ffmpeg static binary...

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

REM Step 3: Run PyInstaller
echo [3/3] Building .exe with PyInstaller...

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "YouTubeDownloader" ^
    --add-data "bin/ffmpeg.exe;bin" ^
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
