import sqlite3
import telebot
import random
import string
from telebot import types

bot = telebot.TeleBot('TeleBotAPI')


conn = sqlite3.connect('menu.db', check_same_thread=False)
cursor = conn.cursor()


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('MENU')
    btn2 = types.KeyboardButton('MY ORDERS')
    btn3 = types.KeyboardButton('BARISTA')
    btn4 = types.KeyboardButton('CONTACT INFO')
    markup.add(btn1, btn2, btn3, btn4)
    video_path = "C:\\Users\HP\Desktop\RetroManiaBot\\video5222363972019193456.mp4"
    bot.send_video(message.chat.id, open(video_path, 'rb'))
    bot.send_message(message.chat.id, 'Welcome to Retromania! Please select an option:', reply_markup=markup)


# Menu command
@bot.message_handler(func=lambda message: message.text == 'MENU')
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Coffee')
    btn2 = types.KeyboardButton('Tea')
    btn3 = types.KeyboardButton('Food')
    btn4 = types.KeyboardButton('BACK')
    markup.add(btn1, btn2, btn3, btn4)
    bot.send_message(message.chat.id, 'Select a category:', reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in ['Coffee', 'Tea', 'Food'])
def show_category_items(message):
    category = message.text
    conn = sqlite3.connect('menu.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, price FROM menu WHERE category = ?', (category,))
    items = cursor.fetchall()
    conn.close()

    if items:
        response = f'{category} Menu:\n'
        markup = types.InlineKeyboardMarkup()

        for item in items:
            btn1 =  types.InlineKeyboardButton(
            text=f'{item[0]}: {item[1]}AMD\n', callback_data=f"order_{item[0]}")
            markup.add(btn1)
        bot.send_message(message.chat.id, response, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, f'No items found in the {category} category.')


@bot.message_handler(func=lambda message: message.text == "BARISTA")
def Barista(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('GOOD')
    btn2 = types.KeyboardButton('BAD')
    btn3 = types.KeyboardButton('BACK')
    markup.add(btn1, btn2, btn3)
    bot.send_message(
        message.chat.id,
        "Hello, I'm your assistant barista. My main goal is to help you choose food or drinks according to your mood. Tell me, what's your mood today? 😊",
        reply_markup=markup
    )


# Answer based on mood
@bot.message_handler(func=lambda message: message.text in ["GOOD", "BAD"])
def answer(message):
    mood = message.text.lower()

    cursor.execute("SELECT name, category, price FROM menu WHERE mood = ?", (mood,))
    items = cursor.fetchall()
    print(items)

    if items:
        coffee_items = [item for item in items if item[1] == "Coffee"]
        tea_items = [item for item in items if item[1] == "Tea"]
        food_items = [item for item in items if item[1] == "Food"]

        random_coffee = random.choice(coffee_items) if coffee_items else None
        random_tea = random.choice(tea_items) if tea_items else None
        random_food = random.choice(food_items) if food_items else None

        markup = types.InlineKeyboardMarkup()
        if random_coffee:
            btn1 = types.InlineKeyboardButton(
                text=f"{random_coffee[0]} - {random_coffee[2]} AMD", callback_data=f"order_{random_coffee[0]}"
            )
            markup.add(btn1)
        if random_tea:
            btn2 = types.InlineKeyboardButton(
                text=f"{random_tea[0]} - {random_tea[2]} AMD", callback_data=f"order_{random_tea[0]}"
            )
            markup.add(btn2)
        if random_food:
            btn3 = types.InlineKeyboardButton(
                text=f"{random_food[0]} - {random_food[2]} AMD", callback_data=f"order_{random_food[0]}"
            )
            markup.add(btn3)

        bot.send_message(
            message.chat.id,
            f"If you want coffee, I recommend: {random_coffee[0]} - {random_coffee[2]} AMD if available.\n"
            f"If you want tea, I recommend: {random_tea[0]} - {random_tea[2]} AMD if available.\n"
            f"If you're hungry, I recommend: {random_food[0]} - {random_food[2]} AMD if available.",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "Sorry, I couldn't find any items for your mood.")
def generate_order_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


@bot.callback_query_handler(func=lambda call: call.data.startswith("order_"))
def order(callback):
    item_name = callback.data.split("_")[1]
    bot.send_message(callback.message.chat.id, f"How many {item_name} would you like to order?")

    bot.register_next_step_handler(callback.message, get_quantity, item_name)


def get_quantity(message, item_name):
    try:
        quantity = int(message.text)
        if quantity <= 0:
            bot.send_message(message.chat.id, "Please enter a valid positive number.")
            bot.register_next_step_handler(message, get_quantity, item_name)
            return

        user_id = message.chat.id
        order_code = generate_order_code()
        order_status = 'Pending'

        cursor.execute(
            'INSERT INTO orders (order_code, items, user_id, order_status, quantity) VALUES (?, ?, ?, ?, ?)',
            (order_code, item_name, user_id, order_status, quantity)
        )
        conn.commit()

        bot.send_message(
            message.chat.id,
            f"You have ordered {quantity} x {item_name}. Your order code is: {order_code}."
        )
    except ValueError:
        bot.send_message(message.chat.id, "Please enter a valid number.")
        bot.register_next_step_handler(message, get_quantity, item_name)


@bot.message_handler(func=lambda message: message.text == 'MY ORDERS')
def show_orders(message):
    user_id = message.chat.id

    cursor.execute('SELECT order_code, items, quantity FROM orders WHERE user_id = ?  AND order_status = ?', (user_id,'Pending'))
    orders = cursor.fetchall()

    if orders:
        response = "Your Orders:\n"
        markup = types.InlineKeyboardMarkup()

        for order in orders:
            order_code, item, quantity = order
            response += f"Order Code: {order_code}, Item: {item}, Quantity: {quantity}\n"
            btn = types.InlineKeyboardButton(f"Cancel Order {order_code}", callback_data=f"Cancel_{order_code}")
            markup.add(btn)

        bot.send_message(message.chat.id, response, reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "You have no active orders.")



@bot.callback_query_handler(func=lambda call: call.data.startswith('Cancel_'))
def cancel_order(callback):
    print(f"Received callback data: {callback.data}")
    order_code = callback.data.split('_')[1]
    user_id = callback.message.chat.id

    cursor.execute('SELECT * FROM orders WHERE user_id = ? AND order_code = ? AND order_status = ?', (user_id, order_code,'Pending'))
    order = cursor.fetchone()

    if order:
        cursor.execute('UPDATE orders SET order_status = ? WHERE user_id = ? AND order_code = ?', ('Close', user_id, order_code))
        conn.commit()

        bot.send_message(callback.message.chat.id, f'Your order with code {order_code} has been canceled.')
    else:
        bot.send_message(callback.message.chat.id, 'Order not found or already canceled.')




@bot.message_handler(func=lambda message: message.text == "BACK")
def back(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton("MENU")
    item1 = types.KeyboardButton("BARISTA")
    item2 = types.KeyboardButton("MY ORDERS")
    btn3 = types.KeyboardButton('CONTACT INFO')
    markup.add(item, item1,item2, btn3)
    bot.send_message(message.chat.id, "Select which section you want to return to.", reply_markup=markup)



@bot.message_handler(func=lambda message: message.text == 'CONTACT INFO')
def contact_info(message):
    bot.send_message(message.chat.id, 'Phone: +374xxxxxxxx')
    bot.send_message(message.chat.id, 'Instagram: http://surl.li/mlcpgo')


bot.infinity_polling()

