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
    ('include', 'financials,guest,listings,notes,tags,custom_fields')
])

url = f'https://public.api.hospitable.com/v2/reservations?{params}'
req = urllib.request.Request(url, headers={
    'Authorization': f'Bearer {pat}',
    'Accept': 'application/json',
    'User-Agent': 'Python/3.11'
})

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    reservations = data.get('data', [])
    for res in reservations:
        if res.get('code') == 'HA-2Z76ZC':
            print("=== TRISTAN MONROE RESERVATION RAW DATA ===")
            print(json.dumps(res, indent=2))
            break
