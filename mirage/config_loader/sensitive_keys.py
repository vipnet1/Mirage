import random
import base64


def encode(data: str) -> str:
    ascii_sum = sum(ord(char) for char in data)
    ascii_sum += random.randint(50, 150)

    result_bytes = bytearray()
    for char in data:
        xor_value = ord(char) ^ ascii_sum
        result_bytes.append(xor_value)

    return base64.b64encode(result_bytes).decode('utf-8') + f'_{str(ascii_sum)}'


def decode(data: str) -> str:
    splitted = data.split('_')
    original_data = splitted[0]
    ascii_sum = splitted[1]

    decoded_bytes = base64.b64decode(original_data)
    result = []
    for byte in decoded_bytes:
        result.append(chr(byte ^ ascii_sum))

    return ''.join(result)
