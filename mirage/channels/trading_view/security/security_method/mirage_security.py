from fastapi import Request


class MirageSecurity:
    def __init__(self, request: Request):
        super().__init__(request)

    def _perform_validation_internal(self):
        return
