@echo off
chcp 65001 > nul
title Prompt Vault
echo.
echo  ========================================
echo    Prompt Vault を起動しています...
echo    ブラウザが自動的に開きます
echo    終了するにはこのウィンドウを閉じてください
echo  ========================================
echo.

cd /d %~dp0

rem ポート5000を使用中のプロセスを終了させる
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":5000 "') do (
    if not "%%a"=="0" (
        taskkill /PID %%a /F > nul 2>&1
    )
)
timeout /t 1 /nobreak > nul

python app.py
pause
