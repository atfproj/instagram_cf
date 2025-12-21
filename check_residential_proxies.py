#!/usr/bin/env python3
import requests
from datetime import datetime

proxies_raw = [
    "148.251.43.86:5000:r_5b683ef78d-country-us-sid-lrpp3piy:75b77ba339",
    "148.113.216.26:5000:r_5b683ef78d-country-us-sid-mo0ulzyz:75b77ba339",
    "15.235.35.31:5000:r_5b683ef78d-country-us-sid-sod8oa74:75b77ba339",
    "148.113.216.37:5000:r_5b683ef78d-country-us-sid-47isuco7:75b77ba339"
]

def parse_proxy(proxy_raw):
    parts = proxy_raw.split(':')
    if len(parts) == 4:
        host, port, username, password = parts
        return f"http://{username}:{password}@{host}:{port}", host, port
    return None, None, None

def check_site(proxy_url, site_name, site_url, timeout=2):
    try:
        response = requests.get(
            site_url,
            proxies={"http": proxy_url, "https": proxy_url},
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            allow_redirects=False
        )
        if response.status_code in [200, 301, 302]:
            return "✅ OK"
        else:
            return f"⚠️  {response.status_code}"
    except requests.exceptions.ProxyError:
        return "❌ ProxyError"
    except requests.exceptions.Timeout:
        return "❌ Timeout"
    except Exception:
        return "❌ Error"

sites = [
    ("Instagram", "https://www.instagram.com"),
    ("Facebook", "https://www.facebook.com"),
    ("LinkedIn", "https://www.linkedin.com")
]

print("="*70)
print(f"Проверка резидентских проксей: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

results = []

for proxy_raw in proxies_raw:
    proxy_url, host, port = parse_proxy(proxy_raw)
    if not proxy_url:
        print(f"\n❌ Неверный формат: {proxy_raw}")
        continue
    
    print(f"\n{'='*70}")
    print(f"Прокси: {host}:{port}")
    print(f"{'='*70}")
    
    proxy_results = {"proxy": f"{host}:{port}", "sites": {}}
    
    for site_name, site_url in sites:
        result = check_site(proxy_url, site_name, site_url, timeout=3)
        print(f"  {site_name:12} {result}")
        proxy_results["sites"][site_name] = result
    
    results.append(proxy_results)

# Итоговая таблица
print(f"\n{'='*70}")
print("ИТОГОВАЯ ТАБЛИЦА")
print(f"{'='*70}")
print(f"{'Прокси':<25} {'Instagram':<15} {'Facebook':<15} {'LinkedIn':<15}")
print("-"*70)

for r in results:
    proxy = r["proxy"]
    insta = r["sites"].get("Instagram", "❌")
    fb = r["sites"].get("Facebook", "❌")
    linkedin = r["sites"].get("LinkedIn", "❌")
    print(f"{proxy:<25} {insta:<15} {fb:<15} {linkedin:<15}")

print("="*70)

# Сохраняем в файл
with open("residential_proxy_check_results.txt", "w", encoding="utf-8") as f:
    f.write(f"Проверка резидентских проксей: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("="*70 + "\n\n")
    for r in results:
        f.write(f"Прокси: {r['proxy']}\n")
        for site_name, result in r["sites"].items():
            f.write(f"  {site_name}: {result}\n")
        f.write("\n")
    f.write("\nИТОГОВАЯ ТАБЛИЦА\n")
    f.write("-"*70 + "\n")
    f.write(f"{'Прокси':<25} {'Instagram':<15} {'Facebook':<15} {'LinkedIn':<15}\n")
    f.write("-"*70 + "\n")
    for r in results:
        proxy = r["proxy"]
        insta = r["sites"].get("Instagram", "❌")
        fb = r["sites"].get("Facebook", "❌")
        linkedin = r["sites"].get("LinkedIn", "❌")
        f.write(f"{proxy:<25} {insta:<15} {fb:<15} {linkedin:<15}\n")

print("\n✅ Результаты сохранены в residential_proxy_check_results.txt")

