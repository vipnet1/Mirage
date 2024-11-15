class TelegramAliases:
    def __init__(self):
        self.aliases = {
            'terminate': 'update-config\nexecution\n{"terminate": true}',
            'suspend': 'update-config\nexecution\n{"suspend": true}',
            'unsuspend': 'update-config\nexecution\n{"suspend": false}',
        }
