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

july_reservations = []
for r in all_reservations:
    dep = r.get('departure_date') or r.get('check_out') or ""
    dep_date = dep[:10]
    if '2026-07-01' < dep_date <= '2026-08-01':
        july_reservations.append(r)

july_reservations.sort(key=lambda x: (x.get('arrival_date') or x.get('check_in') or ""))

for i, r in enumerate(july_reservations):
    print(f"==================================================")
    print(f"RESERVATION #{i+1}: {r.get('code')} ({r.get('platform')})")
    print(f"Guest: {r.get('guest', {}).get('first_name')} {r.get('guest', {}).get('last_name')}")
    print(f"Arrival: {r.get('arrival_date')[:10]} | Departure: {r.get('departure_date')[:10]} | Nights: {r.get('nights')}")
    print("HOST FINANCIALS:")
    print(json.dumps(r.get('financials', {}).get('host', {}), indent=2))
    print("GUEST FINANCIALS:")
    print(json.dumps(r.get('financials', {}).get('guest', {}), indent=2))
