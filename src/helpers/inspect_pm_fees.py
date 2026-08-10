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
            guest = f"{r.get('guest', {}).get('first_name')} {r.get('guest', {}).get('last_name')}"
            host_fin = r.get('financials', {}).get('host', {})
            acc = host_fin.get('accommodation', {}).get('amount', 0) / 100.0
            discounts = sum([d.get('amount', 0) for d in host_fin.get('discounts', [])]) / 100.0
            adjustments = sum([a.get('amount', 0) for a in host_fin.get('adjustments', [])]) / 100.0
            guest_fees = host_fin.get('guest_fees', [])
            print(f"Code: {code} | Guest: {guest}")
            print(f"  Accommodation (Rent): ${acc:.2f}")
            print(f"  Discounts: ${discounts:.2f}")
            print(f"  Adjustments: ${adjustments:.2f}")
            print(f"  Accommodation + Discounts + Adjustments: ${acc + discounts + adjustments:.2f}")
            print(f"  Host Financials Host Obj: {json.dumps(host_fin, indent=4)}")
            print("-" * 80)
