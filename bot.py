"""
Telegram bot to play game of "Cities":
- Player says some city
- Next player replies with the city which starts with the last letter of the previous city
- If there are no cities starting with this letter then it is allowed to skip to the next letter 
(from right to left)
- First who fails to reply loses the game.

Since the bot uses database of the russian Tax Office it plays in russian language only.
You can feed him any list of cities by your choice in order to customize UX. 
Just change letters (LOCAL_A, LOCAL_Z) in settings.py specific to your alphabet and list of cities.

It is made for educational reasons to explore AIOGRAM
"""

import logging
from aiogram import Bot, Dispatcher, executor, types
import creds # creds.py contains bot's token + other credentials and is added to .gitignore
import settings # constants 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    filename='bot.log', 
    level=logging.INFO
    )

# Initializing the bot
bot = Bot(token=creds.API_TOKEN)
dp = Dispatcher(bot)
# game_state = {
#	playing: bool - Is the game started?
#	cities: dict - Consists of loaded cities
#	empty_letters: list - Letters that cities can't begin with
#	city_char - Letter that user's answer/city should begin with
# }
game_state = {'playing': False}
logging.info("Bot is initialized.")


# Set of auxiliary functions

def load_cities_dict():
    # chr(1040) - 'А', chr(1072) - 'Я'
    # Use your own 'A to Z' range specific to your language in settings.py
    cities_dict = {chr(l): [] for l in range(settings.LOCAL_A, settings.LOCAL_Z + 1)}
    with open(settings.LIST_OF_CITIES, 'r', encoding='utf-8') as f_input:
        for line in f_input:
            c = line[0]
            cities_dict[c].append(line.rstrip('\n'))
    return cities_dict

def valid_city(city):
    # Checks whether we have this city or not
    return True if city[0] in game_state['cities'] and city in game_state['cities'][city[0]] else False

def find_last_char(city):
    i = -1
    while city[i] in game_state['empty_letters']:
        i -= 1
    return city[i]

def find_city_for(letter):
    return game_state['cities'][letter].pop() if game_state['cities'][letter] else '404'


# Set of available handlers

@dp.message_handler(commands=['start'])
async def start_game(message: types.Message):
    game_state['cities'] = load_cities_dict()
    game_state['playing'] = True
    game_state['city_char'] = ''
    game_state['empty_letters'] = [chr(i) for i in range(settings.LOCAL_A, settings.LOCAL_Z + 1) if not game_state['cities'][chr(i)]]
    await message.answer(settings.GAME_STARTED_MSG)

@dp.message_handler(commands=['help'])
async def show_help(message: types.Message):
    await message.answer(settings.HELP_MSG)

@dp.message_handler(commands=['stop'])
async def stop_game(message: types.Message):
    game_state['playing'] = False
    await message.answer(settings.GAME_STOPPED_MSG)

@dp.message_handler()
async def play_game(message: types.Message):
    current_city = message.text.strip().upper()
    reply_msg = ''
    # if not 'playing' in game_state.keys() or not game_state['playing']:
    if not game_state['playing']:
        await message.reply(settings.START_GAME_MSG)
    elif current_city[0] == game_state['city_char'] or game_state['city_char'] == '':
        if valid_city(current_city):
            game_state['cities'][current_city[0]].remove(current_city)
            ch = find_last_char(current_city)
            reply_msg = 'Мне на букву {} \n\n'.format(ch)
            city = find_city_for(ch)
            if city != '404':
                reply_msg += '{} \n\n'.format(city)
                game_state['city_char'] = find_last_char(city)
                reply_msg += 'Вам на букву {}'.format(game_state['city_char'])
                await message.reply(reply_msg)
            else:
                reply_msg += 'Города на букву {} закончились. Я проиграл :('.format(ch)
                stop_game(message)
                await message.reply(reply_msg)
        else:
            await message.reply(settings.MISSPELLED_OR_REPEAT_MSG)
    else:
        reply_msg = 'Вам на букву {} \n'.format(game_state['city_char'])
        reply_msg += '/stop - сдаться и завершить игру'
        await message.reply(reply_msg)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)