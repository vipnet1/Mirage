import random
import secrets


def generate_key(length=64):
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_key_random_length():
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(secrets.choice(alphabet) for _ in range(random.randint(32, 64)))


if __name__ == '__main__':
    print(generate_key())
    # print(generate_key_random_length())
