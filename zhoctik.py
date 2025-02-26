import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime, timedelta
import asyncio
import os

API_TOKEN = '7172571551:AAHLwDIPluMe-cOA3aMmqDmZz1zapbQLdBM'
ADMIN_CHAT_ID = 5072441946  # Замените на ID администратора

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и хранилища
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Состояния для бронирования
class Form(StatesGroup):
    choose_equipment = State()
    choose_snowboard_type = State()
    choose_ski_type = State()
    choose_cross_country_ski_type = State()
    enter_height = State()
    enter_shoe_size = State()
    choose_stance = State()
    enter_weight = State()
    add_more_equipment = State()
    enter_phone = State()
    enter_name = State()
    choose_date = State()
    choose_time = State()
    add_comment = State()
    add_photos = State()
    confirm_booking = State()

# Файл для хранения данных
DATA_FILE = "bookings.json"

# Загрузка данных из файла
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"bookings": {}, "user_bookings": {}}

# Сохранение данных в файл
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Глобальный словарь для хранения заявок
data = load_data()
bookings = data.get("bookings", {})
user_bookings = data.get("user_bookings", {})

# Начальный экран с кнопками
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Забронировать инвентарь')],
            [KeyboardButton(text='Цены проката инвентаря')],
            [KeyboardButton(text='Условия проката')],
            [KeyboardButton(text='Ski-сервис')],
            [KeyboardButton(text='Мои брони')]  # Убрали кнопку "Отменить бронь"
        ],
        resize_keyboard=True
    )
    await message.answer("Добрый день. Вас приветствует прокат SkiHouse. Здесь можно ознакомиться с ценами и забронировать необходимый инвентарь:", reply_markup=markup)

# Обработка кнопки "Мои брони"
@dp.message(lambda message: message.text == 'Мои брони')
async def show_user_bookings(message: types.Message):
    booking_id = str(message.from_user.id)
    if booking_id in user_bookings and user_bookings[booking_id]:
        for booking in user_bookings[booking_id]:
            summary_message = "Ваши брони:\n\n"
            summary_message += f"Инвентарь: {booking['equipment']}\n"
            summary_message += f"Тип: {booking.get('snowboard_type', booking.get('ski_type', booking.get('cross_country_ski_type', 'не указано')))}\n"
            summary_message += f"Дата: {booking['date']}\n"
            summary_message += f"Время: {booking['time']}\n"
            summary_message += f"Комментарий: {booking['comment']}\n"

            # Добавляем кнопку "Отменить бронь" под сообщением
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Отменить бронь", callback_data=f"cancel_{booking_id}")]
            ])
            await message.answer(summary_message, reply_markup=markup)
    else:
        await message.answer("У вас нет активных бронирований.")

# Обработка нажатия на кнопку "Отменить бронь"
@dp.callback_query(lambda c: c.data.startswith('cancel_'))
async def cancel_booking(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    booking_id = callback_query.data.split('_')[1]

    if user_id in user_bookings and user_bookings[user_id]:
        # Удаляем бронь пользователя
        canceled_booking = user_bookings.pop(user_id)
        save_data({"bookings": bookings, "user_bookings": user_bookings})  # Сохраняем данные
        await callback_query.message.answer("Ваша бронь отменена.")

        # Уведомляем администратора об отмене брони
        admin_message = (
            f"Пользователь отменил бронь:\n\n"
            f"ID пользователя: {user_id}\n"
            f"Имя: {canceled_booking[0]['name']}\n"
            f"Телефон: {canceled_booking[0]['phone']}\n"
            f"Дата: {canceled_booking[0]['date']}\n"
            f"Время: {canceled_booking[0]['time']}\n"
            f"Комментарий: {canceled_booking[0]['comment']}\n"
        )
        await bot.send_message(ADMIN_CHAT_ID, admin_message)
    else:
        await callback_query.message.answer("У вас нет активных бронирований для отмены.")

# Обработка кнопок с ссылками
@dp.message(lambda message: message.text in ['Цены проката инвентаря', 'Условия проката', 'Ski-сервис'])
async def handle_links(message: types.Message):
    if message.text == 'Цены проката инвентаря':
        url = 'https://houseprokat.ru/'
        text = "Перейдите по ссылке, чтобы узнать цены проката инвентаря:"
    elif message.text == 'Условия проката':
        url = 'https://houseprokat.ru/faq/'
        text = "Перейдите по ссылке, чтобы ознакомиться с условиями проката:"
    elif message.text == 'Ski-сервис':
        url = 'https://houseprokat.ru/ski-service/'
        text = "Перейдите по ссылке, чтобы узнать о нашем Ski-сервисе:"

    # Отправляем сообщение с предложением перейти по ссылке
    markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Перейти по ссылке", url=url)]])
    await message.answer(text, reply_markup=markup)

# Выбор инвентаря
@dp.message(lambda message: message.text == 'Забронировать инвентарь')
async def choose_equipment(message: types.Message, state: FSMContext):
    markup = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Горные лыжи')],
            [KeyboardButton(text='Сноуборд')],
            [KeyboardButton(text='Беговые лыжи')]
        ],
        resize_keyboard=True
    )
    await state.set_state(Form.choose_equipment)
    await message.answer("Какой инвентарь вы хотели бы забронировать?", reply_markup=markup)

