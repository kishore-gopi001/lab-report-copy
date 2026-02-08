# scripts/seed_chroma.py

from database.db import get_connection
from app.vector.chroma_store import add_documents

BATCH_SIZE = 16  # safe even for small datasets


def seed():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT subject_id, test_name, value, unit, status, reason
        FROM lab_interpretations
    """)

    rows = cur.fetchall()

    texts = []
    metadatas = []
    batch_no = 1
    total = 0

    for r in rows:
        text = (
            f"Patient {r['subject_id']} has {r['test_name']} "
            f"value {r['value']} {r['unit']}. "
            f"Status is {r['status']}. "
            f"Reason: {r['reason']}."
        )

        texts.append(text)
        metadatas.append({
            "subject_id": r["subject_id"],
            "test": r["test_name"],
            "status": r["status"]
        })

        if len(texts) == BATCH_SIZE:
            add_documents(texts, metadatas)
            print(f"✅ Inserted batch {batch_no} ({len(texts)} docs)")
            total += len(texts)
            batch_no += 1
            texts, metadatas = [], []

    # Insert remaining docs
    if texts:
        add_documents(texts, metadatas)
        print(f"✅ Inserted final batch ({len(texts)} docs)")
        total += len(texts)

    conn.close()
    print(f"🎉 Chroma seeding completed. Total documents inserted: {total}")


if __name__ == "__main__":
    seed()
