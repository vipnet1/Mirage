from fastapi import Request


class MirageSecurity:
    def __init__(self, request: Request):
        super().__init__(request)

    async def _perform_validation_internal(self) -> dict[str, any]:
        raise Exception('yey')
