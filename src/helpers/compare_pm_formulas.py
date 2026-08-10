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
    july = []
    for r in data.get('data', []):
        dep = (r.get('departure_date') or r.get('check_out'))[:10]
        if '2026-07-01' < dep <= '2026-08-01':
            july.append(r)
    
    july.sort(key=lambda x: (x.get('arrival_date') or x.get('check_in') or ""))
    
    print(f"{'Code':<10} | {'Guest':<18} | {'Gross Acc':<10} | {'Discounts':<9} | {'Adjustments':<11} | {'Net Acc':<10} | {'PM Fee (Gross)':<14} | {'PM Fee (Net Acc)':<15} | {'PM Fee (Net+Adj)':<15}")
    print("-" * 125)
    
    tot_gross_acc = 0
    tot_disc = 0
    tot_adj = 0
    tot_net_acc = 0
    tot_pm_gross = 0
    tot_pm_net = 0
    tot_pm_net_adj = 0
    
    for r in july:
        code = r.get('code')
        guest = f"{r.get('guest', {}).get('first_name')} {r.get('guest', {}).get('last_name')}"
        host_fin = r.get('financials', {}).get('host', {})
        acc = host_fin.get('accommodation', {}).get('amount', 0) / 100.0
        discounts = sum([d.get('amount', 0) for d in host_fin.get('discounts', [])]) / 100.0
        adjustments = sum([a.get('amount', 0) for a in host_fin.get('adjustments', [])]) / 100.0
        
        net_acc = round(acc + discounts, 2)
        net_acc_adj = round(acc + discounts + adjustments, 2)
        
        pm_gross = round(acc * 0.15, 2)
        pm_net = round(net_acc * 0.15, 2)
        pm_net_adj = round(net_acc_adj * 0.15, 2)
        
        print(f"{code:<10} | {guest:<18} | ${acc:<9.2f} | ${discounts:<8.2f} | ${adjustments:<10.2f} | ${net_acc:<9.2f} | ${pm_gross:<13.2f} | ${pm_net:<14.2f} | ${pm_net_adj:<14.2f}")
        
        tot_gross_acc += acc
        tot_disc += discounts
        tot_adj += adjustments
        tot_net_acc += net_acc
        tot_pm_gross += pm_gross
        tot_pm_net += pm_net
        tot_pm_net_adj += pm_net_adj

    print("-" * 125)
    print(f"{'TOTALS':<31} | ${tot_gross_acc:<9.2f} | ${tot_disc:<8.2f} | ${tot_adj:<10.2f} | ${tot_net_acc:<9.2f} | ${tot_pm_gross:<13.2f} | ${tot_pm_net:<14.2f} | ${tot_pm_net_adj:<14.2f}")
