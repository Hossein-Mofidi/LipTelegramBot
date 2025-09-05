# list of admins
ADMINS = [5028385009, 113385839]

# path to answers to questions
ANSWERS = 'answers.json'

# token of the robot
TOKEN = '8113470141:AAFpHhcHGXsuIoxAl5CKg7_pMoLnjtsehFo'

# Sample photos (replace with actual URLs)
PHOTOS = {
    'purple': [
        open(r'media/purple.jpg', 'rb')
    ],
    'brown': [
        open(r'media/brown.jpg', 'rb')
    ],
    'gray': [
        open(r'media/gray.jpg', 'rb')
    ],
    'intensity': {
        'low': open(r'media/purple.jpg', 'rb'),
        'medium': open(r'media/purple.jpg', 'rb'),
        'high': open(r'media/purple.jpg', 'rb')
    }
}

# Brand options
BRANDS = [
    "فیمس", "پرما", "لوکس پرما",
    "ست کارلا", "ایونفلو", "لیوایو", "حنفی"
]

# Undertone options
UNDERTONES = [
    "آمبر", "اورنج", "ورملیون",
    "رد", "کول رد"
]

# Dictionary containing solutions and photos for each challenge type
CHALLENGE_SOLUTIONS = {
    'a': {  # Purple tattoo case
        'text': "راهکار برای لب تاتوی بنفش:\n1. استفاده از کانسیلر نارنجی\n2. ترکیب رنگ X با Y\n3. لایه‌گذاری به روش Z",
        'photo': 'media/challenge_a.jpg'
    },
    'b': {  # Two-tone lips case
        'text': "راهکار برای لب دو رنگ:\n1. یکسان‌سازی رنگ با روش A\n2. استفاده از تکنیک B\n3. ترکیب خاص C",
        'photo': 'media/challenge_b.jpg'
    },
    'c': {  # Dual discoloration case
        'text': "راهکار برای دو نوع کبودی:\n1. اصلاح رنگ با ترکیب M\n2. استفاده از روش N\n3. تکنیک ویژه O",
        'photo': 'media/challenge_c.jpg'
    },
    'd': {  # Mismatched undertone case
        'text': "راهکار برای کبودی با اندرتون متفاوت:\n1. روش اصلاح P\n2. ترکیب رنگ Q\n3. تکنیک R",
        'photo': 'media/challenge_d.jpg'
    }
}

from contextlib import contextmanager

@contextmanager
def get_photo(path):
    try:
        with open(path, 'rb') as f:
            yield f
    finally:
        f.close()