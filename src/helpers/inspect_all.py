import urllib.request
import urllib.parse
import json

pat = ""
with open('.env') as f:
    for line in f:
        if line.startswith('HOSPITABLE_PAT='):
            pat = line.strip().split('=', 1)[1].strip('"\'')

prop_id = "ae163eb2-66be-43b4-af71-2bfa6a2cf854"

# Pagination check
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
        current_page = meta.get('current_page', page)
        last_page = meta.get('last_page', page)
        print(f"Fetched page {current_page} / {last_page}, count: {len(res_list)}")
        if current_page >= last_page or not res_list:
            break
        page += 1

print(f"\nTotal reservations fetched across all pages: {len(all_reservations)}")

for r in all_reservations:
    arrival = r.get('arrival_date') or r.get('check_in')
    departure = r.get('departure_date') or r.get('check_out')
    status = r.get('status')
    code = r.get('code')
    print(f"Code: {code} | Status: {status} | StayType: {r.get('stay_type')} | Arrival: {arrival} | Departure: {departure}")
