# Oracle Database Monitoring Application - CSV File Requirements

## Overview
This document lists all the CSV files that your Django application expects to find in the `output_csv/` directory. Each file has a specific format that the application code expects.

## Summary Report Page (/)
### Database Information Files:
1. **V_DB_NAME.csv** - Database name
2. **V_VERSION.csv** - Oracle version
3. **V_NODES.csv** - Number of nodes
4. **V_DB_status.csv** - Database status
5. **V_DB_ROLE.csv** - Database role (Primary/Standby)
6. **v_db_archival_status.csv** - Archival status
7. **v_total_active_sessions.csv** - Total active sessions
8. **V_PDB_SIZE_GB.csv** - PDB size in GB
9. **V_CDB_SIZE_GB.csv** - CDB size in GB
10. **V_LOCATION.csv** - Database location
11. **V_TIMEZONE.csv** - Database timezone
12. **V_LAST_REBOOT.csv** - Last reboot time
13. **V_SGA_MB.csv** - SGA size in MB
14. **V_PGA_MB.csv** - PGA size in MB
15. **v_last_gather_run.csv** - Last gather statistics run

### System Health Files:
16. **tablespace.csv** - Format: `tablespace_name used_mb free_mb`
17. **most_modified_table.csv** - Format: `table_name modification_count`
18. **cost_inv_managers.csv** - Format: `manager_name status1 status2 final_status`

## Health Check Page (/health/)
### Cache Hit Ratios:
19. **buff_cache_hit_ratio.csv** - Buffer cache hit ratio
20. **lib_hit_ratio.csv** - Library cache hit ratio

### Object Counts:
21. **invalid_object_count.csv** - Invalid objects count
22. **stale_table_count.csv** - Stale tables count
23. **unusable_indexes.csv** - Unusable indexes count

### Storage:
24. **asm_diskgroup_usage.csv** - ASM diskgroup usage

## Wait Event Summary Page (/wait_event_summary/)
25. **waiting_locks.csv** - Format: `wait_event_info per line`
26. **blocking_sessions.csv** - Format: `session_info sid serial# ... count` (minimum 8 columns)
27. **blocking.csv** - Format: Lines containing "SID X is blocking status Y blocking Z"
28. **sessions_locks.csv** - Format: Lines containing "SID X is blocking the sessions Y"

## Top 10 Checklists Page (/top-10/)
29. **top_10_io_consuming_queries.csv** - Format (alternating lines):
    - Line 1: `sql_id owner executions disk_reads buffer_gets read_per_exec gets_per_exec`
    - Line 2: `SQL_TEXT`
    
30. **dblinks.csv** - Format (every 3 lines):
    - Line 1: `owner db_link username`
    - Line 2: `host`
    - Line 3: `created hidden shared_interval valid intra_cdb`

## File Format Notes:

### Single Value Files:
Most of the V_*.csv files should contain just one line with one value, for example:
- V_DB_NAME.csv: `ORCL`
- V_VERSION.csv: `19.3.0.0.0`
- v_total_active_sessions.csv: `25`

### Space-Separated Files:
Files like tablespace.csv should have space-separated values:
```
SYSTEM 1024 512
USERS 2048 1024
TEMP 512 256
```

### Multi-line Structured Files:
Files like dblinks.csv have a specific 3-line pattern that repeats for each record.

### Pattern Matching Files:
Files like blocking.csv and sessions_locks.csv use regex pattern matching, so the exact text format matters.

## Important Notes:
1. All files must be in UTF-8 encoding
2. Empty files are handled gracefully by the application
3. If a file is missing, the application will still work but may show reduced functionality
4. The application automatically calculates health scores based on the data in these files
5. Numeric values should not contain commas except where specifically noted
6. Make sure blocking_sessions.csv has at least 8 columns per line to avoid IndexError

## Directory Structure:
```
report/
├── output_csv/
│   ├── V_DB_NAME.csv
│   ├── V_VERSION.csv
│   ├── ... (all other CSV files)
│   └── dblinks.csv
└── manage.py
```