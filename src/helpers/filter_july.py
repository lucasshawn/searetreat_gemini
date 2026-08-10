import urllib.request
import urllib.parse
import json

pat = ""
with open('.env') as f:
    for line in f:
        if line.startswith('HOSPITABLE_PAT='):
            pat = line.strip().split('=', 1)[1].strip('"\'')

prop_id = "ae163eb2-66be-43b4-af71-2bfa6a2cf854"

all_reservations = []
page = 1
while True:
    params = urllib.parse.urlencode([
        ('properties[]', prop_id),
        ('start_date', '2026-06-01'),
        ('end_date', '2026-08-31'),
        ('date_query', 'checkout'),
        ('include', 'financials,guest,listings'),
        ('page', page)
    ])

    url = f'https://public.api.hospitable.com/v2/reservations?{params}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {pat}',
        'Accept': 'application/json',
        'User-Agent': 'Python/3.11'
    })

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        res_list = data.get('data', [])
        all_reservations.extend(res_list)
        meta = data.get('meta', {})
        if meta.get('current_page', page) >= meta.get('last_page', page) or not res_list:
            break
        page += 1

# Filter for July 2026: departure_date > 2026-07-01 and departure_date <= 2026-08-01
july_reservations = []
for r in all_reservations:
    dep = r.get('departure_date') or r.get('check_out') or ""
    dep_date = dep[:10]
    if '2026-07-01' < dep_date <= '2026-08-01':
        july_reservations.append(r)

july_reservations.sort(key=lambda x: (x.get('arrival_date') or x.get('check_in') or ""))

print(f"July 2026 Reservations Count: {len(july_reservations)}\n")

for i, r in enumerate(july_reservations):
    arr = (r.get('arrival_date') or r.get('check_in'))[:10]
    dep = (r.get('departure_date') or r.get('check_out'))[:10]
    guest_name = f"{r.get('guest', {}).get('first_name', '')} {r.get('guest', {}).get('last_name', '')}".strip()
    status = r.get('status')
    code = r.get('code')
    platform = r.get('platform')
    nights = r.get('nights')
    
    fin = r.get('financials', {})
    host_fin = fin.get('host', {})
    guest_fin = fin.get('guest', {})
    
    # Financial breakdowns
    acc = host_fin.get('accommodation', {}).get('amount', 0) / 100.0
    clean_fee = 0.0
    extra_guest_fee = 0.0
    for gf in host_fin.get('guest_fees', []):
        cat = gf.get('category')
        lbl = gf.get('label', '').lower()
        amt = gf.get('amount', 0) / 100.0
        if 'cleaning' in lbl:
            clean_fee += amt
        else:
            extra_guest_fee += amt
            
    host_fees = sum([hf.get('amount', 0) for hf in host_fin.get('host_fees', [])]) / 100.0
    discounts = sum([d.get('amount', 0) for d in host_fin.get('discounts', [])]) / 100.0
    revenue = host_fin.get('revenue', {}).get('amount', 0) / 100.0
    
    print(f"[{i+1}] Code: {code} | Platform: {platform} | Status: {status}")
    print(f"    Dates: {arr} to {dep} ({nights} nights) | Guest: {guest_name}")
    print(f"    Host Accommodation: ${acc:.2f} | Cleaning Fee: ${clean_fee:.2f} | Extra Guest Fee: ${extra_guest_fee:.2f}")
    print(f"    Discounts: ${discounts:.2f} | Host Fees: ${host_fees:.2f} | Host Revenue: ${revenue:.2f}")
    print("-" * 80)
