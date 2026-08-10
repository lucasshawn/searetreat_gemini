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
        ('end_date', '2026-07-31'),
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

print(f"Total reservations fetched: {len(all_reservations)}")
for res in all_reservations:
    code = res.get('code')
    guest_name = f"{res.get('guest', {}).get('first_name', '')} {res.get('guest', {}).get('last_name', '')}".strip()
    if code == 'HA-WV58G4' or 'Nita' in guest_name:
        print("=== NITA STELLA RESERVATION RAW DATA ===")
        print(json.dumps(res, indent=2))
        break
