from mirage.config_loader.config import Config
from mirage.config_loader.config_loader import ConfigLoader
from mirage.channels.telegram.telegram_channel import TelegramChannel

def main():
    config_loader = ConfigLoader()
    configuration: Config = config_loader.load_config()

    telegram_channel: TelegramChannel = TelegramChannel(configuration)
    telegram_channel.run()
    print('test')


if __name__ == '__main__':
    main()
