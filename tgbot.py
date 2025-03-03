import asyncio
import logging
import os
import aiohttp
import aiosqlite
from aiogram import Bot,Dispatcher,types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

print(f"TOKEN: {TOKEN}")

bot = Bot(token = TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

async def setup_dp():
    async with aiosqlite.connect("users_db") as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                users_id INTEGER UNIQUE,
                city TEXT 
            )
            ''')
        await db.commit()

async def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    temp = data['main']['temp']
                    desc = data['weather'][0]['description']
                    return f"🌍 City: {city}\n  Temperature: {temp}°C\n☁️ Weather: {desc}"
                else:
                    return "City not found!"
    except Exception as e:
        return f"Error with getting forecast: {str(e)}"

def get_city_buttons():
    builder = InlineKeyboardBuilder()
    cities = ["Kyiv","Amsterdam","Minsk","London","Paris","Warsaw"]
    for city in cities:
        builder.add(InlineKeyboardButton(text = city, callback_data=city))
    return builder.as_markup()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 hello,im bot who shows the weather.\n Input the city name and i show you the forecast!.",
        reply_markup=get_city_buttons())


@dp.message()
async def send_weather(message: Message):
    city = message.text.strip()

    weather_info = await get_weather(city)

    async with aiosqlite.connect("users_db") as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id, city) VALUES (?, ?)", (message.from_user.id, city))
        await db.commit()

    await message.answer(weather_info)

@dp.callback_query()
async def city_callback(call:types.CallbackQuery):
    city = call.data
    weather_info = await get_weather(city)
    await call.message.answer(weather_info)

async def main():
    await setup_dp()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



