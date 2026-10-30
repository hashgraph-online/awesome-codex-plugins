#!/usr/bin/env bash
# Synthesizes the demo's 16 s soundtrack with ffmpeg only (no samples, no rights issues):
# 120 BPM, A minor progression Am-F-C-G (one chord per 2 s bar).
#   kick  : pitch-dropping sine on every beat
#   bass  : sub sine, ducked after each kick (sidechain-style pump)
#   pad   : soft chord tones
#   arp   : 16th-note plucks two octaves up (gives the upper bands something to do)
#   hat   : high-passed noise on the off-beats
#   clap  : band-passed noise on beats 2 and 4
# Output: assets/beat.m4a   Run from examples/demo:  bash tools/make-beat.sh
set -euo pipefail
D=16
SR=44100
B='floor(mod(t,8)/2)' # bar index 0..3 within the 8 s loop
ROOT="if(eq($B,0),55,if(eq($B,1),43.65,if(eq($B,2),65.41,49)))"
C1="if(eq($B,0),220,if(eq($B,1),174.61,if(eq($B,2),261.63,196)))"
C2="if(eq($B,0),261.63,if(eq($B,1),220,if(eq($B,2),329.63,246.94)))"
C3="if(eq($B,0),329.63,if(eq($B,1),261.63,if(eq($B,2),392,293.66)))"
STEP='mod(floor(t/0.125),4)'
ARP="if(eq($STEP,0),4*$C1,if(eq($STEP,1),4*$C2,if(eq($STEP,2),4*$C3,2*$C3)))"

KICK="0.95*sin(2*PI*(45*mod(t,0.5)+3.57*(1-exp(-28*mod(t,0.5)))))*exp(-7*mod(t,0.5))"
BASS="0.32*sin(2*PI*$ROOT*t)*(1-exp(-9*mod(t,0.5)))"
PAD="0.05*(sin(2*PI*$C1*t)+sin(2*PI*$C2*t)+sin(2*PI*$C3*t)+0.3*sin(4*PI*$C2*t))"
ARPX="0.11*sin(2*PI*$ARP*t)*exp(-16*mod(t,0.125))"

ffmpeg -v error -y \
  -f lavfi -i "aevalsrc=exprs='$KICK+$BASS+$PAD+$ARPX':s=$SR:d=$D" \
  -f lavfi -i "anoisesrc=d=$D:c=white:r=$SR:a=0.6:seed=7" \
  -f lavfi -i "anoisesrc=d=$D:c=pink:r=$SR:a=0.8:seed=11" \
  -filter_complex "\
[1:a]highpass=f=7000,asetnsamples=n=32,volume=eval=frame:volume='0.55*exp(-45*mod(t+0.25,0.5))'[hat];\
[2:a]bandpass=f=1800:width_type=h:w=1400,asetnsamples=n=32,volume=eval=frame:volume='0.9*exp(-14*mod(t+0.5,1.0))*gte(t,0.5)'[clap];\
[0:a][hat][clap]amix=inputs=3:normalize=0,alimiter=limit=0.89,afade=t=in:d=0.02,afade=t=out:st=15.3:d=0.7,aformat=channel_layouts=stereo[out]" \
  -map "[out]" -c:a aac -b:a 112k assets/beat.m4a
echo "wrote assets/beat.m4a"
