# Kompiliert die Firmware und schreibt den Git-Stand mit ins Binary.
#
# Warum ein Wrapper: arduino-cli hat keinen Pre-Build-Hook, der im Sketch-Ordner
# liegt. Den gibt es nur in der platform.txt des Cores - also ausserhalb des
# Repos und beim naechsten Core-Update weg. Deshalb macht dieses Skript beides:
# version.h schreiben, dann bauen.
#
# Aufruf aus einer normalen PowerShell im Repo-Ordner:
#
#   tools\build.ps1
#   tools\build.ps1 -BuildPath build\schnell
#
# Wer stattdessen arduino-cli direkt aufruft, baut mit dem version.h vom
# letzten Lauf dieses Skripts. Deshalb ist das hier der dokumentierte Weg.

param(
  # Ablage der Build-Artefakte, relativ zum Repo. build/ ist gitignored.
  [string]$BuildPath = "build\battle"
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot

# --- Git-Stand ermitteln ---------------------------------------------------
# version.h ist gitignored und faelscht das Ergebnis deshalb nicht, egal in
# welcher Reihenfolge. Trotzdem erst lesen, dann schreiben.
$hash = (git -C $repo rev-parse --short HEAD 2>$null)
if (-not $hash) { throw "git rev-parse hat nichts geliefert - ist $repo ein Repo?" }
$hash = $hash.Trim()
if (git -C $repo status --porcelain) { $hash = "$hash-dirty" }

# --- version.h schreiben --------------------------------------------------
# ASCII ohne BOM. Der Sketch bindet die Datei ueber __has_include ein und
# faellt ohne sie auf "unbekannt" zurueck - sichtbar, nicht still.
$verFile = Join-Path $repo "version.h"
@(
  "// Erzeugt von tools/build.ps1. Nicht von Hand editieren, nicht committen.",
  "#pragma once",
  "#define FW_GIT `"$hash`""
) | Out-File -FilePath $verFile -Encoding ascii
Write-Host "version.h: FW_GIT = $hash"

# --- ueber die Junction bauen ---------------------------------------------
# Arduino verlangt, dass der Ordner genauso heisst wie die Haupt-.ino. Das Repo
# heisst TamaPoke-fight, der Sketch TamaPoke.ino - ein Build direkt im
# Repo-Ordner scheitert mit "main file missing from sketch". Die Junction
# daneben loest das (siehe CLAUDE.md).
$sketch = Join-Path (Split-Path -Parent $repo) "TamaPoke"
if (-not (Test-Path $sketch)) {
  throw @"
Die Junction $sketch fehlt. Einmalig anlegen:
  cmd /c mklink /J "$sketch" "$repo"
"@
}
# Zeigt die Junction auch wirklich auf DIESES Repo? Sonst baut man still den
# falschen Stand - mit gruenem Exitcode und plausibler Groesse.
#
# .Target ist ein String[], kein String. Ohne das [0] vergleicht man ein Array
# gegen einen String, und PowerShell liefert dann eine gefilterte Liste statt
# eines Boolean - im Einzelelement-Fall geht das zufaellig gut, aber verlassen
# sollte man sich darauf nicht. Trailing Backslash haengt von der
# PowerShell-Version ab, deshalb beide Seiten trimmen.
$target = @((Get-Item $sketch).Target)[0]
if ($target -and $target.TrimEnd('\') -ne $repo.TrimEnd('\')) {
  throw "Die Junction $sketch zeigt auf $target, nicht auf $repo."
}

$FQBN = "esp32:esp32:esp32s3:CDCOnBoot=cdc,FlashSize=16M,PSRAM=opi,PartitionScheme=app3M_fat9M_16MB"
arduino-cli compile --fqbn $FQBN --build-path (Join-Path $repo $BuildPath) $sketch
exit $LASTEXITCODE
