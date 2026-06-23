@echo off
title Package Auto Ball Clicker
echo =====================================
echo   Package Auto Ball Clicker to EXE
echo =====================================
echo.

set PYTHON=C:\Users\Zliang\.workbuddy\binaries\python\envs\default\Scripts\python.exe
set SCRIPT=C:\Users\Zliang\WorkBuddy\2026-06-22-22-23-33\auto_ball_clicker.py

echo [1/3] Installing PyInstaller...
%PYTHON% -m pip install pyinstaller -q

echo [2/3] Building EXE (1-2 min)...
%PYTHON% -m PyInstaller --onefile --noconsole --name "AutoBallClicker" --collect-all numpy --collect-all cv2 --clean "%SCRIPT%"

echo [3/3] Copying to Desktop...
copy /Y "dist\AutoBallClicker.exe" "%USERPROFILE%\Desktop\AutoBallClicker.exe"

echo.
echo =====================================
echo   Done!
echo   - dist\AutoBallClicker.exe
echo   - Desktop\AutoBallClicker.exe
echo   NOTE: Run as Administrator for hotkeys
echo =====================================
echo.
pause
