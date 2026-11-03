// Format and timing of the film. No three.js import here, so Bun tools (tools/*.ts) can read it too.
// Cuts sit on bar lines (bpm) so the edit lands on the music.
export const FILM = {
  title: 'Drone at the table (demo)',
  fps: 24,
  bpm: 120,                                // 1 beat = 0.5 s, 1 bar = 2 s
  aspect: 16 / 9,
  export: { width: 854, height: 480 },     // 480p 16:9: the size of the video-to-video reference
  duration: 10,
  audio: null,                             // e.g. 'assets/music.mp3'; without it the UI clicks on every beat
};
export const BEAT = 60 / FILM.bpm;
