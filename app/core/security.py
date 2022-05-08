import bcrypt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_salt():
    return bcrypt.gensalt().decode()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# The secret key is used for encoding and decoding JWT strings.
# The algorithm value on the other hand is the type of algorithm used in the encoding process.
# TO GENERATE A SECRET KEY
# import os
# import binascii
# binascii.hexlify(os.urandom(24))
# b'deff1952d59f883ece260e8683fed21ab0ad9a53323eca4f'
