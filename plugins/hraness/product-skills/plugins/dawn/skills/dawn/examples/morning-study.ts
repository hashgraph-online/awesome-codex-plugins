import { progression, seq, song, track } from "dawn";

// Copy into song.ts in a fresh `dawn init` project. All voices are synthesized.
export default song({
  tempo: 104,
  meter: [4, 4],
  bars: 8,
  key: "D minor",
  sections: [
    { name: "Question", startBar: 0, bars: 4 },
    { name: "Answer", startBar: 4, bars: 4 },
  ],
  tracks: [
    track({
      name: "Melody",
      instrument: "triangle",
      volume: 0.55,
      notes: seq(
        "D5 . F5 A5 G5 F5 . E5 D5 . A4 C5 E5 . C5 A4 " +
          "F5 A5 . G5 E5 D5 . C5 A4 C5 E5 G5 F5 E5 D5 .",
        { step: 1, len: 0.7, vel: 0.65 },
      ),
    }),
    track({
      name: "Harmony",
      instrument: "organ",
      volume: 0.22,
      notes: progression("i VI iv V i VI iv i", { key: "D minor" }),
    }),
    track({
      name: "Bass",
      instrument: "bass",
      volume: 0.45,
      notes: seq("D2 A2 Bb1 F2 G1 D2 A1 E2 D2 A2 Bb1 F2 G1 D2 D2 .", {
        step: 2,
        len: 1.3,
        vel: 0.7,
      }),
    }),
  ],
});
