# Redesign

Run Pull first, because each move has to come from a widget it found.

1. Freeze the baseline. Follow steps 1 and 2 of audit.md to get the frames of the current widget and the job line. Those files and their sample data stay unchanged from here on. Done when the frames are saved and the job line is written.
2. Walk the job. Go through the job line against the baseline frames, one step at a time, and note where the user slows or stops. Done when every step has a note, even if the note is "fine".
3. Make at most five moves. Each move says what changes, which step it helps, and which widget it comes from, with the mark that widget earns. Cut any move no pulled widget shows. If Pull found nothing, say the whole redesign is opinion and mark every move so.
4. Keep the user's design system and copy: their tokens, components, fonts and strings stay. A move that would need new copy or a new token goes in the report as a question.
5. Show before and after. Render the new version at the baseline's frames with the same sample data, and pair each one with its baseline frame. If you can't render, give the moves as a written spec and mark the after frames missing.

Done when there are five moves or fewer, each one cites a widget or is marked opinion, and every frame has a before and after pair or is marked missing.
