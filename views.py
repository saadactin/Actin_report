import os
import csv
import json
import html
import random
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import pandas as pd
from django.shortcuts import render
from django.conf import settings

CSV_DIR = os.path.join(settings.BASE_DIR, "output_csv")

# Global variable for score
v_score = 0

# --- Utility functions ---
def clean_and_read_value(filepath):
    try:
        if not os.path.exists(filepath):
            return "NA"
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                cell = row[0].strip()
                if cell and cell.lower() not in {"name", "column_name", "value", ""}:
                    return cell
        return "NA"
    except Exception as e:
        return "NA"

def extract_ratio_value(filepath):
    try:
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
            for line in lines:
                if not line.lower().startswith(("name", "column")):
                    try:
                        return float(line)
                    except ValueError:
                        continue
        return None
    except:
        return None

# --- Views ---

def summary_report(request):
    v_score = 0
    summary_map = {
        "Db Name": "V_DB_NAME.csv",
        "Version": "V_VERSION.csv",
        "Nodes": "V_NODES.csv",
        "Db Status": "V_DB_status.csv",
        "Db Role": "V_DB_ROLE.csv",
        "Db Archival Status": "v_db_archival_status.csv",
        "Total Active Sessions": "v_total_active_sessions.csv",
        "Pdb Size Gb": "V_PDB_SIZE_GB.csv",
        "Cdb Size Gb": "V_CDB_SIZE_GB.csv",
        "Location": "V_LOCATION.csv",
        "Timezone": "V_TIMEZONE.csv",
        "Last Reboot": "V_LAST_REBOOT.csv",
        "Sga Mb": "V_SGA_MB.csv",
        "Pga Mb": "V_PGA_MB.csv",
        "Last Gather Run": "v_last_gather_run.csv"
    }
    summary_data = []
    for label, filename in summary_map.items():
        filepath = os.path.join(CSV_DIR, filename)
        value = clean_and_read_value(filepath)
        summary_data.append({'label': label, 'value': value})
        v_score += 1
    request.session['summary_score'] = v_score
    total_score = v_score
    for key in ['health_score', 'wait_score', 'checklist_score']:
        total_score += request.session.get(key, 0)
    # If all scores are zero (i.e., views not called), set display_score to 0
    if (
        v_score == 0 and
        all(request.session.get(key, 0) == 0 for key in ['health_score', 'wait_score', 'checklist_score'])
    ):
        display_score = 0
    elif total_score < 1000:
        display_score = round((total_score / 1000) * 100, 2)
    else:
        display_score = round((total_score / 10000) * 100, 2)
    score_emoji = "\U0001F44E" if display_score < 50 else "\U0001F44D"
    return render(request, "report/summary_report.html", {
        "summary_data": summary_data,
        "generated_on": datetime.now(),
        "v_score": display_score,
        "score_emoji": score_emoji
    })

