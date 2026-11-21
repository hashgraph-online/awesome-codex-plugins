# Generating a source clip that lip-syncs well

The lipsync only replaces the mouth region and blends it in, so the clip has to give it a clear, steady face to work with. Write the video-generation prompt with these in mind, and tell the user why if they ask.

## What to ask the generator for

- **One character, facing the camera or at a slight angle**, head and shoulders or a medium close-up. The face should fill a good part of the frame. A tiny face in a wide shot gives a soft mouth.
- **"Speaking naturally"** or **"talking to the camera"** in the prompt, so the jaw, head and eyebrows already move like speech. A clip of someone standing still with a closed mouth looks wrong once the lips move.
- **A clear view of the mouth:** no hands, microphones, hair, masks or props crossing it.
- **A steady shot:** a locked-off camera or a slow push-in. Avoid whip pans, fast head turns and motion blur across the face.
- **One continuous shot.** If the scene needs several angles, generate them as separate clips.
- **Even, soft lighting on the face**, with no hard flicker or strobe.
- **Length to match the line**, about 2.5 spoken words per second. Most generators make 5 to 10 seconds, which holds one or two sentences.
- **1080p and a constant 24, 25 or 30 fps** where the tool lets you choose.

If the generator also makes audio, either ask for no dialogue, or treat its speech as a placeholder that the new voice replaces.

## Example prompt

> Medium close-up of a woman in her 30s with short dark hair, sitting in a bright, minimal home office, looking straight into the camera and speaking naturally with friendly, relaxed expressions and small head movements. Soft window light, shallow depth of field, locked-off camera, one continuous shot, 8 seconds, no on-screen text.

Adapt the character, setting and mood to the user's idea, but keep the parts about framing, speaking, a steady camera and one continuous shot.

## Before lip-syncing

Check the clip you got back: one face, the mouth visible, no cuts. If the generator added extra people who also move their mouths, pick the speaker with `options.active_speaker_detection`, or regenerate the clip.
