# Bjorn Bot Web Dashboard

A web interface for viewing and managing data from the Bjorn Discord bot.

## Setup

1. Make sure the virtual environment is activated:
```bash
cd /home/abstract/repos/bjorn
python -m venv venv
source venv/bin/activate
```

2. Install the required packages:
```bash
pip install flask pandas plotly
```

3. Make sure the data directory exists:
```bash
mkdir -p data
```

4. Initialize the database directories:
```bash
cd web
flask init-db-dirs
```

## Running the Application

Run the application with:
```bash
cd /home/abstract/repos/bjorn
source venv/bin/activate
cd web
python app.py
```

The web dashboard will be available at: http://localhost:5000

## Environment Variables

The application looks for these environment variables:
- `DATA_DIR`: Path to the directory containing database files (default: "data/")
- `LEAGUE_DB_NAME`: Name of the league database file without .sqlite extension (default: "league")
- `CONFIG_DB_NAME`: Name of the config database file without .sqlite extension (default: "config")

## Troubleshooting

If you encounter database connection errors:
1. Check that the database files exist in the data directory
2. Verify that the paths are correct
3. Ensure you have permission to read the database files
