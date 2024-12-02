import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import random

Token = "Token here"
channel_id = "link"
users_file = "json"


async def load_users():
    try:
        with open(users_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Xatolik: Foydalanuvchilarni yuklashda muammo - {e}")
        return {}


async def save_users(users):
    try:
        with open(users_file, "w+") as file:
            json.dump(users, file, indent=4)
    except Exception as e:
        print(f"Xatolik: Foydalanuvchilarni saqlashda muammo - {e}")


async def add_user(user_id, username, full_name, phone_number):
    try:
        users = await load_users()
        if str(user_id) not in users:
            users[str(user_id)] = {
                "username": username,
                "full_name": full_name,
                "phone_number": phone_number,
                "score": 0
            }
            await save_users(users)
    except Exception as e:
        print(f"Xatolik: Foydalanuvchini qo'shishda muammo - {e}")


async def is_user_registered(user_id):
    try:
        users = await load_users()
        return str(user_id) in users
    except Exception as e:
        print(f"Xatolik: Ro'yxatni tekshirishda muammo - {e}")
        return False


questions = [
    {"savol": "2 + 2 ?", "javob": "4"},
    {"savol": "5 x 3 ?", "javob": "15"},
    {"savol": "8 / 2 ?", "javob": "4"},
    {"savol": "10 - 3 ?", "javob": "7"},
    {"savol": "6 + 4 ?", "javob": "10"},
    {"savol": "9 x 2 ?", "javob": "18"},
    {"savol": "15 / 5 ?", "javob": "3"},
    {"savol": "7 - 2 ?", "javob": "5"},
    {"savol": "5 + 5 ?", "javob": "10"},
    {"savol": "12 - 4 ?", "javob": "8"},
]

user_test_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        "Salom! Iltimos, quyidagi tugmalardan birini tanlang:",
        reply_markup=ReplyKeyboardMarkup(
            [["Register", "Test"]],
            resize_keyboard=True
        )
    )


async def register_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        text="Iltimos, telefon raqamingizni ulashing:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📞 Telefon raqamini ulash", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )


async def save_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = update.effective_user.id
    username = update.effective_user.username
    full_name = update.effective_user.full_name
    phone_number = contact.phone_number

    await add_user(user_id, username, full_name, phone_number)
    await update.message.reply_text("Siz muvaffaqiyatli ro'yxatdan o'tdingiz!")


async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_registered(user_id):
        await update.message.reply_text("Iltimos, avval ro'yxatdan o'ting!")
        return

    user_test_data[user_id] = {"score": 0, "current_question": 0}
    await send_next_question(update, context)


async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    current_index = user_test_data[user_id]["current_question"]

    if current_index < len(questions):
        question = questions[current_index]["savol"]
        await update.message.reply_text(f"Savol {current_index + 1}: {question}")
        user_test_data[user_id]["current_question"] += 1
    else:
        await finish_test(update, context)


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_test_data:
        await update.message.reply_text("Iltimos, avval Testni boshlang!")
        return

    current_index = user_test_data[user_id]["current_question"] - 1
    correct_answer = questions[current_index]["javob"]
    user_answer = update.message.text

    if user_answer == correct_answer:
        user_test_data[user_id]["score"] += 1

    await send_next_question(update, context)


async def finish_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    score = user_test_data[user_id]["score"]
    users = await load_users()
    user_info = users.get(str(user_id), {})

    message = (
        f"Test yakunlandi!\n\n"
        f"Ism: {user_info.get('full_name', 'Noma’lum')}\n"
        f"Telefon: {user_info.get('phone_number', 'Noma’lum')}\n"
        f"Username: @{user_info.get('username', 'Noma’lum')}\n"
        f"Natija: {score}/{len(questions)}"
    )

    await context.bot.send_message(chat_id=channel_id, text=message)
    await update.message.reply_text("Test tugadi. Natijalar kanalda e'lon qilindi.")

    users[str(user_id)]["score"] = score
    await save_users(users)
    del user_test_data[user_id]


if __name__ == "__main__":
    app = ApplicationBuilder().token(Token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^Register$"), register_user))
    app.add_handler(MessageHandler(filters.CONTACT, save_contact))
    app.add_handler(MessageHandler(filters.Regex("^Test$"), start_test))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    print("Bot ishga tushdi...")
    app.run_polling()
