import asyncio
import os
import tempfile
import subprocess
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, types
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
ACCESS_PASSWORD = os.getenv('ACCESS_PASSWORD')

print("Bot is starting...")
print(f"TOKEN loaded: {bool(API_TOKEN)} | PASSWORD loaded: {bool(ACCESS_PASSWORD)}")

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

router = Router()
dp.include_router(router)

# Define conversation states
class FileUploadState(StatesGroup):
    waiting_for_password = State()
    waiting_for_domains = State()
    waiting_for_keywords = State()

# Dictionary to store temporary directories for user sessions
user_sessions = {}

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    print(f"[START] User {message.from_user.id} sent /start")
    await state.set_state(FileUploadState.waiting_for_password)
    await message.answer("🔐 Please enter the access password:")

@router.message(FileUploadState.waiting_for_password)
async def check_password(message: types.Message, state: FSMContext):
    print(f"[PASSWORD] User {message.from_user.id} entered: {message.text}")
    if message.text == ACCESS_PASSWORD:
        # Create a temporary directory for this user session
        user_sessions[message.from_user.id] = tempfile.mkdtemp()
        print(f"[ACCESS GRANTED] Session created for user {message.from_user.id}")
        await state.set_state(FileUploadState.waiting_for_domains)
        await message.answer("✅ Access granted. Please upload `domains.txt`.")
    else:
        print(f"[ACCESS DENIED] Wrong password from user {message.from_user.id}")
        await message.answer("⛔ Incorrect password. Please try again.")

@router.message(FileUploadState.waiting_for_domains)
async def get_domains(message: types.Message, state: FSMContext):
    if not message.document:
        await message.answer("⚠️ Please upload the `domains.txt` file.")
        return

    file_path = os.path.join(user_sessions[message.from_user.id], "domains.txt")
    # Get the file via bot API using file_id
    file = await bot.get_file(message.document.file_id)
    await file.download(destination=file_path)
    print(f"[UPLOAD] domains.txt received from user {message.from_user.id}")

    await state.set_state(FileUploadState.waiting_for_keywords)
    await message.answer("📥 `domains.txt` received. Now upload `keywords.txt`.")

@router.message(FileUploadState.waiting_for_keywords)
async def get_keywords(message: types.Message, state: FSMContext):
    if not message.document:
        await message.answer("⚠️ Please upload the `keywords.txt` file.")
        return

    file_path = os.path.join(user_sessions[message.from_user.id], "keywords.txt")
    file = await bot.get_file(message.document.file_id)
    await file.download(destination=file_path)
    print(f"[UPLOAD] keywords.txt received from user {message.from_user.id}")

    await message.answer("🚀 Starting the analysis. This may take some time...")
    work_dir = user_sessions[message.from_user.id]

    # Copy the analysis script into the user session directory as script.py
    script_path = os.path.join(work_dir, "script.py")
    with open("weba_checker_final_fullcontent_check.py", "r", encoding="utf-8") as src:
        with open(script_path, "w", encoding="utf-8") as dst:
            dst.write(src.read())

    print(f"[RUN] Executing script for user {message.from_user.id} in {work_dir}")
    subprocess.run(["python", script_path], cwd=work_dir)

    results_path = os.path.join(work_dir, "results.csv")
    no_match_path = os.path.join(work_dir, "no_match_log.txt")

    if os.path.exists(results_path):
        print(f"[RESULT] Sending results.csv to user {message.from_user.id}")
        await message.answer_document(FSInputFile(results_path))
    if os.path.exists(no_match_path):
        print(f"[RESULT] Sending no_match_log.txt to user {message.from_user.id}")
        await message.answer_document(FSInputFile(no_match_path))

    await message.answer("✅ Analysis complete. Use /start to begin again.")
    print(f"[DONE] Session complete for user {message.from_user.id}")
    await state.clear()

@router.message()
async def catch_all(message: types.Message):
    print(f"[CATCH-ALL] {message.from_user.id}: {message.text}")
    await message.answer("🤖 I received a message but don't know how to process it. Use /start")

if __name__ == '__main__':
    print("About to start polling...")
    asyncio.run(dp.start_polling(bot))
    print("Polling finished")