# Обработка выбора инвентаря
@dp.message(Form.choose_equipment)
async def process_equipment(message: types.Message, state: FSMContext):
    await state.update_data(equipment=message.text)

    if message.text == 'Сноуборд':
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Комплект сноуборда (доска, крепы, ботинки)')],
                [KeyboardButton(text='Сноуборд + крепления')],
                [KeyboardButton(text='Отдельно ботинки')]
            ],
            resize_keyboard=True
        )
        await state.set_state(Form.choose_snowboard_type)
        await message.answer("Выберите тип сноуборда:", reply_markup=markup)
    elif message.text == 'Горные лыжи':
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Горные лыжи комплект (лыжи + ботинки + палки)')],
                [KeyboardButton(text='Горные лыжи + крепления')],
                [KeyboardButton(text='Отдельно ботинки')]
            ],
            resize_keyboard=True
        )
        await state.set_state(Form.choose_ski_type)
        await message.answer("Выберите тип горных лыж:", reply_markup=markup)
    else:  # Беговые лыжи
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Беговые лыжи комплект (лыжи + ботинки + палки)')],
                [KeyboardButton(text='Беговые лыжи + крепления')],
                [KeyboardButton(text='Отдельно ботинки')]
            ],
            resize_keyboard=True
        )
        await state.set_state(Form.choose_cross_country_ski_type)
        await message.answer("Выберите тип беговых лыж:", reply_markup=markup)

# Обработка выбора типа сноуборда
@dp.message(Form.choose_snowboard_type)
async def process_snowboard_type(message: types.Message, state: FSMContext):
    await state.update_data(snowboard_type=message.text)

    if message.text == 'Отдельно ботинки':
        # Если выбраны только ботинки, запрашиваем размер обуви
        await state.set_state(Form.enter_shoe_size)
        await message.answer("Введите размер обуви:")
    elif message.text == 'Сноуборд + крепления':
        # Если выбран сноуборд + крепления, пропускаем вопрос о размере обуви
        await state.set_state(Form.enter_height)
        await message.answer("Введите ваш рост (в см):")
    else:  # Комплект сноуборда (доска, крепы, ботинки)
        await state.set_state(Form.enter_height)
        await message.answer("Введите ваш рост (в см):")

# Обработка выбора типа горных лыж
@dp.message(Form.choose_ski_type)
async def process_ski_type(message: types.Message, state: FSMContext):
    await state.update_data(ski_type=message.text)

    if message.text == 'Отдельно ботинки':
        # Если выбраны только ботинки, запрашиваем размер обуви
        await state.set_state(Form.enter_shoe_size)
        await message.answer("Введите размер обуви:")
    elif message.text == 'Горные лыжи + крепления':
        # Если выбраны горные лыжи + крепления, пропускаем вопрос о размере обуви
        await state.set_state(Form.enter_height)
        await message.answer("Введите ваш рост (в см):")
    else:  # Горные лыжи комплект (лыжи + ботинки + палки)
        await state.set_state(Form.enter_height)
        await message.answer("Введите ваш рост (в см):")

