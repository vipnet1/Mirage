from mirage.strategy.strategy import Strategy


class JustBuyStrategy(Strategy):
    async def execute(self):
        print('Suppose buying...')
