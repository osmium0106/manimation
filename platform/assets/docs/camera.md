# Camera

Pan and zoom between left/right panels when moving camera is enabled.

## Enabling camera

**Project level** (episode meta):

```
CAMERA: moving          # none | moving
```

**Per beat** — in Beats editor **Camera** tab, check **Use moving camera on this beat**, or in script:

```
CAMERA:     yes
```

When enabled, Studio uses **MovingBeatScene** — the frame can pan and zoom between panels. Uncheck on a beat to keep that beat static even if the project uses camera elsewhere.

## Camera hooks (beat script)

```
─── CAMERA ───
cam_focus_left: after_icon
cam_focus_right: after_line_1
cam_focus_card: punchline
cam_restore: exit
```

| Action | When (hook) |
|--------|-------------|
| `cam_focus_left` | Focus icon panel — e.g. `after_icon` |
| `cam_focus_right` | Focus card/text panel — e.g. `after_line_1`, `after_line_2` |
| `cam_focus_card` | Zoom on white card — e.g. `punchline` |
| `cam_restore` / `cam_restore_fast` | **`exit`** — required every moving beat |

Common hooks: `after_icon`, `after_line_1`, `after_line_2`, `after_line_3`, `after_code`, `after_output`, `after_run`, `punchline`, `exit`.

## Beats editor — Camera tab

Each camera step is a card with:

- **Header:** duration (seconds) + delete
- **Body:** Action and Hook dropdowns (stacked vertically)

Use **Load defaults for [beat type]** to fill standard hooks from the beat type template. Timeline badge `C{n}` shows step count; `cam` when camera is enabled.

Icon entrance runs **after** camera pans to the icon panel when camera is on.

## Rules

1. Every beat that uses pan/zoom must end with **`cam_restore: exit`**
2. Before `beat_transition` (fade to black), restore frame if previous beat moved camera
3. **3–4 icon word-sync:** camera restores to **full frame** so card + icon grid stay visible

## Example — question beat

```
TYPE:       question
LAYOUT:     text_right_icon_left
CAMERA:     moving

─── CAMERA ───
cam_focus_left: after_icon
cam_focus_right: after_line_1
cam_restore: exit

HOLD: 1.2s
```

## JSON

```json
{
  "use_camera": true,
  "camera": [
    {"hook": "after_icon", "action": "cam_focus_left", "run_time": 0.9},
    {"hook": "after_line_1", "action": "cam_focus_right", "run_time": 0.9},
    {"hook": "exit", "action": "cam_restore", "run_time": 0.9}
  ]
}
```

## Related

- [Icon reveal](icon-reveal)
- [Icon entrances](icon-entrances)
- [Continue beat](continue-beat)
- [Studio UI](studio-ui)