# Обработка выбора типа беговых лыж
@dp.message(Form.choose_cross_country_ski_type)
async def process_cross_country_ski_type(message: types.Message, state: FSMContext):
    await state.update_data(cross_country_ski_type=message.text)

    if message.text == 'Отдельно ботинки':
        # Если выбраны только ботинки, запрашиваем размер обуви
        await state.set_state(Form.enter_shoe_size)
        await message.answer("Введите размер обуви:")
    elif message.text == 'Беговые лыжи + крепления':
        # Если выбраны беговые лыжи + крепления, пропускаем вопрос о размере обуви
        await state.set_state(Form.enter_height)
        await message.answer("Введите ваш рост (в см):")
    else:  # Беговые лыжи комплект (лыжи + ботинки + палки)
        await state.set_state(Form.enter_height)
        await message.answer("Введите ваш рост (в см):")

# Обработка роста
@dp.message(Form.enter_height)
async def process_height(message: types.Message, state: FSMContext):
    await state.update_data(height=message.text)
    data = await state.get_data()

    if data['equipment'] == 'Горные лыжи':
        await state.set_state(Form.enter_weight)
        await message.answer("Введите ваш вес (в кг):")
    elif data['equipment'] == 'Сноуборд':
        if data.get('snowboard_type') == 'Комплект сноуборда (доска, крепы, ботинки)':
            # Для комплекта сноуборда запрашиваем стойку
            await state.set_state(Form.choose_stance)
            await message.answer("Выберите стойку:", reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text='Правая')],
                    [KeyboardButton(text='Левая')],
                    [KeyboardButton(text='Универсальная (рекомендуется для новичков)')]
                ],
                resize_keyboard=True
            ))
        else:
            await state.set_state(Form.choose_stance)
            await message.answer("Выберите стойку:", reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text='Правая')],
                    [KeyboardButton(text='Левая')],
                    [KeyboardButton(text='Универсальная (рекомендуется для новичков)')]
                ],
                resize_keyboard=True
            ))
    else:  # Беговые лыжи
        await state.set_state(Form.enter_shoe_size)
        await message.answer("Введите размер обуви:")

# Обработка веса (только для горных лыж)
@dp.message(Form.enter_weight)
async def process_weight(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    data = await state.get_data()

    if data.get('ski_type') == 'Горные лыжи комплект (лыжи + ботинки + палки)':
        # Для комплекта горных лыж запрашиваем размер обуви
        await state.set_state(Form.enter_shoe_size)
        await message.answer("Введите размер обуви:")
    else:
        await state.set_state(Form.add_more_equipment)
        await message.answer("Хотите забронировать еще инвентарь?", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Забронировать еще инвентарь')],
                [KeyboardButton(text='Окончить бронирование')]
            ],
            resize_keyboard=True
        ))

# Обработка стойки (только для сноуборда)
@dp.message(Form.choose_stance)
async def process_stance(message: types.Message, state: FSMContext):
    if message.text not in ['Правая', 'Левая', 'Универсальная (рекомендуется для новичков)']:
        await message.answer("Пожалуйста, выберите стойку, используя кнопки.")
        return

    await state.update_data(stance=message.text)
    data = await state.get_data()

    if data['equipment'] == 'Сноуборд' and data.get('snowboard_type') == 'Комплект сноуборда (доска, крепы, ботинки)':
        # Для комплекта сноуборда запрашиваем размер обуви
        await state.set_state(Form.enter_shoe_size)
        await message.answer("Введите размер обуви:")
    else:
        await state.set_state(Form.add_more_equipment)
        await message.answer("Хотите забронировать еще инвентарь?", reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Забронировать еще инвентарь')],
                [KeyboardButton(text='Окончить бронирование')]
            ],
            resize_keyboard=True
        ))

# Обработка размера обуви
@dp.message(Form.enter_shoe_size)
async def process_shoe_size(message: types.Message, state: FSMContext):
    await state.update_data(shoe_size=message.text)
    await state.set_state(Form.add_more_equipment)
    await message.answer("Хотите забронировать еще инвентарь?", reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Забронировать еще инвентарь')],
            [KeyboardButton(text='Окончить бронирование')]
        ],
        resize_keyboard=True
    ))

