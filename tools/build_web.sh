#!/bin/bash
# Erzeugt die Firmware-Teile fuer den Browser-Installer in web/firmware/.
# Aufruf: bash tools/build_web.sh
#
# Vier Teile an ihren eigenen Adressen, wie flash_args sie fuer esptool
# nennt - NICHT ein zusammengefuegtes Abbild ab 0x0. Das enthielt an der
# Stelle der NVS-Partition (0x9000-0xE000) nur 0xFF und loeschte bei jedem
# Update den Spielstand, auch ohne "Erase". web/manifest.json listet dieselben
# vier Teile; tools/check_flash.py --web prueft das am Ende.
set -e
cd "$(dirname "$0")/.."
FQBN="esp32:esp32:esp32s3:CDCOnBoot=cdc,FlashSize=16M,PSRAM=opi,PartitionScheme=app3M_fat9M_16MB"

echo "Kompiliere..."
arduino-cli compile --fqbn "$FQBN" --export-binaries .

B=build/esp32.esp32.esp32s3
echo "Kopiere die vier Teile..."
cp "$B/TamaPoke.ino.bootloader.bin" web/firmware/bootloader.bin   # 0x0
cp "$B/TamaPoke.ino.partitions.bin" web/firmware/partitions.bin   # 0x8000
cp "$B/boot_app0.bin"               web/firmware/boot_app0.bin    # 0xe000
cp "$B/TamaPoke.ino.bin"            web/firmware/app.bin          # 0x10000

python3 tools/check_flash.py --web

echo "Packe die Sprites..."
python3 tools/pack_bundle.py
