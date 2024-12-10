from mirage.channels.communication_channel import CommunicationChannel


async def log_and_send(log_function, communication_channel: CommunicationChannel, message):
    log_function(message)
    await communication_channel.send_message(message)
