# Continue beat

Skip the black sweep transition into the next beat — content stays on screen.

## When to use

- Setup and punchline split across two beats but should feel continuous
- Multi-part explanation without a full fade-to-black between sections
- Chained statements where the background and label can carry over

## Beat script

```
CONTINUE:   yes
```

Add in the beat header block (after `ICON_ENTRANCE` or `HOLD`).

## Beats editor

Select beat → check **Continue into next beat** → save.

## JSON

```json
{
  "continue_beat": true
}
```

## What happens at render

When `continue_beat` is true, the beat interpreter **skips** the standard black sweep / `beat_transition` into the next beat. The next beat builds on the existing scene state.

When false (default), each beat ends with fade-out and transition.

## Example — Chat prompt

> "Make beat 1 continue into beat 2 without fading to black."

## Related

- [Beat script format](beat-script)
- [Camera](camera) — still use `cam_restore` within moving beats
- [Animations](animations)
