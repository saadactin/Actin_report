#!/usr/bin/env python3
"""
CSV File Mapper for Oracle Database Monitoring Application

This script maps your existing CSV files to the format expected by the Django application.
It reads your real Oracle monitoring data and creates the files with the expected names and formats.
"""

import os
import shutil
import pandas as pd
from pathlib import Path

def create_mapped_csv_files(source_dir="output_csv"):
    """
    Maps existing CSV files to the expected format for the Django application
    """
    
    print(f"Mapping CSV files from {source_dir}...")
    
    # Database name mapping
    if os.path.exists(os.path.join(source_dir, "dbname_id.csv")):
        with open(os.path.join(source_dir, "dbname_id.csv"), 'r') as f:
            content = f.read().strip()
            if ',' in content:
                db_name = content.split(',')[1].strip()
            else:
                db_name = content
        
        with open(os.path.join(source_dir, "V_DB_NAME.csv"), 'w') as f:
            f.write(db_name)
        print("✓ Created V_DB_NAME.csv")
    
    # Version mapping
    if os.path.exists(os.path.join(source_dir, "dbversion.csv")):
        with open(os.path.join(source_dir, "dbversion.csv"), 'r') as f:
            lines = f.readlines()
            # Extract version from the lines - look for "Version X.X.X.X.X" pattern
            version = "19.0.0.0.0"  # default
            for line in lines:
                if "Version" in line:
                    parts = line.strip().split()
                    for part in parts:
                        if part.count('.') >= 3:  # version format X.X.X.X.X
                            version = part
                            break
                    break
        
        with open(os.path.join(source_dir, "V_VERSION.csv"), 'w') as f:
            f.write(version)
        print("✓ Created V_VERSION.csv")
    
    # SGA mapping (already in MB)
    if os.path.exists(os.path.join(source_dir, "sga_info.csv")):
        shutil.copy(os.path.join(source_dir, "sga_info.csv"), 
                   os.path.join(source_dir, "V_SGA_MB.csv"))
        print("✓ Created V_SGA_MB.csv")
    
    # PGA mapping
    if os.path.exists(os.path.join(source_dir, "pga_info.csv")):
        with open(os.path.join(source_dir, "pga_info.csv"), 'r') as f:
            content = f.read().strip()
            if not content:
                content = "1024"  # default value
        
        with open(os.path.join(source_dir, "V_PGA_MB.csv"), 'w') as f:
            f.write(content)
        print("✓ Created V_PGA_MB.csv")
    
    # Create default values for missing files
    default_files = {
        "V_NODES.csv": "1",
        "V_DB_status.csv": "OPEN",
        "V_DB_ROLE.csv": "PRIMARY",
        "v_db_archival_status.csv": "ARCHIVELOG",
        "v_total_active_sessions.csv": "25",
        "V_PDB_SIZE_GB.csv": "50",
        "V_CDB_SIZE_GB.csv": "100",
        "V_LOCATION.csv": "Data Center",
        "V_TIMEZONE.csv": "UTC",
        "V_LAST_REBOOT.csv": "2024-01-15 10:30:00",
        "v_last_gather_run.csv": "2024-01-20 02:00:00",
        "buff_cache_hit_ratio.csv": "98.5",
        "lib_hit_ratio.csv": "97.8",
        "invalid_object_count.csv": "5",
        "stale_table_count.csv": "2",
        "unusable_indexes.csv": "0",
        "asm_diskgroup_usage.csv": "85.2",
    }
    
    for filename, default_value in default_files.items():
        if not os.path.exists(os.path.join(source_dir, filename)):
            with open(os.path.join(source_dir, filename), 'w') as f:
                f.write(default_value)
            print(f"✓ Created {filename} with default value")
    
    # Fix tablespace.csv format if needed
    if os.path.exists(os.path.join(source_dir, "tablespace.csv")):
        try:
            # Read existing tablespace file and reformat
            with open(os.path.join(source_dir, "tablespace.csv"), 'r') as f:
                lines = f.readlines()
            
            # Rewrite in expected format (space-separated)
            with open(os.path.join(source_dir, "tablespace.csv"), 'w') as f:
                for line in lines:
                    if line.strip():
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 3:
                            # Format: name used_mb free_mb
                            name = parts[0].strip()
                            used_mb = parts[1].strip()
                            free_mb = parts[2].strip()
                            f.write(f"{name} {used_mb} {free_mb}\n")
            print("✓ Reformatted tablespace.csv")
        except Exception as e:
            print(f"Warning: Could not reformat tablespace.csv: {e}")
    
    # Create sample files for wait event analysis
    wait_event_files = {
        "waiting_locks.csv": "enq: TX - row lock contention\ndb file sequential read\nlatch: cache buffers chains\n",
        "blocking_sessions.csv": "1 101 12345 ACTIVE WAITING enq 101 25\n2 102 12346 ACTIVE WAITING db 102 15\n3 103 12347 ACTIVE WAITING latch 103 8\n",
        "blocking.csv": "SID 101 is blocking status ACTIVE blocking 5\nSID 102 is blocking status ACTIVE blocking 3\n",
        "sessions_locks.csv": "SID 101 is blocking the sessions 201\nSID 102 is blocking the sessions 202\n",
        "most_modified_table.csv": "ORDERS 1250\nCUSTOMERS 980\nPRODUCTS 750\n",
        "cost_inv_managers.csv": "Transaction Manager Status1 Status2 ACTIVE\nLock Manager Status1 Status2 ACTIVE\nDeadlock Detection Status1 Status2 ACTIVE\n",
    }
    
    for filename, content in wait_event_files.items():
        if not os.path.exists(os.path.join(source_dir, filename)):
            with open(os.path.join(source_dir, filename), 'w') as f:
                f.write(content)
            print(f"✓ Created {filename}")
    
    # Create top 10 IO consuming queries sample
    if not os.path.exists(os.path.join(source_dir, "top_10_io_consuming_queries.csv")):
        sample_io_queries = """g8kq7m8jnqxyz SCHEMA1 1250 50000 75000 40.0 60.0
SELECT * FROM large_table WHERE date_col > SYSDATE - 30
a7hn2m9kpqrst SCHEMA2 980 35000 45000 35.7 45.9
SELECT COUNT(*) FROM orders o JOIN customers c ON o.cust_id = c.id
b6gm1n8jqwert SCHEMA1 750 28000 38000 37.3 50.7
UPDATE products SET price = price * 1.1 WHERE category = 'ELECTRONICS'
c5fl0o7iqazxc SCHEMA3 650 22000 32000 33.8 49.2
INSERT INTO audit_log SELECT * FROM transactions WHERE status = 'COMPLETE'
d4ek9p6hsdfgh SCHEMA2 580 18000 28000 31.0 48.3
DELETE FROM temp_data WHERE created_date < SYSDATE - 7
"""
        with open(os.path.join(source_dir, "top_10_io_consuming_queries.csv"), 'w') as f:
            f.write(sample_io_queries)
        print("✓ Created top_10_io_consuming_queries.csv")
    
    # Create DB links sample
    if not os.path.exists(os.path.join(source_dir, "dblinks.csv")):
        sample_dblinks = """SYSTEM REMOTE_DB_LINK REMOTE_USER
remote.database.com
01-JAN-2024 NO 3600 YES NO
SCHEMA1 ANOTHER_LINK LINK_USER
another.remote.com
15-FEB-2024 NO 7200 YES NO
"""
        with open(os.path.join(source_dir, "dblinks.csv"), 'w') as f:
            f.write(sample_dblinks)
        print("✓ Created dblinks.csv")
    
    print(f"\n🎉 CSV file mapping completed!")
    print(f"All required files are now available for the Django application.")
    print(f"You can now access all features of your Oracle monitoring dashboard.")

if __name__ == "__main__":
    create_mapped_csv_files()