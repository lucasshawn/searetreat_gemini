import urllib.request
import urllib.parse
import json

pat = ""
with open('.env') as f:
    for line in f:
        if line.startswith('HOSPITABLE_PAT='):
            pat = line.strip().split('=', 1)[1].strip('"\'')

prop_id = "ae163eb2-66be-43b4-af71-2bfa6a2cf854"

params = urllib.parse.urlencode([
    ('properties[]', prop_id),
    ('start_date', '2026-06-01'),
    ('end_date', '2026-08-31'),
    ('date_query', 'checkout'),
    ('include', 'financials,guest,listings,notes')
])

url = f'https://public.api.hospitable.com/v2/reservations?{params}'
req = urllib.request.Request(url, headers={
    'Authorization': f'Bearer {pat}',
    'Accept': 'application/json',
    'User-Agent': 'Python/3.11'
})

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    for r in data.get('data', []):
        dep = (r.get('departure_date') or r.get('check_out'))[:10]
        if '2026-07-01' < dep <= '2026-08-01':
            code = r.get('code')
            platform = r.get('platform')
            notes = r.get('notes')
            guest_fees = r.get('financials', {}).get('host', {}).get('guest_fees', [])
            print(f"Code: {code} ({platform}) | Notes: {notes}")
            print(f"  Guest Fees: {json.dumps(guest_fees)}")
