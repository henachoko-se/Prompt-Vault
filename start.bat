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
python app.py
pause
