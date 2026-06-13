# Microscope Usage Tracker

A desktop app for microscopy core facilities to log instrument usage, track session time, and calculate costs — all stored locally with no internet required.

---

## Features

- Log **Microscope Usage** with a live timer and automatic cost calculation
- Log **Sample Preparation** with per-sample pricing
- **Admin panel** (PIN-protected) to add, edit, or remove instruments and rates
- **History tab** to browse all past sessions
- **Export to CSV** for billing or reporting
- All data stored locally in a SQLite database

---

## Installation

### Requirements
- Python 3.8 or higher
- conda (recommended) or pip

### Option 1 — conda (recommended)

```bash
git clone https://github.com/VismayaShhree/Microscope_use.git
cd Microscope_use
conda create -n microscope_use python=3.8
conda activate microscope_use
pip install -r requirements.txt
python Microscope_use.py
```

### Option 2 — pip only

```bash
git clone https://github.com/VismayaShhree/Microscope_use.git
cd Microscope_use
pip install -r requirements.txt
python Microscope_use.py
```

---

## First-Time Setup (Facility Admin)

1. Run the app once — it creates `config.json` and `microscope_usage.db` automatically.
2. Go to the **Admin** tab and enter the default PIN: `1234`
3. **Change the PIN immediately** using the "Change Admin PIN" section.
4. Add or edit your facility's instruments and rates.

---

## Configuring Instruments

Instruments can be managed two ways:

**Via the Admin tab (recommended):**  
Admin tab → Unlock → Add / Edit / Remove instruments

**Via `config.json` directly:**  
Edit the file in any text editor. Each instrument looks like:

```json
"SEM": {
  "full_name": "Scanning Electron Microscope",
  "hourly_rate": 35,
  "enabled": true
}
```

Set `"enabled": false` to hide an instrument without deleting its history.

---

## Building a Standalone App (optional)

To package into a `.app` (Mac) or `.exe` (Windows):

```bash
pip install pyinstaller
pyinstaller --windowed Microscope_use.py
```

The built app appears in the `dist/` folder. Keep `config.json` in the same folder as the `.app`.

> **First launch on Mac:** Right-click → Open to bypass Gatekeeper (unsigned app warning).

---

## Data & Privacy

- All data is stored locally in `microscope_usage.db` (SQLite)
- No data is sent over the internet
- Export to CSV at any time from the History tab

---

## File Structure

```
Microscope_use/
├── Microscope_use.py       # Main application
├── config.json             # Instrument & rate configuration
├── requirements.txt        # Python dependencies
└── microscope_usage.db     # Local database (auto-created on first run)
```

---

## License

MIT — free to use and modify for your facility.
