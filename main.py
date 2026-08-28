import requests
from bs4 import BeautifulSoup
import os
import hashlib

# BURALARI KENDİNİZE GÖRE DÜZENLEYİN
URL = "https://yhgm.saglik.gov.tr/TR-119311/130donem-devlet-hizmeti-yukumlulugu-kurasi.html"
NTFY_TOPIC = "aa_1453_1_26"

def get_page_hash():
    # Siteye Linux üzerinden standart bir tarayıcı gibi bağlanıyoruz
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text(separator=' ', strip=True)
    
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

try:
    current_hash = get_page_hash()
    previous_hash = ""
    
    if os.path.exists("state.txt"):
        with open("state.txt", "r") as f:
            previous_hash = f.read().strip()

    if previous_hash and current_hash != previous_hash:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}", 
            data=f"Sitede değişiklik tespit edildi!\nBağlantı: {URL}".encode('utf-8')
        )
        print("Değişiklik algılandı ve ntfy üzerinden bildirim gönderildi.")
    elif not previous_hash:
        print("İlk çalışma: state.txt oluşturuldu. Sonraki çalıştırmada karşılaştırma yapılacak.")
    else:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}", 
            data=f"Sitede herhangi bir değişiklik yok".encode('utf-8')
        )
        print("Sitede herhangi bir değişiklik yok.")

    with open("state.txt", "w") as f:
        f.write(current_hash)

except Exception as e:
    print("Bir hata oluştu:", e)
