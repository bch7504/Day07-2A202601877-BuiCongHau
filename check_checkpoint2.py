import csv
import re
from pathlib import Path

def main():
    D = Path('data/k4_ecommerce')
    REQ = ['doc_id', 'title', 'source_url', 'retrieved_at', 'document_version']
    mds = sorted(D.glob('*.md'))
    
    with open(D / 'sources.csv', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
        
    ids = []
    roles = {}
    KEY = 'customer_role'
    
    for p in mds:
        parts = p.read_text(encoding='utf-8').split('---')
        if len(parts) < 3:
            print(f"{p.name:40} THIEU FRONT MATTER")
            continue
            
        fm_text = parts[1]
        fm = dict(re.findall(r'^(\w+):\s*(.+)$', fm_text, re.M))
        
        for k, v in fm.items():
            fm[k] = v.split(' #', 1)[0].strip().strip('"').strip("'")
            
        doc_id = fm.get('doc_id')
        ids.append(doc_id)
        
        role = fm.get(KEY)
        roles[role] = roles.get(role, 0) + 1
        
        ok = all(k in fm for k in REQ) and KEY in fm and doc_id == p.stem
        
        status = "OK" if ok else "THIEU METADATA"
        print(f"{p.name:40} {status}")
        if not ok:
            missing = [k for k in REQ if k not in fm]
            if KEY not in fm:
                missing.append(KEY)
            if doc_id != p.stem:
                missing.append(f"doc_id_mismatch({doc_id} vs {p.stem})")
            print(f"  -> Thừa/Thiếu hoặc sai: {missing}")

    print('so file :', len(mds), '(can 5-10)')
    csv_ids = sorted(r['doc_id'] for r in rows)
    md_ids = sorted(ids)
    print('csv     :', 'khop' if csv_ids == md_ids else f'LECH (csv={csv_ids}, md={md_ids})')
    print(KEY, ':', roles)

if __name__ == "__main__":
    main()