# Обработка добавления дополнительного инвентаря
@dp.message(Form.add_more_equipment)
async def process_add_more_equipment(message: types.Message, state: FSMContext):
    if message.text == 'Забронировать еще инвентарь':
        # Сохраняем текущий комплект в список
        data = await state.get_data()
        booking_id = str(message.from_user.id)
        if booking_id not in bookings:
            bookings[booking_id] = []
        bookings[booking_id].append(data)

        # Сбрасываем состояние для нового комплекта
        await state.set_state(Form.choose_equipment)
        await choose_equipment(message, state)
    else:
        # Сохраняем последний комплект в список
        data = await state.get_data()
        booking_id = str(message.from_user.id)
        if booking_id not in bookings:
            bookings[booking_id] = []
        bookings[booking_id].append(data)

        await state.set_state(Form.enter_phone)
        await message.answer("Введите ваш номер телефона:")

# Обработка номера телефона
@dp.message(Form.enter_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(Form.enter_name)
    await message.answer("Введите ваше имя:")

# Обработка имени
@dp.message(Form.enter_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.choose_date)
    await message.answer("Введите дату когда Вы планируете взять инвентарь (в формате ДД.ММ.ГГГГ):")

# Обработка выбора даты
@dp.message(Form.choose_date)
async def process_date(message: types.Message, state: FSMContext):
    try:
        # Пытаемся преобразовать введённую дату в объект datetime
        date = datetime.strptime(message.text, "%d.%m.%Y")
        await state.update_data(date=date.strftime("%d.%m.%Y"))  # Сохраняем дату в формате строки
        await state.set_state(Form.choose_time)

        # Предлагаем выбрать время
        markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='Утро (до 12:00)')],
                [KeyboardButton(text='День (12:00-18:00)')],
                [KeyboardButton(text='Вечер (18:00 до закрытия)')]
            ],
            resize_keyboard=True
        )
        await message.answer("Выберите время бронирования:", reply_markup=markup)
    except ValueError:
        # Если формат даты неверный, сообщаем об ошибке
        await message.answer("Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГГГ.")

# Обработка выбора времени
@dp.message(Form.choose_time)
async def process_time(message: types.Message, state: FSMContext):
    await state.update_data(time=message.text)
    await state.set_state(Form.add_comment)
    await message.answer("Добавьте комментарий или нажмите кнопку продолжить:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Продолжить без комментария')]
        ],
        resize_keyboard=True
    ))

# Обработка комментария
@dp.message(Form.add_comment)
async def process_comment(message: types.Message, state: FSMContext):
    if message.text != 'Продолжить без комментария':
        await state.update_data(comment=message.text)
    else:
        await state.update_data(comment='нет')

    await state.set_state(Form.add_photos)
    await message.answer("При желании прикрепите фотографии к вашему комментарию. Если фотографий нет, нажмите 'Продолжить без фотографий'.", reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Продолжить без фотографий')]
        ],
        resize_keyboard=True
    ))

