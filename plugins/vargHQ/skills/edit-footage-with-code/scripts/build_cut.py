#!/usr/bin/env python3
"""Turn edit/edl.json into a real cut.

  python3 build_cut.py edit/edl.json --take take.mp4

Writes, next to the EDL:
  cut.sh      ffmpeg rough cut with a short fade at every join (acut.mp4)
  clips.html  the same cut as HyperFrames <video> clips
  Cut.tsx     the same cut as a Remotion <Series>
  cut.fcpxml  the same cut for Resolve or Final Cut: every clip keeps its handles,
              because it points at the whole source

Then transcribe the cut itself and time captions, B-roll and SFX from that transcript.
Do not push the take's word times through the EDL: on our test clip that lost 23 words.
"""
import argparse, json, os, shlex, subprocess
from fractions import Fraction
from xml.sax.saxutils import quoteattr


def fcpxml(edl, segs, fps, take):
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
                                      "-of", "json", take], capture_output=True, text=True, check=True).stdout)
    w, h = info["streams"][0]["width"], info["streams"][0]["height"]
    # 29.97-style rates are 1001-based; everything else is a whole number of frames per second
    frame = Fraction(1001, round(fps * 1001)) if abs(fps - round(fps)) > 0.001 else Fraction(1, round(fps))

    def rt(n):
        v = frame * n
        return "%d/%ds" % (v.numerator, v.denominator) if v.denominator != 1 else "%ds" % v.numerator
    total = round(float(info["format"]["duration"]) / frame)
    uri = "file://" + os.path.abspath(take).replace(" ", "%20")
    rows = "\n".join('            <asset-clip name=%s ref="r2" offset="%s" start="%s" duration="%s" format="r1" tcFormat="NDF" audioRole="dialogue"/>'
                     % (quoteattr(s["id"]), rt(round(s["at"] / frame)), rt(round(s["in"] / frame)), rt(s["frames"])) for s in segs)
    return """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>
<fcpxml version="1.9">
  <resources>
    <format id="r1" frameDuration="%s" width="%d" height="%d"/>
    <asset id="r2" name=%s start="0s" duration="%s" hasVideo="1" hasAudio="1" format="r1" audioSources="1" audioChannels="2">
      <media-rep kind="original-media" src=%s/>
    </asset>
  </resources>
  <library>
    <event name="Rough cut">
      <project name="Rough cut">
        <sequence format="r1" duration="%s" tcStart="0s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">
          <spine>
%s
          </spine>
        </sequence>
      </project>
    </event>
  </library>
</fcpxml>
""" % (rt(1), w, h, quoteattr(os.path.basename(take)), rt(total), quoteattr(uri), rt(edl["frames"]), rows)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("edl"); p.add_argument("--take", required=True)
    p.add_argument("--fade-ms", type=float, default=30, help="audio fade at each join. Use 8 if you moved an in point within 30 ms of a word")
    p.add_argument("--crf", type=int, default=18); p.add_argument("--src", help="path as the composition sees it")
    a = p.parse_args()
    edl = json.load(open(a.edl)); fps = edl["fps"]; segs = edl["segments"]; d = os.path.dirname(a.edl) or "."
    # edit only "in" and "out" by hand: frames and positions are always recomputed here
    t = 0
    for i, s in enumerate(segs):
        s["id"] = "s%03d" % (i + 1)
        s["in"] = round(round(s["in"] * fps) / fps, 4)
        s["frames"] = round((s["out"] - s["in"]) * fps)
        s["out"] = round(s["in"] + s["frames"] / fps, 4)
        s["at"] = round(t / fps, 4)
        t += s["frames"]
    edl["frames"], edl["duration"] = t, round(t / fps, 3)
    json.dump(edl, open(a.edl, "w"), indent=1)
    rate = int(json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=sample_rate", "-of", "json", a.take],
                                         capture_output=True, text=True, check=True).stdout)["streams"][0]["sample_rate"])
    # ffmpeg: frame-accurate, re-encoded, one fade per join
    parts, chain = [], []
    for i, s in enumerate(segs):
        ln = s["frames"] / fps
        f_in, f_out = s.get("fade_in_ms", a.fade_ms) / 1000, s.get("fade_out_ms", a.fade_ms) / 1000  # one join can differ
        f0 = round(s["in"] * fps)  # by frame number: time-based trims gained 2 frames over 14 clips on our test
        parts.append("[0:v]trim=start_frame=%d:end_frame=%d,setpts=PTS-STARTPTS[v%d]" % (f0, f0 + s["frames"], i))
        # by sample number for the same reason: rounded seconds move later joins by a frame
        parts.append("[0:a]atrim=start_sample=%d:end_sample=%d,asetpts=PTS-STARTPTS,afade=t=in:d=%.3f,afade=t=out:st=%.4f:d=%.3f[a%d]"
                     % (round(f0 / fps * rate), round((f0 + s["frames"]) / fps * rate), f_in, max(0, ln - f_out), f_out, i))
        chain.append("[v%d][a%d]" % (i, i))
    graph = ";".join(parts) + ";" + "".join(chain) + "concat=n=%d:v=1:a=1[v][a]" % len(segs)
    open(os.path.join(d, "filter.txt"), "w").write(graph)
    open(os.path.join(d, "cut.sh"), "w").write(
        "#!/bin/sh\n# Rough cut from the EDL. Never overwrites the source.\nffmpeg -y -i %s -filter_complex \"$(cat %s)\" -map '[v]' -map '[a]' "
        "-c:v libx264 -crf %d -preset veryfast -fps_mode passthrough -g %d -pix_fmt yuv420p -c:a aac -b:a 256k -ar 48000 -movflags +faststart %s\n"
        % (shlex.quote(a.take), shlex.quote(os.path.join(d, "filter.txt")), a.crf, round(fps), shlex.quote(os.path.join(d, "acut.mp4"))))
    # HyperFrames: sound stays on the <video>, so cutting the clip cuts its sound
    src = a.src or a.take
    html = ['<!-- %d clips, %.3f s. Each id is required: the mixer ignores timed media without one. -->' % (len(segs), edl["duration"])]
    for s in segs:
        html.append('<video id="%s" class="clip" src="%s" data-start="%.4f" data-duration="%.4f" data-media-start="%.4f" '
                    'data-track-index="0" playsinline data-has-audio="true" style="position:absolute;inset:0;width:100%%;height:100%%;object-fit:cover"></video>'
                    % (s["id"], src, s["at"], s["frames"] / fps, s["in"]))
    open(os.path.join(d, "clips.html"), "w").write("\n".join(html) + "\n")
    # Remotion: durations and trims in frames, never in seconds
    rows = ",\n".join("  {id: '%s', trimBefore: %d, frames: %d}" % (s["id"], round(s["in"] * fps), s["frames"]) for s in segs)
    open(os.path.join(d, "Cut.tsx"), "w").write(
        "import {Series, staticFile} from 'remotion';\nimport {Video} from '@remotion/media';\n\n"
        "// %d clips at %s fps: %d frames. Set the composition's durationInFrames to CUT_FRAMES.\nconst CUT = [\n%s,\n];\n"
        "export const CUT_FRAMES = CUT.reduce((n, c) => n + c.frames, 0);\n\n"
        "export const Cut = () => (\n  <Series>\n    {CUT.map((c) => (\n      <Series.Sequence key={c.id} durationInFrames={c.frames}>\n"
        "        <Video src={staticFile('%s')} trimBefore={c.trimBefore} durationInFrames={c.frames} />\n"
        "      </Series.Sequence>\n    ))}\n  </Series>\n);\n" % (len(segs), fps, edl["frames"], rows, os.path.basename(src)))
    open(os.path.join(d, "cut.fcpxml"), "w").write(fcpxml(edl, segs, fps, a.take))
    out = {"clips": len(segs), "duration": edl["duration"], "files": ["cut.sh", "clips.html", "Cut.tsx", "cut.fcpxml"]}
    print(json.dumps(out))


if __name__ == "__main__":
    main()
