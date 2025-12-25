# Asteroid Impact Calculator

A simple Flask app for estimating asteroid impact effects.

## Requirements
- Python 3.10+
- pip

## Setup (Windows PowerShell)
1. Navigate to the project folder:
```powershell
cd C:\Users\AMITHAB\OneDrive\Documents\Asteroid
```
2. (Optional) Create and activate a virtual environment:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
3. Install dependencies:
```powershell
pip install -r requirements.txt
```

## Run
```powershell
python app.py
```
Then open:
- http://127.0.0.1:5000/

Press Ctrl+C in the terminal to stop the server.

## Project Structure
```
Asteroid/
  app.py               # Flask app
  requirements.txt     # Python dependencies
  templates/           # Jinja2 templates (index.html, result.html)
  static/              # Static assets (optional; currently empty)
```

## Troubleshooting
- ERR_FILE_NOT_FOUND: Access the app via http://127.0.0.1:5000/ rather than double-clicking HTML files.
- PowerShell command chaining: Avoid using `&&`. Run commands on separate lines, or use `;`.
- Template errors: Ensure `index.html` and `result.html` are inside the `templates/` folder. 