#!/bin/bash
# The cheap first pass. These filters default to 2 s, which lets a one-frame fault through, so lower them.
ffmpeg -hide_banner -nostdin -i "$1" \
  -vf "blackdetect=d=0.04:pix_th=0.10:pic_th=0.98,freezedetect=n=-60dB:d=0.4,scdet=t=10,metadata=print:key=lavfi.scd.time:file=-" \
  -af "silencedetect=n=-45dB:d=0.1,ebur128=peak=true:framelog=quiet" \
  -f null - 2>&1 | grep -E "black_start|freeze_start|freeze_duration|silence_start|silence_duration|lavfi.scd.time|I:  |Peak:"
