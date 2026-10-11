# Screenshots Directory

Place your dashboard screenshots here and reference them in `README.md`.

## Suggested Shots

| File | Description | Suggested Size |
|------|-------------|----------------|
| `dashboard.png` | Dashboard tab — hero, KPIs, carousel, AQI gauge | 1600×1000 |
| `historical.png` | Historical Analysis — trends, extremes, microclimate | 1600×1000 |
| `forecast.png` | Weather Forecast — cards, charts, pollutant grid | 1600×1000 |
| `dark-mode-detail.png` | Close-up of design system (typography, cards, gauge) | 1200×800 |
| `mobile.png` | Responsive view (mobile width) | 375×800 |

## How to Capture

```powershell
# Run app
streamlit run app.py

# In browser:
# 1. Navigate to each tab
# 2. Use browser devtools (F12) → device toolbar (Ctrl+Shift+M)
# 3. Set to 1600×1000 (desktop) or 375×800 (mobile)
# 4. Screenshot (Ctrl+Shift+P → "Capture screenshot")
# 5. Save to this folder
```

## GIF Recording (Optional)

For the README hero animation:

```powershell
# Using ScreenToGif (Windows) or Kap (Mac) or peek (Linux)
# Record ~10-15 seconds of:
# - Carousel drag scroll
# - Tab switching
# - Hover effects on cards
# Export as optimized GIF (< 2MB)
# Save as `assets/screenshots/demo.gif`
```

Then update README.md:
```markdown
![Demo](assets/screenshots/demo.gif)
```