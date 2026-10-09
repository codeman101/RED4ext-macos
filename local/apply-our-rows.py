#!/usr/bin/env python3
"""R30 (local-trial only): write the address database for the trial copy.

Input:  deps/red4ext.sdk/cyberpunk2077_addresses.json (jackmaxwil's database, unchanged) and local/our-rows.tsv.
Output: local/cyberpunk2077_addresses.json, the database the trial copy installs as red4ext-jm/bin/x64/cyberpunk2077_addresses.json.

Only the rows of our-rows.tsv change: each gets our Mac offset and "verified": true, and a "local_evidence" note with our check-rows verdict.
They are exactly the rows that jackmaxwil's database lists as unverified, that our plugins compile in, and that our check-rows evidence rates
STRONG, OK or REVIEWED (tools/addr-match/check-rows.py, 2026-10-09). No other row changes; there is no allow-all.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'deps', 'red4ext.sdk', 'cyberpunk2077_addresses.json')
OUT = os.path.join(HERE, 'cyberpunk2077_addresses.json')
db = json.load(open(SRC))
idx = {e['hash']: e for e in db['Addresses']}
changed = 0
for line in open(os.path.join(HERE, 'our-rows.tsv')):
    if line.startswith('#') or not line.strip():
        continue
    h, name, ours, verdict, before = line.rstrip('\n').split('\t')[:5]
    e = idx.get(h)
    if e is None:
        sys.exit('hash %s (%s) is not in the database' % (h, name))
    if e.get('verified'):
        sys.exit('hash %s (%s) is already verified in the database; this script only marks unverified rows' % (h, name))
    if e.get('offset') != before:
        sys.exit('hash %s (%s): the database offset changed since the evidence list was made (%s, list says %s)' % (h, name, e.get('offset'), before))
    e['offset'] = ours
    e['verified'] = True
    e['local_evidence'] = 'cp2077-mac check-rows %s (local edit for the R30 trial; was %s, unverified)' % (verdict, before)
    changed += 1
json.dump(db, open(OUT, 'w'), indent=2)
print('wrote %s: %d rows marked verified with our offsets' % (OUT, changed))
