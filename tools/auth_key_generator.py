import secrets


def generate_api_key(length=32):
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


if __name__ == '__main__':
    print(generate_api_key())
