import urllib.request
import urllib.parse
import json

pat = ""
with open('.env') as f:
    for line in f:
        if line.startswith('HOSPITABLE_PAT='):
            pat = line.strip().split('=', 1)[1].strip('"\'')

params = urllib.parse.urlencode([
    ('properties[]', 'ae163eb2-66be-43b4-af71-2bfa6a2cf854'),
    ('start_date', '2026-06-01'),
    ('end_date', '2026-08-31'),
    ('date_query', 'checkout'),
    ('include', 'financials,guest,listings')
])

req = urllib.request.Request(f'https://public.api.hospitable.com/v2/reservations?{params}', headers={
    'Authorization': f'Bearer {pat}',
    'Accept': 'application/json',
    'User-Agent': 'Python/3.11'
})

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    for r in data['data']:
        if r.get('code') == 'HA-WK4CRM':
            print("HOST FINANCIALS FOR HA-WK4CRM:")
            print(json.dumps(r['financials']['host'], indent=2))
