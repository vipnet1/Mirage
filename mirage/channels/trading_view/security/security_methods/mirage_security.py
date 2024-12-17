import hashlib
import json
import time
import consts
from mirage.channels.trading_view.security.security_method import SecurityMethod, SecurityMethodException
from mirage.database.mongo.common_operations import get_single_record, insert_dict


class MirageSecurityException(SecurityMethodException):
    pass


class MirageSecurity(SecurityMethod):
    CONFIG_XOR_KEYS = 'xor_keys'
    CONFIG_SECRET_KEY = 'secret_key'

    async def _perform_validation_internal(self) -> dict[str, any]:
        try:
            request_json = await self._request.json()
            decrypted_json = self._decrypt_data(request_json['request']['data'])
            decrypted_data = decrypted_json['decrypted_data']

            message_content = decrypted_data['message']
            message_hash = decrypted_data['hash']

            message = json.loads(message_content)['message']
            self._validate_hash(message_content, message_hash)
            self._validate_request_expiration(message['timenow'])
            self._validate_request_nonce(message['nonce'])

            self._insert_request_nonce(message['nonce'])

            return message['body']

        except MirageSecurityException as exc:
            raise exc
        except Exception as exc:
            raise MirageSecurityException('Exception during mirage security authentication') from exc

    def _validate_hash(self, message_content: str, message_hash: str) -> None:
        sha256_hash = hashlib.sha256()
        sha256_hash.update((message_content + self._method_config.get(MirageSecurity.CONFIG_SECRET_KEY)).encode())

        if sha256_hash.hexdigest() == message_hash:
            return

        raise MirageSecurityException('Invalid message hash')

    def _validate_request_expiration(self, timenow: int) -> None:
        current_time = int(time.time())
        time_difference = current_time - timenow / 1000

        if time_difference <= consts.MIRAGE_SECURITY_REQUEST_EXPIRATION:
            return

        raise MirageSecurityException('Request expired')

    def _validate_request_nonce(self, nonce: str) -> None:
        result = get_single_record(consts.DB_NAME_MIRAGE_SECURITY, consts.COLLECTION_REQUEST_NONCES, {'_id': nonce})
        if result is None:
            return

        raise MirageSecurityException('Nonce already exists')

    def _insert_request_nonce(self, nonce: str) -> None:
        insert_dict(consts.DB_NAME_MIRAGE_SECURITY, consts.COLLECTION_REQUEST_NONCES, {'_id': nonce})

    def _decrypt_data(self, data: str) -> dict[str, any]:
        decrypted_data = self._create_bytearray_from_data(data)
        for key in self._method_config.get(MirageSecurity.CONFIG_XOR_KEYS):
            for index, _ in enumerate(decrypted_data):
                decrypted_data[index] ^= ord(key[index % len(key)])

        content = decrypted_data.decode()
        return json.loads(content)

    def _create_bytearray_from_data(self, data: str) -> bytearray:
        numbers = data.split(',')
        return bytearray([int(number) for number in numbers])
