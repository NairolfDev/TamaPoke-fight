@echo off
rem Flasht die zuletzt gebaute Firmware auf das Geraet - OHNE den Spielstand
rem anzufassen.
rem
rem   flash.bat          fragt nach dem Port
rem   flash.bat COM3     ohne Rueckfrage nach dem Port
rem   flash.bat 3        "3" wird zu COM3
rem
rem Geschrieben werden Bootloader, Partitionstabelle, boot_app0 und App - genau
rem die Liste in build\battle\flash_args, die der ESP32-Core bei jedem Build
rem anlegt. NICHT das 16-MB-Vollabbild merged.bin: das enthaelt an der Stelle
rem des Spielstands (NVS, 0x9000) nur 0xFF und loescht das Pokemon. So ist es
rem beim Flash von Phase 5 passiert. tools\check_flash.py prueft das vorher.
rem
rem Vorher bauen mit:  tools\build.ps1
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "BUILD=build\battle"
if not exist "%BUILD%\flash_args" (
  echo FEHLER: %BUILD%\flash_args fehlt. Erst bauen: tools\build.ps1
  goto fail
)

rem Schutz des Spielstands: bricht ab, wenn irgendein Teil NVS beruehrt.
python3 tools\check_flash.py "%BUILD%"
if errorlevel 1 (
  echo FEHLER: Flashen abgebrochen - entweder wuerde der Spielstand geloescht,
  echo oder python3 fehlt. Ohne diese Pruefung wird nicht geflasht.
  goto fail
)

rem esptool liegt in einem Ordner mit Versionsnummer, die sich mit jedem
rem Core-Update aendert - deshalb suchen statt fest eintragen.
set "ESPTOOL="
for /d %%D in ("%LOCALAPPDATA%\Arduino15\packages\esp32\tools\esptool_py\*") do (
  if exist "%%D\esptool.exe" set "ESPTOOL=%%D\esptool.exe"
)
if not defined ESPTOOL (
  echo FEHLER: esptool.exe nicht gefunden unter
  echo   %LOCALAPPDATA%\Arduino15\packages\esp32\tools\esptool_py\
  echo Ist der ESP32-Core installiert?  arduino-cli core list
  goto fail
)

rem Welcher Stand wird geflasht? version.h schreibt tools\build.ps1.
set "HASH=unbekannt"
if exist version.h (
  for /f "tokens=3" %%H in ('findstr /c:"#define FW_GIT" version.h') do set "HASH=%%~H"
)
echo.
echo Stand:   !HASH!
echo esptool: %ESPTOOL%
echo.
echo !HASH! | findstr /i /c:"dirty" /c:"unbekannt" >nul
if not errorlevel 1 (
  echo ACHTUNG: Der Stand ist nicht sauber committet ^(oder unbekannt^).
  echo Am Geraet ist dann nicht nachvollziehbar, was drauf ist.
  echo Sauber geht es so: committen, dann tools\build.ps1, dann flash.bat
  set /p "GO=Trotzdem flashen? [j/N] "
  if /i not "!GO!"=="j" goto abort
)

set "PORT=%~1"
if not defined PORT (
  echo Verfuegbare Ports zeigt:  arduino-cli board list
  set /p "PORT=COM-Port (z.B. COM3): "
)
if not defined PORT goto abort
rem nur Ziffern eingegeben? Dann COM davor.
echo !PORT!| findstr /r "^[0-9][0-9]*$" >nul && set "PORT=COM!PORT!"

echo.
echo Nur ein Programm darf den Port halten - Serial-Monitor vorher schliessen.
echo Flashe !PORT! ...
echo.
rem flash_args nennt die Dateien relativ zum Build-Ordner.
pushd "%BUILD%"
"%ESPTOOL%" --chip esp32s3 --port !PORT! --baud 921600 --before default-reset --after hard-reset write-flash @flash_args
set "RC=!errorlevel!"
popd
if not "!RC!"=="0" (
  echo.
  echo FEHLER beim Flashen. Port pruefen ^(arduino-cli board list^),
  echo Serial-Monitor schliessen, Kabel pruefen.
  goto fail
)
echo.
echo Fertig. Der Spielstand ist unangetastet.
echo Nach dem Neustart zeigt die Bootzeile:  TamaPoke fw v1.5 ^(!HASH!^)
echo Der Port kann sich dabei neu anmelden - arduino-cli board list.
endlocal
exit /b 0

:abort
echo Abgebrochen, nichts geflasht.
endlocal
exit /b 1

:fail
endlocal
exit /b 1
