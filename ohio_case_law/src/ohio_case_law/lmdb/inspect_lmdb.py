#!/usr/bin/env python3
"""
Script to inspect and show examples from all 5 LMDB databases
"""
import lmdb
import json
from pathlib import Path

LMDB_DIR = Path(__file__).parent.parent / "data" / "enriched_output" / "comprehensive_lmdb"

def inspect_database(db_name: str, num_examples: int = 3):
    """Show examples from a specific LMDB database"""
    db_path = LMDB_DIR / f"{db_name}.lmdb"

    if not db_path.exists():
        print(f"❌ {db_name}.lmdb not found at {db_path}")
        return

    print(f"\n{'='*80}")
    print(f"📊 {db_name.upper()}.LMDB")
    print(f"{'='*80}")

    try:
        env = lmdb.open(str(db_path), readonly=True, lock=False)
        with env.begin() as txn:
            cursor = txn.cursor()
            count = 0
            total = txn.stat()['entries']

            print(f"Total entries: {total:,}\n")

            for key, value in cursor:
                if count >= num_examples:
                    break

                key_str = key.decode('utf-8')
                try:
                    value_obj = json.loads(value.decode('utf-8'))
                    print(f"🔑 Key: {key_str}")
                    print(f"📄 Value:")
                    print(json.dumps(value_obj, indent=2)[:1000])  # Limit to 1000 chars
                    if len(json.dumps(value_obj)) > 1000:
                        print("... (truncated)")
                    print()
                except:
                    print(f"🔑 Key: {key_str}")
                    print(f"📄 Value: {value.decode('utf-8')[:500]}")
                    print()

                count += 1

        env.close()

    except Exception as e:
        print(f"❌ Error reading {db_name}: {e}")

def main():
    print("\n" + "="*80)
    print("🔍 OHIO CASE LAW - LMDB DATABASE INSPECTION")
    print("="*80)

    databases = ['sections', 'citations', 'reverse_citations', 'chains', 'metadata']

    for db_name in databases:
        inspect_database(db_name, num_examples=2)

    print("\n" + "="*80)
    print("✅ Inspection complete!")
    print("="*80)

if __name__ == "__main__":
    main()