import asyncio
import os
import tempfile
import subprocess
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.filters import CommandStart, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile

API_TOKEN = 'YOUR_TELEGRAM_BOT_API_TOKEN'  # <-- replace with your token
ACCESS_PASSWORD = '1234'  # <-- set your desired password

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class FileUploadState(StatesGroup):
    waiting_for_password = State()
    waiting_for_domains = State()
    waiting_for_keywords = State()

user_sessions = {}

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(FileUploadState.waiting_for_password)
    await message.answer("🔐 Please enter the access password:")

@dp.message(FileUploadState.waiting_for_password)
async def check_password(message: types.Message, state: FSMContext):
    if message.text == ACCESS_PASSWORD:
        user_sessions[message.from_user.id] = tempfile.mkdtemp()
        await state.set_state(FileUploadState.waiting_for_domains)
        await message.answer("✅ Access granted. Please upload `domains.txt`.")
    else:
        await message.answer("⛔ Incorrect password. Please try again.")

@dp.message(FileUploadState.waiting_for_domains)
async def get_domains(message: types.Message, state: FSMContext):
    if not message.document:
        await message.answer("⚠️ Please upload the `domains.txt` file.")
        return

    file_path = os.path.join(user_sessions[message.from_user.id], "domains.txt")
    await message.document.download(destination_file=file_path)
    await state.set_state(FileUploadState.waiting_for_keywords)
    await message.answer("📥 `domains.txt` received. Now upload `keywords.txt`.")

@dp.message(FileUploadState.waiting_for_keywords)
async def get_keywords(message: types.Message, state: FSMContext):
    if not message.document:
        await message.answer("⚠️ Please upload the `keywords.txt` file.")
        return

    file_path = os.path.join(user_sessions[message.from_user.id], "keywords.txt")
    await message.document.download(destination_file=file_path)

    await message.answer("🚀 Starting the analysis. This may take some time...")
    work_dir = user_sessions[message.from_user.id]

    # Copy the main script
    script_path = os.path.join(work_dir, "script.py")
    with open("weba_checker_final_fullcontent_check.py", "r", encoding="utf-8") as src:
        with open(script_path, "w", encoding="utf-8") as dst:
            dst.write(src.read())

    process = subprocess.run(
        ["python", script_path],
        cwd=work_dir
    )

    results_path = os.path.join(work_dir, "results.csv")
    no_match_path = os.path.join(work_dir, "no_match_log.txt")

    if os.path.exists(results_path):
        await message.answer_document(FSInputFile(results_path))
    if os.path.exists(no_match_path):
        await message.answer_document(FSInputFile(no_match_path))

    await message.answer("✅ Analysis complete. Use /start to begin again.")
    await state.clear()

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
