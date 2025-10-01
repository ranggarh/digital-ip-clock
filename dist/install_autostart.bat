@echo off
chcp 65001 >nul
title Digital IP Clock - Auto Startup Installer
color 0A

echo.
echo ═══════════════════════════════════════════════════════════
echo    DIGITAL IP CLOCK - AUTO STARTUP INSTALLER
echo    By Puterako
echo ═══════════════════════════════════════════════════════════
echo.

:MENU
echo.
echo Pilih opsi:
echo.
echo [1] Install Auto-Startup (Registry Method)
echo [2] Install Auto-Startup (Startup Folder Method)
echo [3] Hapus Auto-Startup
echo [4] Cek Status Auto-Startup
echo [5] Exit
echo.
set /p choice="Masukkan pilihan (1-5): "

if "%choice%"=="1" goto INSTALL_REGISTRY
if "%choice%"=="2" goto INSTALL_FOLDER
if "%choice%"=="3" goto UNINSTALL
if "%choice%"=="4" goto CHECK_STATUS
if "%choice%"=="5" goto EXIT
echo.
echo ✗ Pilihan tidak valid!
goto MENU

:INSTALL_REGISTRY
echo.
echo ══════════════════════════════════════════════════════════
echo  INSTALL AUTO-STARTUP (REGISTRY METHOD)
echo ══════════════════════════════════════════════════════════
echo.
set /p exe_path="Masukkan path lengkap file .exe: "

if not exist "%exe_path%" (
    echo.
    echo ✗ File tidak ditemukan: %exe_path%
    pause
    goto MENU
)

echo.
echo Menambahkan ke Registry...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DigitalIPClock" /t REG_SZ /d "%exe_path%" /f >nul 2>&1

if %errorlevel%==0 (
    echo.
    echo ✓ BERHASIL! Auto-startup telah diaktifkan
    echo   App Name: DigitalIPClock
    echo   Path: %exe_path%
    echo   Method: Windows Registry
    echo.
    echo Aplikasi akan otomatis berjalan saat Windows startup.
) else (
    echo.
    echo ✗ GAGAL! Tidak bisa menambahkan ke Registry
)
echo.
pause
goto MENU

:INSTALL_FOLDER
echo.
echo ══════════════════════════════════════════════════════════
echo  INSTALL AUTO-STARTUP (STARTUP FOLDER METHOD)
echo ══════════════════════════════════════════════════════════
echo.
set /p exe_path="Masukkan path lengkap file .exe: "

if not exist "%exe_path%" (
    echo.
    echo ✗ File tidak ditemukan: %exe_path%
    pause
    goto MENU
)

set startup_folder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set shortcut_path=%startup_folder%\DigitalIPClock.bat

echo.
echo Membuat shortcut di Startup Folder...

echo @echo off > "%shortcut_path%"
echo start "" "%exe_path%" >> "%shortcut_path%"

if exist "%shortcut_path%" (
    echo.
    echo ✓ BERHASIL! Auto-startup telah diaktifkan
    echo   Shortcut: %shortcut_path%
    echo   Target: %exe_path%
    echo   Method: Startup Folder
    echo.
    echo Aplikasi akan otomatis berjalan saat Windows startup.
) else (
    echo.
    echo ✗ GAGAL! Tidak bisa membuat shortcut
)
echo.
pause
goto MENU

:UNINSTALL
echo.
echo ══════════════════════════════════════════════════════════
echo  HAPUS AUTO-STARTUP
echo ══════════════════════════════════════════════════════════
echo.
echo Menghapus dari Registry...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DigitalIPClock" /f >nul 2>&1

if %errorlevel%==0 (
    echo ✓ Berhasil dihapus dari Registry
) else (
    echo ○ Tidak ada entry di Registry
)

echo.
echo Menghapus dari Startup Folder...
set startup_folder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set shortcut_path=%startup_folder%\DigitalIPClock.bat

if exist "%shortcut_path%" (
    del "%shortcut_path%" >nul 2>&1
    echo ✓ Berhasil dihapus dari Startup Folder
) else (
    echo ○ Tidak ada shortcut di Startup Folder
)

echo.
echo ✓ SELESAI! Auto-startup telah dihapus
echo.
pause
goto MENU

:CHECK_STATUS
echo.
echo ══════════════════════════════════════════════════════════
echo  STATUS AUTO-STARTUP
echo ══════════════════════════════════════════════════════════
echo.
echo [1] CEK REGISTRY METHOD
echo    -------------------------------------------------------
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DigitalIPClock" >nul 2>&1

if %errorlevel%==0 (
    echo    Status: ✓ AKTIF
    echo.
    for /f "tokens=3*" %%a in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "DigitalIPClock" 2^>nul ^| findstr "DigitalIPClock"') do (
        echo    Path: %%a %%b
    )
) else (
    echo    Status: ○ TIDAK AKTIF
)

echo.
echo [2] CEK STARTUP FOLDER METHOD
echo    -------------------------------------------------------
set startup_folder=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set shortcut_path=%startup_folder%\DigitalIPClock.bat

if exist "%shortcut_path%" (
    echo    Status: ✓ AKTIF
    echo    Path: %shortcut_path%
) else (
    echo    Status: ○ TIDAK AKTIF
)

echo.
echo ══════════════════════════════════════════════════════════
echo.
pause
goto MENU

:EXIT
echo.
echo Terima kasih telah menggunakan Auto Startup Installer!
echo.
timeout /t 2 >nul
exit

:EOF