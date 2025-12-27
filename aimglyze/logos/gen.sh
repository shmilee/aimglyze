#!/bin/bash
# Copyright (C) 2025 shmilee

for sxs in 16x16 32x32 64x64 128x128 256x256; do
    magick convert aimglyze-light.png -resize ${sxs} aimglyze-light-${sxs}.png
done

magick convert aimglyze-light-{16x16,32x32,64x64}.png aimglyze-light.ico
magick convert aimglyze-light-16x16.png aimglyze-light-16x16.ico
