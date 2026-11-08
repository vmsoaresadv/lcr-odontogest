@echo off
title LCR Clinica Odontologica
cd /d "%~dp0"
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0main.py"
