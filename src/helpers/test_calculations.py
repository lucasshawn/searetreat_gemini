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

print(f"Total July 2026 Reservations: {len(july_reservations)}\n")

rows = []
for r in july_reservations:
    code = r.get('code')
    platform = r.get('platform')
    guest_name = f"{r.get('guest', {}).get('first_name', '')} {r.get('guest', {}).get('last_name', '')}".strip()
    arr = (r.get('arrival_date') or r.get('check_in'))[:10]
    dep = (r.get('departure_date') or r.get('check_out'))[:10]
    nights = r.get('nights')
    
    fin = r.get('financials', {})
    host_fin = fin.get('host', {})
    guest_fin = fin.get('guest', {})
    
    # Base accommodation
    acc = host_fin.get('accommodation', {}).get('amount', 0) / 100.0
    
    # Guest fees
    cleaning_fee = 0.0
    extra_guest_fee = 0.0
    other_guest_fees = 0.0
    for gf in host_fin.get('guest_fees', []):
        lbl = gf.get('label', '').lower()
        amt = gf.get('amount', 0) / 100.0
        if 'clean' in lbl:
            cleaning_fee += amt
        elif 'extra' in lbl or 'additional guest' in lbl:
            extra_guest_fee += amt
        else:
            other_guest_fees += amt
            
    # Discounts
    discounts = sum([d.get('amount', 0) for d in host_fin.get('discounts', [])]) / 100.0
    
    # Host fees (platform fee, host service fee, paid to vrbo, etc.)
    host_fees = sum([hf.get('amount', 0) for hf in host_fin.get('host_fees', [])]) / 100.0 # stored as negative in API
    platform_fee = abs(host_fees)
    
    # Taxes
    host_taxes = sum([t.get('amount', 0) for t in host_fin.get('taxes', [])]) / 100.0
    guest_taxes = sum([t.get('amount', 0) for t in guest_fin.get('taxes', [])]) / 100.0
    
    # Net Eligible Rental Revenue (Base Rent + Extra Guest Fee + Discounts)
    net_rental_revenue = acc + extra_guest_fee + discounts
    
    # Property Manager Fee (15%)
    pm_fee = net_rental_revenue * 0.15
    
    # Cleaner Payout
    cleaner_payout = cleaning_fee
    
    # Gross Revenue (Rent + Cleaning + Fees)
    # Rent = acc + discounts, Fees = extra_guest_fee + cleaning_fee (or Rent = net_rental_revenue, Gross Revenue = net_rental_revenue + cleaning_fee)
    gross_revenue = net_rental_revenue + cleaning_fee
    
    # Net Host Revenue (from API)
    api_host_revenue = host_fin.get('revenue', {}).get('amount', 0) / 100.0
    
    # Net Owner Income = Gross Revenue - (Platform Fees + Taxes + PM Fee + Cleaner Fee)
    # Note: Platform Fees = platform_fee, PM Fee = pm_fee, Cleaner Fee = cleaner_payout, Taxes = host_taxes
    net_owner_income = gross_revenue - platform_fee - host_taxes - pm_fee - cleaner_payout
    
    rows.append({
        'code': code,
        'platform': platform,
        'guest': guest_name,
        'checkin': arr,
        'checkout': dep,
        'nights': nights,
        'accommodation': acc,
        'extra_guest_fee': extra_guest_fee,
        'discounts': discounts,
        'net_rental_revenue': net_rental_revenue,
        'cleaning_fee': cleaning_fee,
        'gross_revenue': gross_revenue,
        'platform_fee': platform_fee,
        'pm_fee': pm_fee,
        'cleaner_payout': cleaner_payout,
        'host_taxes': host_taxes,
        'guest_taxes': guest_taxes,
        'api_host_revenue': api_host_revenue,
        'net_owner_income': net_owner_income
    })

print(f"{'Code':<12} | {'Checkin':<10} | {'Checkout':<10} | {'Rent Revenue':<12} | {'Cleaning':<9} | {'Gross Rev':<10} | {'Platform Fee':<12} | {'PM Fee (15%)':<12} | {'Cleaner Fee':<11} | {'Net Owner Inc':<12}")
print("-" * 130)

tot_rent_rev = 0
tot_cleaning = 0
tot_gross = 0
tot_platform = 0
tot_pm = 0
tot_cleaner = 0
tot_net_owner = 0

for r in rows:
    print(f"{r['code']:<12} | {r['checkin']:<10} | {r['checkout']:<10} | ${r['net_rental_revenue']:<11.2f} | ${r['cleaning_fee']:<8.2f} | ${r['gross_revenue']:<9.2f} | ${r['platform_fee']:<11.2f} | ${r['pm_fee']:<11.2f} | ${r['cleaner_payout']:<10.2f} | ${r['net_owner_income']:<11.2f}")
    tot_rent_rev += r['net_rental_revenue']
    tot_cleaning += r['cleaning_fee']
    tot_gross += r['gross_revenue']
    tot_platform += r['platform_fee']
    tot_pm += r['pm_fee']
    tot_cleaner += r['cleaner_payout']
    tot_net_owner += r['net_owner_income']

print("-" * 130)
print(f"{'TOTALS':<36} | ${tot_rent_rev:<11.2f} | ${tot_cleaning:<8.2f} | ${tot_gross:<9.2f} | ${tot_platform:<11.2f} | ${tot_pm:<11.2f} | ${tot_cleaner:<10.2f} | ${tot_net_owner:<11.2f}")
