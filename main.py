#python
import requests
from bs4 import BeautifulSoup
import os
import hashlib

# BURALARI KENDİNİZE GÖRE DÜZENLEYİN
URL = "https://yhgm.saglik.gov.tr/TR-119311/130donem-devlet-hizmeti-yukumlulugu-kurasi.html"
NTFY_TOPIC = "aa_1453.1.26"

def get_page_hash():
    # Siteye sanki bir tarayıcıymışız gibi bağlanıyoruz
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(URL, headers=headers)
    response.raise_for_status()
    
    # Sitenin sadece metin kısımlarını alıyoruz (Görünmez kod değişiklikleri bizi yanıltmasın diye)
    soup = BeautifulSoup(response.text, 'html.parser')
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text(separator=' ', strip=True)
    
    # Tüm metni kaydetmek yerine metnin bir "özetini" (hash) çıkarıyoruz
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

try:
    current_hash = get_page_hash()
    previous_hash = ""
    
    # Eski durum dosyası var mı kontrol et
    if os.path.exists("state.txt"):
        with open("state.txt", "r") as f:
            previous_hash = f.read().strip()

    # Eğer eski durum varsa ve yeni durumla eşleşmiyorsa site değişmiştir
    if previous_hash and current_hash != previous_hash:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}", 
            data=f"Sitede değişiklik tespit edildi!\nBağlantı: {URL}".encode('utf-8')
        )

    # Yeni durumu dosyaya yazıyoruz ki bir sonraki kontrolde karşılaştırabilelim
    with open("state.txt", "w") as f:
        f.write(current_hash)

except Exception as e:
    print("Bir hata oluştu:", e)