#--import libraries/загружаем библиотеки--
#version: 2.1

import requests
import os
import time
import re


#--ASCII color/ANSI цвета--
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"

#--ASCII logo/ASCII лого--
ascii_art = f"""
{GREEN}PPPP{RESET}    {BLUE}V{RESET}   {BLUE}V{RESET}   {BLUE}K{RESET}   {BLUE}K{RESET}
{GREEN}P   P{RESET}   {BLUE}V{RESET}   {BLUE}V{RESET}   {BLUE}K{RESET}  {BLUE}K{RESET}
{GREEN}PPPP{RESET}    {BLUE}V{RESET}   {BLUE}V{RESET}   {BLUE}KKK{RESET}
{GREEN}P{RESET}       {BLUE}V{RESET} {BLUE}V{RESET}     {BLUE}K{RESET}  {BLUE}K{RESET}
{GREEN}P{RESET}        {BLUE}V{RESET}      {BLUE}K{RESET}   {BLUE}K{RESET}
"""

#--set version/назначяем версию--
version = '5.131'

#--print ASCII logo/вывод ASCII лого--
print(ascii_art)

#--Language selection/Выбор языка--
lang = input("Choose language/Выберите язык (en/ru):").strip().lower()
if lang not in ['en', 'ru']:
    lang = 'en'

#--Messages dictionary/Словарь сообщений--
messages = {
    'en': {
        'enter_user_id': "Enter VK user ID (example: 4225252): ",
        'enter_token': "Enter VK access token: ",
        'starting_download': "\n[+] Starting download for user: {}",
        'fetching_standard_albums': "\n[+] Fetching standard albums...",
        'album': " → Album: {}",
        'fetching_system_albums': "\n[+] Fetching system albums...",
        'fetching_wall_photos': "\n[+] Fetching wall post photos...",
        'all_done': "\nAll photos downloaded successfully!",
        'vk_api_error': "[VK API Error] {}",
        'request_error': "[Request Error] {}",
        'download_error': "[Download Error] {}: {}"
    },
    'ru': {
        'enter_user_id': "Введите ID пользователя VK (пример: 4225252): ",
        'enter_token': "Введите access token VK: ",
        'starting_download': "\n[+] Начинаем загрузку для пользователя: {}",
        'fetching_standard_albums': "\n[+] Получаем стандартные альбомы...",
        'album': " → Альбом: {}",
        'fetching_system_albums': "\n[+] Получаем системные альбомы...",
        'fetching_wall_photos': "\n[+] Получаем фото со стены...",
        'all_done': "\nВсе фото успешно загружены!",
        'vk_api_error': "[Ошибка VK API] {}",
        'request_error': "[Ошибка запроса] {}",
        'download_error': "[Ошибка скачивания] {}: {}"
    }
}

#--Input/Ввод данных--
user_id = input(messages[lang]['enter_user_id']).strip()
access_token = input(messages[lang]['enter_token']).strip()

#--Helpers/Вспомогательные функции--
def clean_filename(name):
    # Clean file/folder names from invalid characters
    # Очищаем имя файла/папки от недопустимых символов
    return re.sub(r'[\\/:"*?<>|]+', '_', name)

def vk_api_request(method, params):
    # Perform VK API request with error handling
    # Выполняем запрос к VK API с обработкой ошибок
    url = f"https://api.vk.com/method/{method}"
    params.update({'access_token': access_token, 'v': version})
    try:
        response = requests.get(url, params=params).json()
        if 'error' in response:
            print(messages[lang]['vk_api_error'].format(response['error']['error_msg']))
            return None
        return response['response']
    except Exception as e:
        print(messages[lang]['request_error'].format(e))
        return None

def get_user_name(user_id):
    # Get user's full name from VK
    # Получаем имя и фамилию пользователя из VK
    response = vk_api_request('users.get', {'user_ids': user_id})
    if response and len(response) > 0:
        user = response[0]
        full_name = f"{user.get('first_name', '')}_{user.get('last_name', '')}"
        return clean_filename(full_name)
    return str(user_id)

def download_photo(url, folder, filename):
    # Download photo and save to folder
    # Скачиваем фото и сохраняем в папку
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, clean_filename(filename))
    try:
        img = requests.get(url).content
        with open(path, 'wb') as f:
            f.write(img)
    except Exception as e:
        print(messages[lang]['download_error'].format(filename, e))

#--Logic/Основная логика--
def get_albums(user_id):
    # Get user albums
    # Получаем альбомы пользователя
    response = vk_api_request('photos.getAlbums', {'owner_id': user_id})
    return response['items'] if response else []

def get_photos(owner_id, album_id):
    # Get photos from album
    # Получаем фото из альбома
    response = vk_api_request('photos.get', {
        'owner_id': owner_id,
        'album_id': album_id,
        'photo_sizes': 1,
        'count': 1000
    })
    return response['items'] if response else []

def get_wall_photos(owner_id):
    # Get photos from wall posts
    # Получаем фото из постов на стене
    photos = []
    offset = 0
    count = 100

    while True:
        response = vk_api_request('wall.get', {
            'owner_id': owner_id,
            'offset': offset,
            'count': count,
            'filter': 'owner'
        })
        if not response:
            break
        items = response.get('items', [])
        if not items:
            break
        for post in items:
            for att in post.get('attachments', []):
                if att['type'] == 'photo':
                    photos.append(att['photo'])
        if len(items) < count:
            break
        offset += count
        time.sleep(0.34)
    return photos

def process_photos(photos, folder):
    # Download all photos from list
    # Скачиваем все фото из списка
    for i, photo in enumerate(photos):
        sizes = photo.get('sizes', [])
        if not sizes:
            continue
        url = sorted(sizes, key=lambda s: s['width'] * s['height'])[-1]['url']
        filename = f"{i+1}.jpg"
        download_photo(url, folder, filename)

#--Main execution/Основной запуск--

user_name_folder = get_user_name(user_id)
base_folder = os.path.join("parser_VK", user_name_folder)

print(messages[lang]['starting_download'].format(user_name_folder))
print(messages[lang]['fetching_standard_albums'])
albums = get_albums(user_id)
for album in albums:
    album_id = album['id']
    title = clean_filename(album['title'])
    print(messages[lang]['album'].format(title))
    folder_path = os.path.join(base_folder, title)
    photos = get_photos(user_id, album_id)
    process_photos(photos, folder_path)
    time.sleep(0.34)

print(messages[lang]['fetching_system_albums'])
system_albums = {
    'profile': 'Profile Photos',
    'wall': 'Wall Photos',
    'saved': 'Saved Photos'
}
for album_id, title in system_albums.items():
    print(messages[lang]['album'].format(title))
    folder_path = os.path.join(base_folder, clean_filename(title))
    photos = get_photos(user_id, album_id)
    process_photos(photos, folder_path)
    time.sleep(0.34)

print(messages[lang]['fetching_wall_photos'])
wall_photos = get_wall_photos(user_id)
wall_folder = os.path.join(base_folder, "Wall_Posts")
process_photos(wall_photos, wall_folder)

print(messages[lang]['all_done'])
