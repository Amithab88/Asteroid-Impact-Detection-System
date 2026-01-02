# Asteroid Impact Calculator

A static web application for calculating and visualizing asteroid impact effects. This project is designed to run entirely in the browser with no backend server required.

## Features

- **Impact Calculations**: Calculate kinetic energy, crater diameter, air blast radius, shock wave radius, and thermal radiation radius
- **Target Material Selection**: Choose from different surface materials (Rock, Water, Ice, Sand, Forest)
- **Interactive Visualizations**: 
  - Animated impact visualization with expanding effect rings
  - Bar chart comparing different impact effects
- **Educational Insights**: Learn why different effects have different magnitudes
- **Responsive Design**: Works on desktop and mobile devices

## GitHub Pages Deployment

This is a static website that can be hosted on GitHub Pages:

1. **Push to GitHub**: 
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Enable GitHub Pages**:
   - Go to your repository Settings
   - Navigate to Pages section
   - Select source: `main` branch
   - Select folder: `/ (root)`
   - Click Save

3. **Access your site**: `https://YOUR_USERNAME.github.io/YOUR_REPO/`

## Local Development

Simply open `index.html` in a web browser. No server required!

Or use a local server:
```bash
# Python 3
python -m http.server 8000

# Node.js (with http-server)
npx http-server

# Then visit http://localhost:8000
```

## File Structure

```
Asteroid/
├── index.html              # Main form page
├── result.html             # Results display page
├── static/
│   ├── calculations.js     # All calculation functions (converted from Python)
│   └── impact.js           # Visualization and animation code
└── README.md              # This file
```

## How It Works

1. User enters mass, velocity, target material, and calculation type on `index.html`
2. JavaScript (`calculations.js`) performs all calculations client-side
3. Results are stored in `sessionStorage` and displayed on `result.html`
4. Visualizations are rendered using Canvas API and Chart.js

## Technologies Used

- **HTML5/CSS3**: Structure and styling
- **Vanilla JavaScript**: All calculations and logic
- **Canvas API**: Impact animation
- **Chart.js**: Bar chart visualization
- **Bootstrap 5**: Responsive layout

## Notes

- All calculations are performed client-side (no backend needed)
- Data is passed between pages using `sessionStorage`
- No external dependencies except CDN libraries (Bootstrap, Chart.js)
- Fully compatible with GitHub Pages static hosting

## License

This project is for educational purposes.
