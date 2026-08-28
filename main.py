import requests
from bs4 import BeautifulSoup
import os
import time
import subprocess
import sys

# ================== AYARLAR ==================
URL = "https://yhgm.saglik.gov.tr/TR-119308/130donem-devlet-hizmeti-yukumlulugu-kurasi.html"
NTFY_TOPIC = "aa_1453_1_26"
ANAHTAR_KELIME = "Münhal Kadrolar"

KONTROL_ARALIGI = 5 * 60          # her kontrol arası 5 dakika
MAKS_CALISMA_SURESI = 5 * 60 * 60 + 50 * 60   # 5 saat 50 dk sonra kendini yeniden tetikler
STATE_DOSYASI = "state.txt"
WORKFLOW_DOSYA_ADI = "monitor.yml"   # .github/workflows/ altındaki dosya adı

# GitHub Actions tarafından otomatik sağlanan ortam değişkenleri
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")  # "kullanici/repo" formatında
GITHUB_REF_NAME = os.environ.get("GITHUB_REF_NAME", "main")


def check_keyword():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    return ANAHTAR_KELIME.lower() in text.lower()


def read_state():
    if os.path.exists(STATE_DOSYASI):
        with open(STATE_DOSYASI, "r") as f:
            return f.read().strip()
    return ""


def write_state_and_commit(yeni_durum):
    with open(STATE_DOSYASI, "w") as f:
        f.write(yeni_durum)

    # Değişikliği doğrudan buradan commit'liyoruz çünkü script hiç bitmeyebilir,
    # workflow'un sonundaki adımlar hiç çalışmayabilir.
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"], check=True)
        subprocess.run(["git", "config", "--global", "user.email",
                         "github-actions[bot]@users.noreply.github.com"], check=True)
        subprocess.run(["git", "add", STATE_DOSYASI], check=True)

        # Eğer gerçek bir değişiklik yoksa commit boş kalır, bunu es geçiyoruz
        diff_check = subprocess.run(["git", "diff", "--cached", "--quiet"])
        if diff_check.returncode != 0:
            subprocess.run(["git", "commit", "-m", "Site durumu güncellendi"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("state.txt commit edildi ve push edildi.")
        else:
            print("state.txt içeriği değişmedi, commit atlanıyor.")
    except subprocess.CalledProcessError as e:
        print("Git işlemi sırasında hata:", e)


def trigger_self_rerun():
    """6 saatlik iş limitine takılmadan önce workflow'u yeniden tetikler."""
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        print("UYARI: GITHUB_TOKEN veya GITHUB_REPOSITORY bulunamadı, kendini yeniden tetikleyemiyor.")
        return False

    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/workflows/{WORKFLOW_DOSYA_ADI}/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {"ref": GITHUB_REF_NAME}

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        if resp.status_code == 204:
            print("Yeni bir workflow çalıştırması başarıyla tetiklendi.")
            return True
        else:
            print(f"Yeniden tetikleme başarısız. Kod: {resp.status_code}, Yanıt: {resp.text}")
            return False
    except Exception as e:
        print("Yeniden tetikleme sırasında hata:", e)
        return False


def main():
    baslangic = time.monotonic()

    while True:
        try:
            is_found = check_keyword()
            mevcut_durum = read_state()
            already_notified = (mevcut_durum == "bulundu")

            if is_found and not already_notified:
                requests.post(
                    f"https://ntfy.sh/{NTFY_TOPIC}",
                    data=f"DİKKAT: '{ANAHTAR_KELIME}' sitede yayınlandı!\nBağlantı: {URL}".encode('utf-8'),
                    timeout=15
                )
                print("Kelime bulundu ve bildirim gönderildi.")
                write_state_and_commit("bulundu")

            elif not is_found and already_notified:
                write_state_and_commit("bulunmadi")
                print("Kelime siteden kaldırılmış, durum sıfırlandı.")

            else:
                print("Kelime sitede var, bildirim zaten gönderilmiş." if is_found
                      else "Kelime henüz sitede yok.")

        except Exception as e:
            print("Bir hata oluştu:", e)

        gecen_sure = time.monotonic() - baslangic
        if gecen_sure >= MAKS_CALISMA_SURESI:
            print("Maksimum çalışma süresine yaklaşıldı, yeni bir çalıştırma tetikleniyor...")
            trigger_self_rerun()
            sys.exit(0)

        print(f"{KONTROL_ARALIGI} saniye erteleniyor...")
        time.sleep(KONTROL_ARALIGI)


if __name__ == "__main__":
    main()
