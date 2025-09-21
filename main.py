# --- Import python library ---

import requests
import os
import time

# User input for VK API access
user_id = input("Enter VK user ID(example:4225252): ")
access_token = input("Enter VK access token: ")
version = '5.131'

# Base folder for saving photos
base_folder = os.path.join("parser_VK", user_id)

# Function to get user's albums
def get_albums(user_id):
    url = 'https://api.vk.com/method/photos.getAlbums'
    params = {
        'owner_id': user_id,
        'access_token': access_token,
        'v': version
    }
    response = requests.get(url, params=params).json()
    return response['response']['items']

# Function to get photos from an album (standard or system)
def get_photos(owner_id, album_id):
    url = 'https://api.vk.com/method/photos.get'
    params = {
        'owner_id': owner_id,
        'album_id': album_id,
        'access_token': access_token,
        'v': version,
        'photo_sizes': 1,
        'count': 1000
    }
    response = requests.get(url, params=params).json()
    if 'error' in response:
        print(f"Error getting photos from album '{album_id}': {response['error']['error_msg']}")
        return []
    return response['response']['items']

# Get photos from posts on user's wall
def get_wall_photos(owner_id):
    url = 'https://api.vk.com/method/wall.get'
    photos = []
    offset = 0
    count = 100

    while True:
        params = {
            'owner_id': owner_id,
            'access_token': access_token,
            'v': version,
            'count': count,
            'offset': offset,
            'filter': 'owner'
        }
        response = requests.get(url, params=params).json()

        if 'error' in response:
            print(f"Error getting photos from wall: {response['error']['error_msg']}")
            break

        items = response['response']['items']
        if not items:
            break

        for post in items:
            if 'attachments' in post:
                for att in post['attachments']:
                    if att['type'] == 'photo':
                        photos.append(att['photo'])

        if len(items) < count:
            break
        offset += count

    return photos

# Function to download photo from URL
def download_photo(url, folder, filename):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    try:
        img = requests.get(url).content
        with open(path, 'wb') as f:
            f.write(img)
    except Exception as e:
        print(f"Error downloading photo {filename}: {e}")

# --- Main logic ---

# 1. Download all standard albums
albums = get_albums(user_id)
for album in albums:
    album_id = album['id']
    title = album['title'].replace('/', '_').strip()
    print(f"Downloading album: {title}")
    folder_path = os.path.join(base_folder, title)
    photos = get_photos(user_id, album_id)
    for i, photo in enumerate(photos):
        url = sorted(photo['sizes'], key=lambda x: x['width'] * x['height'])[-1]['url']
        download_photo(url, folder_path, f"{i + 1}.jpg")

# 2. Download system albums: 'profile', 'wall', and 'saved' (if token belongs to user)
system_albums = {
    'profile': 'Profile Photos',
    'wall': 'Wall Photos',
    'saved': 'Saved Photos'
}

for sys_album_id, name in system_albums.items():
    print(f"Downloading system album: {name}")
    folder_path = os.path.join(base_folder, name)
    photos = get_photos(user_id, sys_album_id)
    for i, photo in enumerate(photos):
        url = sorted(photo['sizes'], key=lambda x: x['width'] * x['height'])[-1]['url']
        download_photo(url, folder_path, f"{i + 1}.jpg")

# 3. Download photos from wall posts
print("Downloading photos from wall posts...")
wall_photos = get_wall_photos(user_id)
wall_folder = os.path.join(base_folder, "Wall_Posts")
for i, photo in enumerate(wall_photos):
    url = sorted(photo['sizes'], key=lambda x: x['width'] * x['height'])[-1]['url']
    download_photo(url, wall_folder, f"{i + 1}.jpg")

print("All photos downloaded successfully.")
time.sleep(5)
