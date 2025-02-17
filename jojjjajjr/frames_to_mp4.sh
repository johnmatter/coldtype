#!/bin/bash
frame_dir=/Users/matter/coldtype/coldtype/jojjjajjr/renders/circles/circles
filename_template=circles_%04d.png
frame_rate=25
crf_value=22

ffmpeg \
    -f image2 \
    -framerate $frame_rate \
    -i "$frame_dir/$filename_template" \
    -vcodec libx264 \
    -crf $crf_value \
    -pix_fmt yuv420p \
    video.mp4
