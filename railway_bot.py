import pandas as pd
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# 1. Excel dosyasını yükle
def load_excel_data():
    try:
        # Excel dosyasını yükle
        excel_path = 'SRK_PartiPerformans02.xlsx'
        df = pd.read_excel(excel_path, sheet_name='SRK_PartiPerformans02')
        print(f"✅ Excel dosyası yüklendi: {excel_path}")
        
        # Veri hazırlığı
        df['Parti No'] = df['Parti No'].astype(str)
        df.set_index('Parti No', inplace=True)
        
        return df
    except Exception as e:
        print(f"❌ Excel yükleme hatası: {e}")
        return None

# Excel verisini yükle
df = load_excel_data()

# 2. Log ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 3. Başlangıç komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏭 *Parti Performans Sorgulama Botu* 🏭\n\n"
        "Sadece *Parti No* girin (örneğin: 251033)\n"
        "Ben size tüm üretim performans detaylarını getireceğim.\n\n"
        "✅ *Kullanım:* Parti numarasını yazıp gönderin.",
        parse_mode='Markdown'
    )

# 4. Yardım komutu
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Yardım*\n\n"
        "1. Sadece Parti No girin (örn: 251033)\n"
        "2. Bot size şu bilgileri getirecek:\n"
        "   • Parti metrajı ve kalite bilgileri\n"
        "   • Kopuş ve randıman verileri\n"
        "   • Çözgü ve haşıl bilgileri\n"
        "   • İplik ve levent detayları",
        parse_mode='Markdown'
    )

# 5. Parti No işleme
async def handle_parti_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if df is None:
        await update.message.reply_text(
            "❌ *Veritabanı yüklenemedi!*\n"
            "Lütfen daha sonra tekrar deneyin.",
            parse_mode='Markdown'
        )
        return
    
    parti_no = update.message.text.strip()
    
    if parti_no not in df.index:
        await update.message.reply_text(
            f"❌ *Parti No '{parti_no}' bulunamadı!*\n"
            f"Lütfen geçerli bir Parti No girin.",
            parse_mode='Markdown'
        )
        return
    
    # Parti verisini al
    row = df.loc[parti_no]
    
    response = f"🏭 *PARTİ PERFORMANS RAPORU* 🏭\n"
    
    response += f"🔢 *Parti No:* {parti_no}\n"
    response += f"📏 *Parti Metrajı:* {row.get('Toplam Parti Metre', 'N/A'):,.2f} m\n"
    response += f"🎨 *İndigo Tip Adı:* {row.get('Tip Dağılım Bilgi', 'N/A')}\n"
    response += f"🏷️ *Kalite Tip Adı:* {row.get('KaliteCikanUrunAdi', 'N/A')}\n\n"
    
    response += f"📊 *KALİTE KONTROL BİLGİLERİ*\n"
    response += f"1A Metrajı: {row.get('Kalite1Metre', 'N/A'):,.2f} m\n"
    response += f"Toplam Metre: {row.get('Kalite Metre', 'N/A'):,.2f} m\n"
    response += f"Kalite Oranı: {row.get('Kalite %', 'N/A'):,.2f}%\n\n"
    
    response += f"🧵 *İPLİK & LEVENT BİLGİLERİ*\n"
    cozgu_iplikleri = []
    if pd.notna(row.get('Cozgu1 Iplik Adi')):
        cozgu_iplikleri.append(str(row.get('Cozgu1 Iplik Adi')))
    if pd.notna(row.get('Cozgu2 Iplik Adi')):
        cozgu_iplikleri.append(str(row.get('Cozgu2 Iplik Adi')))
    if pd.notna(row.get('Cozgu3 Iplik Adi')):
        cozgu_iplikleri.append(str(row.get('Cozgu3 Iplik Adi')))
    
    cozgu_text = " + ".join(cozgu_iplikleri) if cozgu_iplikleri else "N/A"
    response += f"Çözgü İplik Ne Cinsi: {cozgu_text}\n"
    response += f"Çözgü Lotu: {row.get('Hammadde Lotu', 'N/A')}\n\n"
    
    response += f"⚠️ *SERİ ÇÖZGÜ BİLGİLERİ*\n"
    response += f"Seri Çözgü Kopuş Adeti: {row.get('SC Toplam Kopus Adet', 'N/A')}\n"
    response += f"Seri Çözgü Kopuş Oranı: {row.get('SC Kopus Milyon', 'N/A'):,.2f}\n\n"
    
    response += f"⚠️ *SLASHER BİLGİLERİ*\n"
    response += f"Reçete Adı: {row.get('Reçete Adı', 'N/A')}\n"
    response += f"Haşıl Açıklaması: {row.get('Hasil Aciklama', 'N/A')}\n"
    response += f"Toplam Kopuş Adeti: {row.get('Toplam Kopus', 'N/A')}\n"
    response += f"Hamut Adeti: {row.get('Parti Hamut Adet', 'N/A')}\n"
    response += f"Sarık Adeti: {row.get('Parti Sarık Adet', 'N/A')}\n"
    response += f"Slasher Kopuş Oranı: {row.get('Parti Kopus Binde', 'N/A'):,.3f}‰\n\n"
    
    response += f"📈 *RANDIMAN & PERFORMANS*\n"
    response += f"Salon Randımanı: {row.get('Salon R%', 'N/A'):,.2f}%\n"
    response += f"Efektif Randıman: {row.get('Efektif R%', 'N/A'):,.2f}%\n"
    response += f"Ortalama Devir: {row.get('Devir', 'N/A'):,.2f} rpm\n"
    response += f"Atkı Kopuş Oranı: {row.get('A 10*5', 'N/A'):,.2f}\n"
    response += f"Çözgü Kopuş Oranı: {row.get('Ç 10*5', 'N/A'):,.2f}\n\n"
    
    response += f"Levent Numaraları: {row.get('Indigo Levent Numaralari', 'N/A')}\n\n"
    
    response += f"📅 *Son Güncelleme:* {row.get('Son Güncellenme Zamanı', 'N/A')}\n"
    
    if len(response) > 4000:
        response = response[:4000] + "\n\n... (mesaj çok uzun, kısaltıldı)"
    
    await update.message.reply_text(response, parse_mode='Markdown')

# 6. Hatalı mesajları ele al
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤔 *Anlamadım!*\n"
        "Lütfen sadece Parti No girin (örneğin: 251033)\n"
        "Yardım için /help yazın.",
        parse_mode='Markdown'
    )

# 7. Ana fonksiyon
def main():
    # Telegram Bot Token'ını environment variable'dan al
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8153956502:AAGzadeTb5RIKLbpONu05pdFLv7Bb04Q5as')
    
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_parti_no))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    
    # Botu başlat
    print("🤖 Parti Performans Botu Railway'de çalışıyor...")
    
    app.run_polling()

if __name__ == '__main__':
    main()