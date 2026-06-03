# Code demo beats

Full-width code editor with syntax-colored lines and a terminal output panel.

## When to use

- Live coding walkthroughs
- Showing error output (`result: error`)
- Python, or other languages supported by the code window theme

## Required fields

```
TYPE:       code_demo
LAYOUT:     code_full_card
```

No `ICONS` section required.

## CODE block

```
─── CODE ───
language: python
result: success          # success | error
output: |
  Hello, World!
lines:
  print("Hello, World!")
  print("Done")
```

### Error example

```
─── CODE ───
language: python
result: error
error_line: 2
error: NameError: name 'y' is not defined
output: |
  NameError: name 'y' is not defined
lines:
  x = 1
  print(y)
```

## JSON

```json
{
  "label": "Run Your Code",
  "type": "code_demo",
  "layout": "code_full_card",
  "code_lines": ["print('Hello, World!')"],
  "code_output": "Hello, World!",
  "code_result": "success",
  "hold": 1.5
}
```

## Theming

The active project **theme palette** wires into code window colors (background, gutter, syntax) at render time.

## Related

- [Beat types](beat-types)
- [Layouts](layouts)
- [Themes](themes)
