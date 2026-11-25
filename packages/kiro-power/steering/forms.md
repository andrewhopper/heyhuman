# Form patterns

- Yes/no: two buttons, `decide('approved')` and `decide('denied')`, or the `approve-deny` template.
- Choice: one button per option, `decide('<id>')`.
- Image grid: a 2-column grid of tappable tiles, each calling `decide('<name>')`.
- Stars: store the rating in a variable and submit JSON, for example `decide(JSON.stringify(ratings))`.
- Time slot: show busy and free slots, submit the chosen slot.
- Slider and toggle: plain `<input type="range">` and a styled checkbox; read them in a Submit button's handler. Untested here.

Keep tap targets at least 56px tall and use one column. The form runs in a sandbox with no network access. Test the form's JavaScript before sending it.
