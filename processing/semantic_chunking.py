import pandas as pd
from database.db import get_connection
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())
try:
    from app.vector.chroma_store import add_documents
except ImportError:
    print("Warning: Could not import add_documents from app.vector.chroma_store")

# Paths
DB_PATH = "database/lab_results.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_patient_chunks(subject_id, gender, patient_df, window_size=30):
    """
    Creates multiple semantic chunks for a patient if history is long.
    This ensures the LLM has manageable context while preserving temporal data.
    """
    # Sort by time: most recent first
    patient_df = patient_df.sort_values(by=['processed_time'], ascending=[False])
    
    chunks = []
    total_records = len(patient_df)
    
    # Process in windows
    for i in range(0, total_records, window_size):
        window_df = patient_df.iloc[i : i + window_size]
        is_latest = (i == 0)
        
        lines = [f"Clinical Report for Patient {subject_id} ({gender}) - Part {i//window_size + 1}:"]
        
        if is_latest:
            critical_count = len(patient_df[patient_df['status'] == 'CRITICAL'])
            abnormal_count = len(patient_df[patient_df['status'] == 'ABNORMAL'])
            lines.append(f"Patient Overview: {total_records} total records. {critical_count} CRITICAL, {abnormal_count} ABNORMAL.")
        
        lines.append("-" * 40)
        lines.append(f"Records {i+1} to {min(i+window_size, total_records)} (Most Recent First):")
        
        for _, row in window_df.iterrows():
            timestamp = row.get('processed_time', 'N/A')
            test = row.get('test_name', 'Unknown Test')
            val = row.get('value', '?')
            unit = row.get('unit', '')
            status = row.get('status', 'UNKNOWN')
            reason = row.get('reason', '')
            
            line = f"[{timestamp}] Test: {test} | Value: {val} {unit} | Status: {status}"
            if reason and reason.lower() != 'none':
                line += f" | NOTE: {reason}"
            lines.append(line)
        
        text = "\n".join(lines)
        chunks.append({
            "text": text,
            "metadata": {
                "subject_id": str(subject_id),
                "type": "patient_history_window",
                "is_latest": is_latest,
                "window_index": i//window_size,
                "range": f"{i+1}-{min(i+window_size, total_records)}"
            }
        })
    
    return chunks

def run_chunking():
    print("Starting Optimized Semantic Chunking...")
    
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return []

    conn = get_connection()
    
    try:
        print("Fetching data from lab_interpretations...")
        df = pd.read_sql_query("SELECT * FROM lab_interpretations", conn)
        
        all_chunks = []
        
        # Group by subject_id to create context-rich summaries
        print("Grouping labs by patient and generating semantic chunks...")
        for subject_id, group in df.groupby('subject_id'):
            gender = group.iloc[0]['gender']
            patient_chunks = create_patient_chunks(subject_id, gender, group)
            all_chunks.extend(patient_chunks)
            
        print(f"Created {len(all_chunks)} total semantic chunks (optimized from {len(df)}).")
        return all_chunks
        
    except Exception as e:
        print(f"Error during chunking: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        conn.close()

def populate_chroma(chunks):
    if not chunks:
        return
    print(f"Populating ChromaDB with {len(chunks)} chunks...")
    texts = [c['text'] for c in chunks]
    metadatas = [c['metadata'] for c in chunks]
    
    # Process in batches
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_metadatas = metadatas[i:i + batch_size]
        add_documents(batch_texts, batch_metadatas)
        print(f"  Added batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")

if __name__ == "__main__":
    chunks = run_chunking()
    if chunks:
        populate_chroma(chunks)
        print("Finalized ChromaDB population.")
