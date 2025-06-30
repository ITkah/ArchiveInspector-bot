print("Bot is starting...")

import os
from dotenv import load_dotenv
load_dotenv()

print(f"ENV from OS: API={os.environ.get('API_TOKEN')}, PWD={os.environ.get('ACCESS_PASSWORD')}")

API_TOKEN = os.getenv('API_TOKEN')
ACCESS_PASSWORD = os.getenv('ACCESS_PASSWORD')
print(f"TOKEN loaded: {bool(API_TOKEN)} | PASSWORD loaded: {bool(ACCESS_PASSWORD)}")

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

print("About to start polling...")
import asyncio
asyncio.run(dp.start_polling(bot))
print("Polling finished")