# Обработка фотографий
@dp.message(Form.add_photos)
async def process_photos(message: types.Message, state: FSMContext):
    if message.text == 'Продолжить без фотографий':
        await state.update_data(photos=[])
    else:
        if message.photo:
            photos = [photo.file_id for photo in message.photo]
            await state.update_data(photos=photos)
        else:
            await message.answer("Пожалуйста, прикрепите фотографии или нажмите 'Продолжить без фотографий'.")
            return

    data = await state.get_data()
    booking_id = str(message.from_user.id)

    # Формируем сводку данных
    summary_message = "Ваши заказы:\n\n"
    for order in bookings[booking_id]:
        # Определяем тип инвентаря в зависимости от выбранного оборудования
        if order['equipment'] == 'Сноуборд':
            equipment_type = order.get('snowboard_type', 'не указано')
        elif order['equipment'] == 'Горные лыжи':
            equipment_type = order.get('ski_type', 'не указано')
        elif order['equipment'] == 'Беговые лыжи':
            equipment_type = order.get('cross_country_ski_type', 'не указано')
        else:
            equipment_type = 'не указано'

        # Формируем строку с параметрами в зависимости от типа инвентаря
        summary_message += f"Инвентарь: {order['equipment']}\n"
        summary_message += f"Тип: {equipment_type}\n"

        if order['equipment'] == 'Горные лыжи':
            if equipment_type == 'Горные лыжи комплект (лыжи + ботинки + палки)':
                summary_message += f"Рост: {order.get('height', 'не указано')}\n"
                summary_message += f"Вес: {order.get('weight', 'не указано')}\n"
                summary_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"
            elif equipment_type == 'Горные лыжи + крепления':
                summary_message += f"Рост: {order.get('height', 'не указано')}\n"
                summary_message += f"Вес: {order.get('weight', 'не указано')}\n"
            elif equipment_type == 'Отдельно ботинки':
                summary_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"
        elif order['equipment'] == 'Сноуборд':
            if equipment_type == 'Комплект сноуборда (доска, крепы, ботинки)':
                summary_message += f"Рост: {order.get('height', 'не указано')}\n"
                summary_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"
                summary_message += f"Стойка: {order.get('stance', 'не указано')}\n"
            elif equipment_type == 'Сноуборд + крепления':
                summary_message += f"Рост: {order.get('height', 'не указано')}\n"
                summary_message += f"Стойка: {order.get('stance', 'не указано')}\n"
            elif equipment_type == 'Отдельно ботинки':
                summary_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"
        elif order['equipment'] == 'Беговые лыжи':
            if equipment_type == 'Беговые лыжи комплект (лыжи + ботинки + палки)':
                summary_message += f"Рост: {order.get('height', 'не указано')}\n"
                summary_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"
            elif equipment_type == 'Беговые лыжи + крепления':
                summary_message += f"Рост: {order.get('height', 'не указано')}\n"
            elif equipment_type == 'Отдельно ботинки':
                summary_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"

        summary_message += "\n"

    summary_message += (
        f"Телефон: {data['phone']}\n"
        f"Имя: {data['name']}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Комментарий: {data['comment']}"
    )
    await message.answer(summary_message)

    # Отправляем заявку администратору
    admin_message = "Новая заявка на бронирование:\n\n"
    for order in bookings[booking_id]:
        # Определяем тип инвентаря в зависимости от выбранного оборудования
        if order['equipment'] == 'Сноуборд':
            equipment_type = order.get('snowboard_type', 'не указано')
        elif order['equipment'] == 'Горные лыжи':
            equipment_type = order.get('ski_type', 'не указано')
        elif order['equipment'] == 'Беговые лыжи':
            equipment_type = order.get('cross_country_ski_type', 'не указано')
        else:
            equipment_type = 'не указано'

        # Формируем строку с параметрами в зависимости от типа инвентаря
        admin_message += f"Инвентарь: {order['equipment']}\n"
        admin_message += f"Тип: {equipment_type}\n"

        if order['equipment'] == 'Горные лыжи':
            if equipment_type == 'Горные лыжи комплект (лыжи + ботинки + палки)':
                admin_message += f"Рост: {order.get('height', 'не указано')}\n"
                admin_message += f"Вес: {order.get('weight', 'не указано')}\n"
                admin_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"
            elif equipment_type == 'Горные лыжи + крепления':
                admin_message += f"Рост: {order.get('height', 'не указано')}\n"
                admin_message += f"Вес: {order.get('weight', 'не указано')}\n"
            elif equipment_type == 'Отдельно ботинки':
                admin_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"
        elif order['equipment'] == 'Сноуборд':
            if equipment_type == 'Комплект сноуборда (доска, крепы, ботинки)':
                admin_message += f"Рост: {order.get('height', 'не указано')}\n"
                admin_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"
                admin_message += f"Стойка: {order.get('stance', 'не указано')}\n"
            elif equipment_type == 'Сноуборд + крепления':
                admin_message += f"Рост: {order.get('height', 'не указано')}\n"
                admin_message += f"Стойка: {order.get('stance', 'не указано')}\n"
            elif equipment_type == 'Отдельно ботинки':
                admin_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"
        elif order['equipment'] == 'Беговые лыжи':
            if equipment_type == 'Беговые лыжи комплект (лыжи + ботинки + палки)':
                admin_message += f"Рост: {order.get('height', 'не указано')}\n"
                admin_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"
            elif equipment_type == 'Беговые лыжи + крепления':
                admin_message += f"Рост: {order.get('height', 'не указано')}\n"
            elif equipment_type == 'Отдельно ботинки':
                admin_message += f"Размер обуви: {order.get('shoe_size', 'не указано')}\n"

        admin_message += "\n"

    admin_message += (
        f"Телефон: {data['phone']}\n"
        f"Имя: {data['name']}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n"
        f"Комментарий: {data['comment']}\n"
        f"ID пользователя: {booking_id}"
    )

    # Отправляем фотографии администратору
    photos = data.get('photos', [])
    if photos:
        media_group = [InputMediaPhoto(media=photo) for photo in photos]
        await bot.send_media_group(ADMIN_CHAT_ID, media=media_group)

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_{booking_id}")],
        [InlineKeyboardButton(text="Отклонить", callback_data=f"reject_{booking_id}")]
    ])
    await bot.send_message(ADMIN_CHAT_ID, admin_message, reply_markup=markup)

    # Очищаем данные пользователя после отправки заявки
    if booking_id in bookings:
        del bookings[booking_id]

    # Сохраняем заявку пользователя
    if booking_id not in user_bookings:
        user_bookings[booking_id] = []
    user_bookings[booking_id].append(data)

    # Сохраняем данные в файл
    save_data({"bookings": bookings, "user_bookings": user_bookings})

    await state.set_state(Form.confirm_booking)
    await message.answer("Ваша заявка отправлена на рассмотрение. Ожидайте уведомления.")

    # Возвращаем пользователя на главное меню
    await cmd_start(message)

