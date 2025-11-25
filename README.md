# Oracle Database Monitoring Dashboard

A Django-based web application for monitoring and analyzing Oracle database health metrics.

## Features

- **Summary Report**: Overview of database information and status
- **Health Check**: Comprehensive database health monitoring
- **Wait Event Summary**: Analysis of database wait events and performance
- **Top 10 Analysis**: Top CPU/I/O consuming queries, fragmented tables, and database links

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd report
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database (optional - SQLite is used by default)**
   ```bash
   python app.py migrate
   ```

4. **Create a superuser (optional - for admin access)**
   ```bash
   python app.py createsuperuser
   ```

## Running the Application

Simply run:
```bash
python app.py
```

The server will start on `http://127.0.0.1:8007/`

### Alternative: Run on specific IP and port
```bash
python app.py runserver 0.0.0.0:8007
```

## Data Source

The application reads data from CSV files in the `output_csv/` directory. Make sure your CSV files are placed in this folder.

If data is missing, the application will display "NA" instead of errors.

## Project Structure

```
report/
├── app.py                 # Main entry point
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── output_csv/           # CSV data files
├── templates/            # HTML templates
│   ├── base.html
│   └── report/
├── oracle_db_project/    # Django project settings
└── views.py              # Application views
```

## Pages

- `/` - Summary Report
- `/health/` - Health Check
- `/wait_event_summary/` - Wait Event Summary
- `/top-10/` - Top 10 Analysis

## Notes

- The application uses SQLite database by default
- All data is read from CSV files in `output_csv/` folder
- Missing data will be displayed as "NA"
- For production deployment, update `SECRET_KEY` in `oracle_db_project/settings.py`

## License

[Your License Here]

