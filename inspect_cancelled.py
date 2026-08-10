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
        ('start_date', '2026-05-01'),
        ('end_date', '2026-08-31'),
        ('date_query', 'checkout'),
        ('include', 'financials,guest,listings,notes'),
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

for r in all_reservations:
    dep = (r.get('departure_date') or r.get('check_out'))[:10]
    status = r.get('status')
    code = r.get('code')
    guest = f"{r.get('guest', {}).get('first_name')} {r.get('guest', {}).get('last_name')}"
    if status == 'cancelled' or r.get('reservation_status', {}).get('current', {}).get('category') == 'cancelled':
        print(f"CANCELLED STAY: {code} | Checkout: {dep} | Guest: {guest} | Status: {status}")
        host_fin = r.get('financials', {}).get('host', {})
        print(f"  Revenue: ${host_fin.get('revenue', {}).get('amount', 0)/100.0:.2f}")
        print(f"  Accommodation: ${host_fin.get('accommodation', {}).get('amount', 0)/100.0:.2f}")
        print(f"  Adjustments: ${sum([a.get('amount', 0) for a in host_fin.get('adjustments', [])])/100.0:.2f}")
        print("-" * 60)
