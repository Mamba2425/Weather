import logging
import os
import requests
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

TELEGRAM_TOKEN = os.getenv("7744517884:AAF4N1XJostF6o8HnIOoYLP7JVEMX3bVdf8") or "ВАШ_ТЕЛЕГРАМ_ТОКЕН"
WEATHER_API_KEY = os.getenv("a690bd87765197cadf3994735346cc02") or "ВАШ_OPENWEATHERMAP_КЛЮЧ"

logging.basicConfig(level=logging.INFO)

def get_current_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    return {
        'city': data['name'],
        'country': data['sys']['country'],
        'temp': data['main']['temp'],
        'feels_like': data['main']['feels_like'],
        'humidity': data['main']['humidity'],
        'wind': data['wind']['speed'],
        'desc': data['weather'][0]['description'],
        'icon': data['weather'][0]['icon']
    }

def get_forecast(city):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    data = r.json()
    forecasts = []
    for item in data['list'][::8]:
        forecasts.append({
            'date': item['dt_txt'].split(" ")[0],
            'temp': item['main']['temp'],
            'desc': item['weather'][0]['description'],
            'icon': item['weather'][0]['icon']
        })
    return forecasts

def format_weather(w):
    return (
        f"Погода в {w['city']}, {w['country']}:"

        f"{w['desc'].capitalize()}"

        f"Температура: {w['temp']}°C (ощущается как {w['feels_like']}°C)"

        f"Влажность: {w['humidity']}%"

        f"Ветер: {w['wind']} м/с"
    )

def format_forecast(forecast):
    text = "Прогноз на 5 дней:"

    for f in forecast:
        text += f"\n{f['date']} — {f['desc'].capitalize()}, {f['temp']}°C"
    return text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Москва"), KeyboardButton("Санкт-Петербург")],
        [KeyboardButton("Ташкент"), KeyboardButton("Нью-Йорк")],
        [KeyboardButton("Отправить геолокацию", request_location=True)],
    ]
    await update.message.reply_text(
        "Привет! Отправь название города или выбери из кнопок ниже:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    current = get_current_weather(city)
    forecast = get_forecast(city)

    if not current or not forecast:
        await update.message.reply_text("Город не найден.")
        return

    icon_url = f"http://openweathermap.org/img/wn/{current['icon']}@2x.png"
    await update.message.reply_photo(photo=icon_url, caption=format_weather(current))

    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("Показать прогноз на 5 дней", callback_data=f"forecast|{city}")]
    ])
    await update.message.reply_text("Хочешь посмотреть прогноз?", reply_markup=button)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, city = query.data.split("|")
    forecast = get_forecast(city)
    if forecast:
        icon_url = f"http://openweathermap.org/img/wn/{forecast[0]['icon']}@2x.png"
        await query.message.reply_photo(photo=icon_url, caption=format_forecast(forecast))

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loc = update.message.location
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={loc.latitude}&lon={loc.longitude}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    r = requests.get(url)
    data = r.json()
    city = data['name']
    await handle_city(update._replace(message=update.message._replace(text=city)), context)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__weather_bot__":
    main()
