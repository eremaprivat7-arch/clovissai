# python, osint.py
import aiohttp
import re

PLATFORMS = {
    "Telegram": "https://t.me/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "TikTok": "https://www.tiktok.com/@{}",
    "GitHub": "https://github.com/{}",
    "VK": "https://vk.com/{}",
    "Twitter (X)": "https://twitter.com/{}",
    "YouTube": "https://www.youtube.com/@{}",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Twitch": "https://www.twitch.tv/{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "Reddit": "https://www.reddit.com/user/{}"
}

async def check_username(session: aiohttp.ClientSession, username: str):
    results = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for name, url_template in PLATFORMS.items():
        url = url_template.format(username)
        try:
            async with session.get(url, headers=headers, timeout=5, allow_redirects=True) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    if "Page not found" not in text and "Sorry, this page" not in text:
                        results[name] = f"✅ {url}"
                    else:
                        results[name] = "❌ Нет"
                else:
                    results[name] = "❌ Нет"
        except Exception:
            results[name] = "⚠️ Ошибка"
    return results

def check_phone(phone: str):
    clean_phone = re.sub(r'\D', '', phone)
    if len(clean_phone) < 10:
        return "Неверный формат номера."
    
    operator = "Неизвестно"
    if clean_phone.startswith(("777", "747")):
        operator = "Tele2 / Altel"
    elif clean_phone.startswith(("701", "702")):
        operator = "Beeline"
    elif clean_phone.startswith(("705", "771")):
        operator = "Activ / Kcell"
        
    return f"📱 Номер: +{clean_phone}\n📡 Оператор: {operator}\n🔍 Google: https://www.google.com/search?q=%22{clean_phone}%22"