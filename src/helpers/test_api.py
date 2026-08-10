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
    ('include', 'financials,guest,listings')
])

url = f'https://public.api.hospitable.com/v2/reservations?{params}'
print(f"Requesting: {url}")

req = urllib.request.Request(url, headers={
    'Authorization': f'Bearer {pat}',
    'Accept': 'application/json',
    'User-Agent': 'Python/3.11'
})

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        reservations = data.get('data', [])
        print(f"Total reservations returned: {len(reservations)}")
        print("Meta:", data.get('meta'))
        
        for i, res in enumerate(reservations):
            print(f"\n--- Reservation #{i+1} ---")
            print(f"Code/ID: {res.get('code')} / {res.get('id')}")
            print(f"Status: {res.get('status')}")
            print(f"Checkin: {res.get('checkin')}, Checkout: {res.get('checkout')}")
            print("Full Reservation Object:\n", json.dumps(res, indent=2))
except Exception as e:
    if hasattr(e, 'read'):
        print('Error body:', e.read().decode('utf-8'))
    else:
        print('Error:', e)
