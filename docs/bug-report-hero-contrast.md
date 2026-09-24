# Bug Report: Hero text has insufficient color contrast

## Summary

The course-assistant title and the descriptive labels beside the dashboard statistics appeared as dark navy text on the dark hero background. They were difficult to read and did not visually match the white, charcoal, and Leeds-gold theme.

## Evidence

The supplied screenshot showed:

- `MBAX 6418 Course Assistant` rendered in dark navy against the charcoal gradient;
- `lecture decks`, `slides`, and `text and visual records` rendered in the same low-contrast color; and
- the introductory sentence and numeric values remaining readable, which made the inconsistent styling especially visible.

## Steps to reproduce

1. Start the application with `python app.py`.
2. Open the local or shared Gradio URL.
3. View the hero banner at the top of the page.
4. Compare the course title and statistic labels with the banner background.

## Expected behavior

- The course title should be high-contrast off-white.
- Statistic labels should use a readable neutral gray.
- The school name should retain the Leeds-inspired gold accent.
- The complete banner should remain legible in both light and dark browser themes.

## Actual behavior before the fix

Gradio's theme rules overrode inherited text colors for the heading and nested statistic text. The resulting navy-on-charcoal combinations had poor contrast, while adjacent text used the intended light colors.

## Root cause

The custom CSS set a color on the parent `.hero`, but it did not explicitly override colors applied by Gradio to nested headings and spans. The theme's more specific component rules won the cascade.

## Fix

The hero CSS now explicitly applies:

- `#f8fafc` to the title and numeric values;
- `#e7e5e4` to the introductory copy;
- `#d6d3d1` to statistic labels; and
- `#fbbf24` to the Leeds School of Business eyebrow.

The selectors are scoped beneath `.hero` and use `!important` only where necessary to defeat Gradio's component-level theme rules.

## Status

Fixed and visually verified in the relaunched Gradio interface. The title, description, statistic values, and statistic labels are now clearly readable and consistent with the charcoal, off-white, and Leeds-gold palette.