# Обработка ответа администратора
@dp.callback_query(lambda c: c.data.startswith(('confirm_', 'reject_')))
async def process_admin_response(callback_query: types.CallbackQuery):
    booking_id = callback_query.data.split('_')[1]
    user_id = int(booking_id)
    action = callback_query.data.split('_')[0]

    if action == 'confirm':
        await bot.send_message(
            user_id,
            "Ваша заявка на бронирование подтверждена!\n\n"
            "Ждём вас по адресу ул. Белорусская д 4. 1 этаж. Пункт проката SkiHouse.\n\n"
            "Напоминаем, что с собой потребуется паспорт для составления договора аренды и залог.\n"
            "В качестве залога вы можете оставить один из документов (загранпаспорт/водительское удостоверение/военный билет), либо 10000 рублей за каждый комплект.\n\n"
            "Также вы можете отменить бронь на главном меню в разделе 'Мои брони'.\n\n"
            "С уважением, команда SkiHouse!"
        )
    elif action == 'reject':
        await bot.send_message(user_id, "Ваша заявка отклонена. Пожалуйста, свяжитесь с администратором для уточнения деталей.")

    await callback_query.answer()

# Напоминание о брони за день до назначенной даты
async def send_reminder(user_id, booking):
    reminder_message =(
        "Напоминаем о вашем бронировании:\n\n"
        f"Инвентарь: {booking['equipment']}\n"
        f"Тип: {booking.get('snowboard_type', booking.get('ski_type', booking.get('cross_country_ski_type', 'не указано')))}\n"
        f"Дата: {booking['date']}\n"
        f"Время: {booking['time']}\n\n"
        "Ждём вас по адресу ул. Белорусская д 4. 1 этаж. Пункт проката SkiHouse."
    )
    await bot.send_message(user_id, reminder_message)

# Запуск напоминаний
async def schedule_reminders():
    while True:
        today = datetime.today()
        for user_id, bookings in user_bookings.items():
            for booking in bookings:
                booking_date = datetime.strptime(booking['date'], "%d.%m.%Y")
                if booking_date - timedelta(days=1) == today:
                    await send_reminder(int(user_id), booking)
        await asyncio.sleep(86400)  # Проверка каждые 24 часа

# Автоматический перезапуск бота в случае ошибок
async def start_bot():
    while True:
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Ошибка: {e}. Перезапуск бота...")
            await asyncio.sleep(5)  # Пауза перед перезапуском

if __name__ == '__main__':
    # Запуск бота с автоматическим перезапуском
    asyncio.run(start_bot())
    # Запуск напоминаний
    asyncio.create_task(schedule_reminders())