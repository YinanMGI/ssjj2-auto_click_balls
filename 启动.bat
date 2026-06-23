@echo off
title Auto Ball Clicker
echo =====================================
echo   Auto Ball Clicker v1.0
echo =====================================
echo.
echo [1] Normal mode
echo [2] Slow debug mode (visible mouse)
echo.
set /p choice="Choose (1/2): "
if "%choice%"=="2" goto slow
if "%choice%"=="1" goto normal
goto normal

:normal
echo Starting normal mode...
"C:\Users\Zliang\.workbuddy\binaries\python\envs\default\Scripts\python.exe" "C:\Users\Zliang\WorkBuddy\2026-06-22-22-23-33\auto_ball_clicker.py"
goto end

:slow
echo Starting SLOW debug mode...
"C:\Users\Zliang\.workbuddy\binaries\python\envs\default\Scripts\python.exe" "C:\Users\Zliang\WorkBuddy\2026-06-22-22-23-33\auto_ball_clicker.py" --slow
goto end

:end
pause