def health_check(request):
    v_score = 0
    # Use a local score variable
    
    # Cache ratios
    cache_ratios = {
        "Buffer Cache Hit Ratio": "buff_cache_hit_ratio.csv",
        "Library Cache Hit Ratio": "lib_hit_ratio.csv"
    }
    db_object_check = {
        "Invalid Objects": "invalid_object_count.csv",
        "Stale Tables": "stale_table_count.csv"
    }
    db_usable_indexes_check = {
        "Unusable Indexes": "unusable_indexes.csv"
    }
    asm_disk_group_check = {
        "ASM Disk Groups": "asm_diskgroup_usage.csv"
    }
    pass_items = []
    warn_items = []

    for label, filename in cache_ratios.items():
        filepath = os.path.join(CSV_DIR, filename)
        value = extract_ratio_value(filepath)
        if value is None:
            warn_items.append((label, "Invalid or missing"))
        elif value < 90:
            warn_items.append((label, f"{value:.2f}%"))
        else:
            pass_items.append((label, f"{value:.2f}%"))
            v_score += 5

    for label, filename in db_object_check.items():
        filepath = os.path.join(CSV_DIR, filename)
        value = clean_and_read_value(filepath)
        if value is None:
            warn_items.append((label, "Invalid or missing"))
        elif int(value) > 1000:
            warn_items.append((label, value))
        else:
            pass_items.append((label, value))
            v_score += 5

    for label, filename in db_usable_indexes_check.items():
        filepath = os.path.join(CSV_DIR, filename)
        value = clean_and_read_value(filepath)
        if value is None:
            warn_items.append((label, "Invalid or missing"))
        elif int(value) > 0:
            warn_items.append((label, value))
        else:
            pass_items.append((label, value))
            v_score += 5

    # ASM Disk Group
    for label, filename in asm_disk_group_check.items():
        filepath = os.path.join(CSV_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        group = parts[0].strip()
                        try:
                            usage = float(parts[1].strip())
                            display_label = f"{label} - {group}"
                            if usage > 90:
                                warn_items.append((display_label, f"{usage:.2f}%"))
                            else:
                                pass_items.append((display_label, f"{usage:.2f}%"))
                                v_score += 6
                        except ValueError:
                            warn_items.append((f"{label} - {group}", "Invalid number"))
                    else:
                        warn_items.append((f"{label} - {line}", "Missing value"))
        except Exception as e:
            warn_items.append((label, f"Error: {e}"))

    # Most Modified Table
    most_modified_table_path = os.path.join(CSV_DIR, "most_modified_table.csv")
    try:
        with open(most_modified_table_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 6:
                    owner = parts[0].strip()
                    table = parts[1].strip()
                    full_table = f"{owner}.{table}"
                    try:
                        insert = int(float(parts[2].strip()))
                        update = int(float(parts[3].strip()))
                        delete = int(float(parts[4].strip()))
                        total = int(float(parts[5].strip()))
                        summary = (
                            f"Most Modified Table: {full_table} "
                            f"(Insert: {insert:,} , Update: {update:,} , Delete: {delete:,} , Total: {total:,})"
                        )
                        warn_items.append(("Modification Alert", summary))
                    except ValueError:
                        warn_items.append(("Modification Alert", f"Invalid number format for {full_table}"))
                else:
                    warn_items.append(("Modification Alert", "Invalid row format in most_modified_table.csv"))
    except Exception as e:
        warn_items.append(("Modification Alert", f"Error reading most_modified_table.csv: {e}"))

    # Transaction Manager Status Check
    transaction_manager_file = os.path.join(CSV_DIR, "cost_inv_managers.csv")
    try:
        with open(transaction_manager_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                label = " ".join(parts[:-2]) if len(parts) > 2 else parts[0]
                status = parts[-1].strip().lower()
                display_label = label.strip()
                if status == "inactive":
                    warn_items.append((display_label, "Inactive"))
                elif status == "active":
                    pass_items.append((display_label, "Active"))
                    v_score += 1
                else:
                    warn_items.append((display_label, f"Unknown status: {status}"))
    except Exception as e:
        warn_items.append(("Transaction Manager Status", f"Error: {e}"))

    # Tablespace chart data
    tablespaces = []
    freemb = []
    point_colors = []
    DATA_FILE = os.path.join(CSV_DIR, "tablespace.csv")
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    try:
                        name = parts[0]
                        free_str = parts[2].replace(',', '')
                        free = float(free_str)
                        tablespaces.append(name)
                        freemb.append(free)
                    except (ValueError, IndexError):
                        continue
    except Exception:
        pass
    combined = list(zip(tablespaces, freemb))
    combined.sort(key=lambda x: x[1], reverse=True)
    threshold = 10000
    tablespaces_sorted = []
    freemb_sorted = []
    for name, free in combined:
        tablespaces_sorted.append(name)
        freemb_sorted.append(free)
        if free <=10:
            v_score += 2
        elif free <= 30:
            v_score += 5
        elif free >= 90:
            v_score += 10   
        else:
            v_score += 20
        color = 'rgba(255, 99, 132, 1)'  if free < threshold else 'rgba(74, 144, 226, 1)'
        point_colors.append(color)

    # Archival Generation chart data
    daily_data = {}
    CSV_file = os.path.join(CSV_DIR, "archivals_for_last_2days_per_hour.csv")
    try:
        if os.path.exists(CSV_file):
            with open(CSV_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if not parts or not parts[0].startswith('2025'):
                        continue
                    date = parts[0]
                    try:
                        hourly_values = list(map(int, parts[1:25]))
                        daily_data[date] = hourly_values
                    except (ValueError, IndexError):
                        continue
    except Exception:
        pass
    archival_score = 0
    for date, values in daily_data.items():
        if len(values) < 24:
            continue
        total = sum(values)
        if total < 100:
            archival_score += 20
        elif total < 300:
            archival_score += 10
        elif total < 1000:
            archival_score += 15
        else:
            archival_score += 5
    v_score += archival_score


    request.session['health_score'] = v_score
    total_score = v_score
    for key in ['summary_score', 'wait_score', 'checklist_score']:
        total_score += request.session.get(key, 0)
    if total_score < 1000:
        display_score = round((total_score / 1000) * 100, 2)
    else:
        display_score = round((total_score / 10000) * 100, 2)
    score_emoji = "\U0001F44E" if display_score < 50 else "\U0001F44D"
    return render(request, "report/health_check.html", {
        "pass_items": pass_items,
        "warn_items": warn_items,
        "tablespaces": json.dumps(tablespaces_sorted),
        "freemb": json.dumps(freemb_sorted),
        "point_colors": json.dumps(point_colors),
        "threshold": threshold,
        "daily_data": json.dumps(daily_data),
        "generated_on": datetime.now(),
        "v_score": display_score,
        "score_emoji": score_emoji
    })

def wait_event_summary(request):
    v_score = 0
    CSV_DIR = os.path.join(settings.BASE_DIR, "output_csv")
    session_wait_file = os.path.join(CSV_DIR, "wait_events.csv")
    waiting_locks_file = os.path.join(CSV_DIR, "waiting_blocking_locks.csv")
    blocking_sessions_file = os.path.join(CSV_DIR, "blocking_sessions.csv")
    blocking_file = os.path.join(CSV_DIR, "blocking_sessions.csv")
    
    # Initialize all variables
    wait_event_counter = Counter()
    wait_event_trend = defaultdict(int)
    generate_wait_trend = False
    blocking_counter = Counter()
    blocking_labels = []
    blocking_counts = []
    generate_blocking_graph = False
    blkedges = set()
    
    # Initialize wait event detail variables
    wait_event_labels = []
    wait_event_counts = []
    wait_event_times = []
    wait_event_avg_times = []
    wait_event_percentages = []

    # Wait event summary (top 10) - Enhanced to extract detailed information
    wait_event_details = {}  # Store detailed info: {event_name: {count, total_time, avg_time}}
    try:
        if os.path.exists(session_wait_file):
            with open(session_wait_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    # Simple format: one event per line
                    wait_event = line
                    wait_event_counter[wait_event] += 1
                    # Initialize detailed info if not exists
                    if wait_event not in wait_event_details:
                        wait_event_details[wait_event] = {
                            'count': 0,
                            'total_time': 0,
                            'avg_time': 0
                        }
                    wait_event_details[wait_event]['count'] += 1
        
        # Try to get more detailed info from blocking_sessions.csv
        if os.path.exists(blocking_sessions_file):
            try:
                with open(blocking_sessions_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        parts = line.split()
                        if len(parts) >= 7:
                            try:
                                # Format: session_id sid serial# status wait_type sid count
                                wait_type = parts[4] if len(parts) > 4 else ""
                                count = int(parts[6]) if len(parts) > 6 else 1
                                # Map wait type to full event name
                                wait_event_map = {
                                    'enq': 'enq: TX - row lock contention',
                                    'db': 'db file sequential read',
                                    'latch': 'latch: cache buffers chains',
                                    'buffer': 'buffer busy waits',
                                    'log': 'log file sync'
                                }
                                # Try to find matching event
                                event_name = None
                                for key, value in wait_event_map.items():
                                    if wait_type.lower().startswith(key):
                                        event_name = value
                                        break
                                
                                if not event_name:
                                    # Try to match from existing events
                                    for event in wait_event_counter.keys():
                                        if wait_type.lower() in event.lower() or event.lower().startswith(wait_type.lower()):
                                            event_name = event
                                            break
                                
                                if event_name and event_name in wait_event_details:
                                    # Estimate time based on count (assuming 1ms per wait)
                                    estimated_time = count * 1.0
                                    wait_event_details[event_name]['total_time'] += estimated_time
                                    wait_event_details[event_name]['count'] = max(
                                        wait_event_details[event_name]['count'],
                                        count
                                    )
                            except (ValueError, IndexError):
                                continue
            except Exception:
                pass
        
        # Calculate averages and prepare data
        for event_name, details in wait_event_details.items():
            if details['count'] > 0:
                details['avg_time'] = details['total_time'] / details['count']
        
        # Get top 10 by count
        most_common_waits = wait_event_counter.most_common(10)
        wait_event_labels = []
        wait_event_counts = []
        wait_event_times = []
        wait_event_avg_times = []
        wait_event_percentages = []
        
        total_wait_time = sum(details['total_time'] for details in wait_event_details.values())
        
        for event, count in most_common_waits:
            wait_event_labels.append(event)
            wait_event_counts.append(count)
            
            if event in wait_event_details:
                details = wait_event_details[event]
                wait_event_times.append(round(details['total_time'], 2))
                wait_event_avg_times.append(round(details['avg_time'], 2))
                if total_wait_time > 0:
                    percentage = round((details['total_time'] / total_wait_time) * 100, 2)
                else:
                    percentage = 0
                wait_event_percentages.append(percentage)
            else:
                # Default values if no detailed info
                wait_event_times.append(0)
                wait_event_avg_times.append(0)
                wait_event_percentages.append(0)
                
    except Exception as e:
        wait_event_labels = []
        wait_event_counts = []
        wait_event_times = []
        wait_event_avg_times = []
        wait_event_percentages = []

    # Wait event trend (simulate as in trail.py)
    trend_labels = []
    trend_counts = []
    if os.path.exists(waiting_locks_file):
        with open(waiting_locks_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                generate_wait_trend = True
                now = datetime.now()
                for _ in range(100):
                    event_time = now - timedelta(minutes=random.randint(0, 9))
                    bucket = event_time.strftime("%H:%M")
                    wait_event_trend[bucket] += 1
                trend_labels = sorted(wait_event_trend.keys())
                trend_counts = [wait_event_trend[t] for t in trend_labels]
    else:
        v_score += 5
    if os.path.exists(blocking_sessions_file):
        with open(blocking_sessions_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                generate_blocking_graph = True
                for line in content.splitlines():
                    parts = line.split()
                    if len(parts) >= 4:
                        sid = parts[1]
                        count = int(parts[7])
                        blocking_counter[sid] += count
                most_common_blocking = blocking_counter.most_common(10)
                blocking_labels = [sid for sid, _ in most_common_blocking]
                blocking_counts = [count for _, count in most_common_blocking]
    else:
        v_score += 5
    if os.path.exists(blocking_file):
        with open(blocking_file, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.search(r"SID (\d+) is blocking status \w+ blocking (\d+)", line.strip())
                if match:
                    blocker_sid = match.group(1)
                    blocked_session = match.group(2)
                    blkedges.add((blocker_sid, blocked_session))
    else:
        v_score += 5
    blkedges = list(blkedges)
    blknodes = list(set([n for pair in blkedges for n in pair]))

    vis_blknodes = [{"id": int(n), "label": f"SID {n}"} for n in blknodes] if blkedges else []
    vis_blkedges = [{"from": int(f), "to": int(t)} for f, t in blkedges] if blkedges else []
   
    # Locking Sessions Graph (sessions_locks.csv)
    locking_file = os.path.join(CSV_DIR, "sessions_locks.csv")
    edges = []
    if os.path.exists(locking_file):
        with open(locking_file, 'r', encoding='utf-8') as f:
            for line in f:
                match = re.search(r"SID (\d+) is blocking the sessions (\d+)", line.strip())
                if match:
                    blocker = match.group(1)
                    blocked = match.group(2)
                    edges.append((blocker, blocked))
    else:
        v_score += 5
    nodes = list(set([n for pair in edges for n in pair]))
    vis_nodes = [{"id": int(n), "label": f"SID {n}"} for n in nodes] if edges else []
    vis_edges = [{"from": int(f), "to": int(t)} for f, t in edges] if edges else []

    request.session['wait_score'] = v_score
    total_score = v_score
    for key in ['summary_score', 'health_score', 'checklist_score']:
        total_score += request.session.get(key, 0)
    if total_score < 1000:
        display_score = round((total_score / 1000) * 100, 2)
    else:
        display_score = round((total_score / 10000) * 100, 2)
    score_emoji = "\U0001F44E" if display_score < 50 else "\U0001F44D"
    return render(request, "report/wait_event_summary.html", {
        "wait_event_labels": json.dumps(wait_event_labels),
        "wait_event_counts": json.dumps(wait_event_counts),
        "wait_event_times": json.dumps(wait_event_times),
        "wait_event_avg_times": json.dumps(wait_event_avg_times),
        "wait_event_percentages": json.dumps(wait_event_percentages),
        "trend_labels": json.dumps(trend_labels),
        "trend_counts": json.dumps(trend_counts),
        "generate_wait_trend": generate_wait_trend,
        "blocking_labels": json.dumps(blocking_labels),
        "blocking_counts": json.dumps(blocking_counts),
        "generate_blocking_graph": generate_blocking_graph,
        "vis_blknodes": json.dumps(vis_blknodes),
        "vis_blkedges": json.dumps(vis_blkedges),
        "has_blocking_graph": bool(blkedges),
        "vis_locknodes": json.dumps(vis_nodes),
        "vis_lockedges": json.dumps(vis_edges),
        "has_locking_graph": bool(edges),
        "generated_on": datetime.now(),
        "v_score": display_score,
        "score_emoji": score_emoji
    })

def top_10_checklists(request):
    # Use a local score variable
    v_score = 0
    v_frag_pct = 0
    v_total_frag_score = 0
    v_total_cpu_time = 0
    v_total_disk_reads = 0
    # Fragmented tables - exactly as in trail.py
    # Read and parse the CSV into a list of dicts to avoid TypeError
    frag_file = os.path.join(CSV_DIR, 'top_10_fragmented_tables.csv')
    fragmented_tables = []
    try:
        if os.path.exists(frag_file):
            with open(frag_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 6:
                        try:
                            rec = {
                                'OWNER': parts[0],
                                'TABLE_NAME': parts[1],
                                'BLOCKS': int(float(parts[2])),
                                'NUM_OF_ROWS': int(float(parts[3])),
                                'AVG_ROW_LEN': float(parts[4]),
                                'APPROX_UNUSED_MB': float(parts[5])
                            }
                            fragmented_tables.append(rec)
                        except (ValueError, IndexError):
                            continue
    except Exception:
        pass
    # Sort by APPROX_UNUSED_MB descending
    fragmented_tables.sort(key=lambda x: x['APPROX_UNUSED_MB'], reverse=True)
    table_names = [rec['TABLE_NAME'] for rec in fragmented_tables]
    unused_space = [rec['APPROX_UNUSED_MB'] for rec in fragmented_tables]
    owners = [rec['OWNER'] for rec in fragmented_tables]
    num_rows = [rec['NUM_OF_ROWS'] for rec in fragmented_tables]
    for rec in fragmented_tables:
        rec['BLOCKS'] = int(rec['BLOCKS'])
        rec['APPROX_UNUSED_MB'] = float(rec['APPROX_UNUSED_MB'])
        if rec['BLOCKS'] > 0:
            v_frag_pct = ((rec['APPROX_UNUSED_MB']*1024*1024) / (rec['BLOCKS'] * 8192))*100
            if v_frag_pct < 10:
                v_total_frag_score = v_total_frag_score + 1.5
            elif v_frag_pct < 30:
                v_total_frag_score = v_total_frag_score + 1.0
            else:
                v_total_frag_score = v_total_frag_score + 0.5
    
    if v_total_frag_score > 15:
        v_score += 15



    # Top 10 CPU consuming queries - exactly as in trail.py
    records = []
    cpu_file = os.path.join(CSV_DIR, "top_10_cpu_consuming_queries.csv")
    try:
        if os.path.exists(cpu_file):
            with open(cpu_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            for line in lines:
                if not line or line.startswith('#'):
                    continue
                
                # Check if sql_text is in the same line
                if "sql_text," in line:
                    # Format: SQL_ID OWNER CPU_TIME sql_text,SQL_TEXT
                    sql_text_start = line.find("sql_text,")
                    meta_part = line[:sql_text_start].strip()
                    sql_line = line[sql_text_start + 9:].strip()
                    parts = meta_part.split()
                else:
                    # Format: SQL_ID OWNER CPU_TIME (no SQL text)
                    parts = line.split()
                    sql_line = ""

                if len(parts) < 3:
                    continue

                try:
                    sql_id = parts[0]
                    owner = parts[1]
                    cpu_time = float(parts[2])
                    elapsed_time = float(parts[3]) if len(parts) > 3 else cpu_time
                    rows_processed = int(float(parts[4])) if len(parts) > 4 else 0
                    
                    records.append({
                        "SQL_ID": sql_id,
                        "OWNER": owner,
                        "CPU_TIME": cpu_time,
                        "ELAPSED_TIME": elapsed_time,
                        "ROWS_PROCESSED": rows_processed,
                        "SQL_TEXT": sql_line if sql_line else "NA"
                    })
                except (ValueError, IndexError):
                    continue
    except Exception:
        pass

    # Create DataFrame and handle empty case
    if records:
        df = pd.DataFrame(records)
        if not df.empty and "CPU_TIME" in df.columns:
            df_sorted = df.sort_values(by="CPU_TIME", ascending=False)
            sql_id = df_sorted["SQL_ID"].tolist()
            cpu_times = df_sorted["CPU_TIME"].tolist()
            owners_cpu = df_sorted["OWNER"].tolist()
            elapsed_times = df_sorted["ELAPSED_TIME"].tolist()
            rows = df_sorted["ROWS_PROCESSED"].tolist()
            sql_texts = df_sorted["SQL_TEXT"].tolist()

            for rec in df_sorted.to_dict('records'):
                v_total_cpu_time += rec.get('CPU_TIME', 0) + rec.get('ELAPSED_TIME', 0)
        else:
            sql_id = []
            cpu_times = []
            owners_cpu = []
            elapsed_times = []
            rows = []
            sql_texts = []
    else:
        sql_id = []
        cpu_times = []
        owners_cpu = []
        elapsed_times = []
        rows = []
        sql_texts = []
    if v_total_cpu_time < 100:
        v_score += 20
    elif v_total_cpu_time < 1000:
        v_score += 10
    elif v_total_cpu_time < 10000:
        v_score += 15
    else:
        v_score += 5

    # Top 10 IO consuming queries - exactly as in trail.py
    CSV_FILE = "top_10_io_consuming_queries.csv"
    CSV_PATH = os.path.join(CSV_DIR, CSV_FILE)

    records_io = []
    try:
        if os.path.exists(CSV_PATH):
            with open(CSV_PATH, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            for line in lines:
                if not line or line.startswith('#'):
                    continue
                
                # Check if sql_text is in the same line
                if "sql_text," in line:
                    # Format: SQL_ID OWNER EXECUTIONS DISK_READS ... sql_text,SQL_TEXT
                    sql_text_start = line.find("sql_text,")
                    meta_part = line[:sql_text_start].strip()
                    sql_line = line[sql_text_start + 9:].strip()
                    parts = meta_part.split()
                else:
                    # Format: SQL_ID OWNER EXECUTIONS DISK_READS ... (no SQL text)
                    parts = line.split()
                    sql_line = ""

                if len(parts) < 3:
                    continue

                try:
                    sql_id_io = parts[0]
                    owner_io = parts[1]
                    executions = float(parts[2]) if len(parts) > 2 else 0
                    disk_reads = float(parts[3]) if len(parts) > 3 else 0
                    buffer_gets = float(parts[4]) if len(parts) > 4 else 0
                    read_per_exec = float(parts[5]) if len(parts) > 5 else 0
                    gets_per_exec = float(parts[6]) if len(parts) > 6 else 0
                    
                    sql_text = sql_line.strip() if sql_line else "NA"

                    records_io.append({
                        "SQL_ID": sql_id_io,
                        "OWNER": owner_io,
                        "EXECUTIONS": executions,
                        "DISK_READS": disk_reads,
                        "BUFFER_GETS": buffer_gets,
                        "READ_PER_EXEC": read_per_exec,
                        "GETS_PER_EXEC": gets_per_exec,
                        "SQL_TEXT": sql_text
                    })
                except (ValueError, IndexError):
                    continue
    except Exception:
        pass

    # Create DataFrame and handle empty case
    if records_io:
        df_io = pd.DataFrame(records_io)
        if not df_io.empty and "DISK_READS" in df_io.columns:
            df_io_sorted = df_io.sort_values(by="DISK_READS", ascending=False).head(10)
            sql_id_io = df_io_sorted["SQL_ID"].tolist()
            owners_io = df_io_sorted["OWNER"].tolist()
            executions = df_io_sorted["EXECUTIONS"].tolist()
            disk_reads = df_io_sorted["DISK_READS"].tolist()
            buffer_gets = df_io_sorted["BUFFER_GETS"].tolist()
            read_per_exec = df_io_sorted["READ_PER_EXEC"].tolist()
            gets_per_exec = df_io_sorted["GETS_PER_EXEC"].tolist()
            sql_texts_io = df_io_sorted["SQL_TEXT"].tolist()

            for rec in df_io_sorted.to_dict('records'):
                v_total_disk_reads += rec.get('DISK_READS', 0) + rec.get('BUFFER_GETS', 0)
        else:
            sql_id_io = []
            owners_io = []
            executions = []
            disk_reads = []
            buffer_gets = []
            read_per_exec = []
            gets_per_exec = []
            sql_texts_io = []
    else:
        sql_id_io = []
        owners_io = []
        executions = []
        disk_reads = []
        buffer_gets = []
        read_per_exec = []
        gets_per_exec = []
        sql_texts_io = []
    if v_total_disk_reads < 100000:
        v_score += 20
    elif v_total_disk_reads < 1000000:
        v_score += 15
    elif v_total_disk_reads < 10000000:
        v_score += 10
    else:
        v_score += 5

    # DB Links - exactly as in trail.py
    cleaned_data = []
    dblinks_file = os.path.join(CSV_DIR, "dblinks.csv")
    try:
        if os.path.exists(dblinks_file):
            with open(dblinks_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]

            for i in range(0, len(lines), 3):
                try:
                    if i + 2 >= len(lines):
                        break

                    part1 = lines[i].split()
                    if len(part1) < 3:
                        continue
                    owner, db_link, username = part1[0], part1[1], part1[2]

                    host = lines[i + 1].strip() if i + 1 < len(lines) else "NA"

                    part3 = lines[i + 2].split() if i + 2 < len(lines) else []
                    if len(part3) < 5:
                        continue

                    created, hidden, shared_interval, valid, intra_cdb = part3[0], part3[1], part3[2], part3[3], part3[4]

                    cleaned_data.append({
                        "owner": owner,
                        "dblink": db_link,
                        "username": username,
                        "host": host,
                        "created": created,
                        "hidden": hidden,
                        "shared_interval": shared_interval,
                        "valid": valid,
                        "intra_cdb": intra_cdb
                    })
                    v_score += 1
                except Exception:
                    continue
    except Exception:
        pass

    request.session['checklist_score'] = v_score
    total_score = v_score
    for key in ['summary_score', 'health_score', 'wait_score']:
        total_score += request.session.get(key, 0)
    if total_score < 1000:
        display_score = round((total_score / 1000) * 100, 2)
    else:
        display_score = round((total_score / 10000) * 100, 2)
    score_emoji = "\U0001F44E" if display_score < 50 else "\U0001F44D"
    # Prepare CPU data for template
    cpu_queries = []
    if records:
        df = pd.DataFrame(records)
        df_sorted = df.sort_values(by="CPU_TIME", ascending=False).head(10)
        cpu_queries = df_sorted.to_dict('records')
    
    # Prepare IO data for template
    io_queries = []
    if records_io:
        df_io = pd.DataFrame(records_io)
        df_io_sorted = df_io.sort_values(by="DISK_READS", ascending=False).head(10)
        io_queries = df_io_sorted.to_dict('records')
    
    return render(request, "report/top_10_checklists.html", {
        "table_names": json.dumps(table_names if fragmented_tables else []),
        "unused_space": json.dumps(unused_space if fragmented_tables else []),
        "owners": json.dumps(owners if fragmented_tables else []),
        "num_rows": json.dumps(num_rows if fragmented_tables else []),
        "cpu_queries": cpu_queries,  # Pass as Python list for template iteration
        "cpu_queries_json": json.dumps(cpu_queries),  # JSON for JavaScript
        "io_queries": io_queries,  # Pass as Python list for template iteration
        "io_queries_json": json.dumps(io_queries),  # JSON for JavaScript
        "dblinks": cleaned_data,
        "generated_on": datetime.now(),
        "v_score": display_score,
        "score_emoji": score_emoji
    })