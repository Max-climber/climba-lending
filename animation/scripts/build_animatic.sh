#!/bin/zsh
set -euo pipefail

ROOT='/Users/maksimizrailev/Desktop/climba-lending-2'
OUT="$ROOT/animation/output/climba_animatic_v1.mp4"
python3 "$ROOT/animation/scripts/make_animatic_cards.py"

ffmpeg -y \
  -loop 1 -t 4 -i "$ROOT/animation/output/real_hall_panda_blocking.png" \
  -loop 1 -t 4 -i "$ROOT/animation/output/mascot_v2/mascot_v2_front.png" \
  -ss 8 -t 4 -i '/Users/maksimizrailev/Downloads/ScreenRecording_10-11-2026 22-45-08_1.MP4' \
  -loop 1 -t 5 -i "$ROOT/animation/output/scan_directions/sector_3_W.png" \
  -loop 1 -t 4 -i "$ROOT/animation/output/phone_ui/phone_route.png" \
  -loop 1 -t 3 -i "$ROOT/animation/output/phone_ui/phone_confirm.png" \
  -loop 1 -t 3 -i "$ROOT/animation/output/phone_ui/phone_ranking.png" \
  -loop 1 -t 3 -i "$ROOT/animation/output/mascot_v2/mascot_v2_three_quarter.png" \
  -loop 1 -t 6 -i "$ROOT/animation/output/animatic_end_card.png" \
  -filter_complex "\
    [0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[s0];\
    [1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[s1];\
    [2:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[s2];\
    [3:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[s3];\
    [4:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[s4];\
    [5:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[s5];\
    [6:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[s6];\
    [7:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p[s7];\
    [8:v]scale=1080:1920,setsar=1,fps=30,format=yuv420p[s8];\
    [s0][s1][s2][s3][s4][s5][s6][s7][s8]concat=n=9:v=1:a=0,\
      fade=t=in:st=0:d=0.35,fade=t=out:st=35.5:d=0.5[v]" \
  -map '[v]' -an -c:v libx264 -preset medium -crf 20 -movflags +faststart "$OUT"

printf '%s\n' "$OUT"
