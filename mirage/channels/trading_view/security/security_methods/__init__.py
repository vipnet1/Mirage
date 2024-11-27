from .api_key import ApiKey
from .mirage_security import MirageSecurity

enabled_security_methods = {
    'api-key': ApiKey,
    'mirage-security': MirageSecurity
}
