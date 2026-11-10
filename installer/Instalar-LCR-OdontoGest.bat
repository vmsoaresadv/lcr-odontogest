@echo off
chcp 65001 > nul
title Instalador LCR OdontoGest — Dra. Lara Camila
color 0F

echo ============================================================
echo        INSTALADOR OFICIAL — LCR ODONTOGEST v1.0
echo             Dra. Lara Camila — CRO-BA 15247
echo ============================================================
echo.
echo [1/4] Verificando conexao com a internet...
ping -n 1 8.8.8.8 >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Sem conexao com a internet. Conecte o computador a rede e tente novamente.
    pause
    exit /b 1
)

set "REPO=vmsoaresadv/lcr-odontogest"
set "DEST_DIR=C:\LCR-OdontoGest"
set "TEMP_ZIP=%TEMP%\LCR-OdontoGest-Latest.zip"

echo [2/4] Consultando versao mais recente no GitHub (%REPO%)...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ProgressPreference = 'Continue'; " ^
    "try { " ^
    "   [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "   $rel = Invoke-RestMethod -Uri 'https://api.github.com/repos/%REPO%/releases/latest'; " ^
    "   $tag = $rel.tag_name; " ^
    "   Write-Host \"[INFO] Versao encontrada: $tag\"; " ^
    "   $asset = $rel.assets | Where-Object { $_.name -like '*.zip' } | Select-Object -First 1; " ^
    "   if (-not $asset) { throw 'Nenhum pacote .zip encontrado na ultima release.' } " ^
    "   Write-Host \"[INFO] Baixando arquivos do pacote ($($asset.name))...\"; " ^
    "   Invoke-WebRequest -Uri $asset.browser_download_url -OutFile '%TEMP_ZIP%'; " ^
    "   Write-Host '[INFO] Download concluido com sucesso!'; " ^
    "} catch { " ^
    "   Write-Error $_.Exception.Message; exit 1; " ^
    "}"

if errorlevel 1 (
    echo.
    echo [AVISO] Nao foi possivel baixar automaticamente da nuvem no momento.
    echo Certifique-se de que a Release com o arquivo .zip foi publicada no GitHub.
    pause
    exit /b 1
)

echo.
echo [3/4] Instalando em %DEST_DIR%...
if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Expand-Archive -Path '%TEMP_ZIP%' -DestinationPath '%DEST_DIR%' -Force; " ^
    "Remove-Item '%TEMP_ZIP%' -Force -ErrorAction SilentlyContinue;"

echo.
echo [4/4] Criando atalho oficial na Area de Trabalho...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$w = New-Object -ComObject WScript.Shell; " ^
    "$desk = [Environment]::GetFolderPath('Desktop'); " ^
    "$s = $w.CreateShortcut((Join-Path $desk 'LCR OdontoGest.lnk')); " ^
    "$exe = (Join-Path '%DEST_DIR%' 'LCR-OdontoGest.exe'); " ^
    "if (-not (Test-Path $exe)) { " ^
    "   $sub = Get-ChildItem -Path '%DEST_DIR%' -Filter 'LCR-OdontoGest.exe' -Recurse | Select-Object -First 1; " ^
    "   if ($sub) { $exe = $sub.FullName } " ^
    "} " ^
    "$s.TargetPath = $exe; " ^
    "$s.WorkingDirectory = (Split-Path $exe -Parent); " ^
    "$ico = Join-Path (Split-Path $exe -Parent) 'assets\app_icon.ico'; " ^
    "if (Test-Path $ico) { $s.IconLocation = $ico; } " ^
    "$s.Save();"

echo.
echo ============================================================
echo   [SUCESSO] LCR ODONTOGEST INSTALADO COM SUCESSO!
echo ============================================================
echo.
echo Iniciando o sistema agora...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$exe = (Join-Path '%DEST_DIR%' 'LCR-OdontoGest.exe'); " ^
    "if (-not (Test-Path $exe)) { " ^
    "   $sub = Get-ChildItem -Path '%DEST_DIR%' -Filter 'LCR-OdontoGest.exe' -Recurse | Select-Object -First 1; " ^
    "   if ($sub) { $exe = $sub.FullName } " ^
    "} " ^
    "Start-Process $exe -WorkingDirectory (Split-Path $exe -Parent);"

timeout /t 3 > nul
exit /b 0
