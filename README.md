# PHA/USDT Free Analysis Bot
Render hosts the analysis API; Telegram webhook handles /analysis; GitHub Actions triggers the daily report at 04:00 UTC (09:00 Pakistan).
Required Render variables: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, WEBHOOK_SECRET, SYMBOL=PHAUSDT, TIMEZONE=Asia/Karachi.
After deployment set Telegram webhook:
https://api.telegram.org/botYOUR_TOKEN/setWebhook?url=YOUR_RENDER_URL/telegram
Then create a GitHub repo and upload `.github/workflows/daily.yml`. Add GitHub Actions secrets BOT_URL and WEBHOOK_SECRET.
No Binance API key is required and the bot never places trades.
