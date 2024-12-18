# Mirage
## Disclaimer ##
This software is a trading software. Therefore loss of money is possible. \
Do not risk money which you are afraid to lose. Use this software at your own risk. \
The authors and all affiliates are not responsible for your trading results - whether because of trading, bugs in code, or any other reason.

You need python knowledge to understand the code. You are welcome to read the source code, build on top of it or contribute. \
: )

## What Is It ##
Mirage is a framework to help you automating all aspects of trading, except of the entry/exit conditions themselves. \
You can imagine Mirage as a middleware. External source, let's say TradingView, sends that it found an entry or exit point for trade. Mirage will actually perform the trade, manage the risk, generate logs/db records/reports so you can check trade performance.

### Features ###
- API to send trade or other commands to the broker
- API to receive commands for processing
- Generating reports on trades performance for investigation

### Why Entry & Exit signals not handled by Mirage ###
Strategies can be complex. They can include many indicators, conditions, require efficient candles processing etc. \
There are projects that will serve this purpose better than doing it via python code, for example TradingView's PineScript. \
By having external source deal with this issue, Mirage can focus on all other aspects of trading - and those are easily achievable via python code.

## The Vision ##
As we said, Mirage is a Framework.

It was built in a modular way, so you can relatively easy add brokers, commands, and strategies for processing.

The vision is that Mirage will contain different components and each trader can construct and choose the one's suit them. \
For example for channels telegram, discord, whatsapp or others. \
For entry/exit signals tradingview, external server, whatever. \
For brokers crypto brokers like Binance, or stocks like IB.

And then people can via a few lines of code modification build a version of Mirage that suits them.

The strategy itself can be kept a secret because it is not located in Mirage. It removes the incentive to hide Mirage code and can enhance contribution.

## In Practive ###
Mirage was build for personal use, with focus on integration with TradingView & Binance.

- It receives commands from TradingView PineScript to perform trade
- Manage Mirage via commands from Telegram 
- It communicates Binance to perform the needed operations
- Provides a way to check strategy performance via various commands & logging mechanisms

## Available Components ##
### Channels ###
#### Regular ####
- TradingView

#### Communication ####
- Telegram

### Databases ###
- Mongo

### Brokers ###
- Binance

### Strategy Managers ###
- Binance Strategy Manager

### Strategies ###
- BuyBtc(for simple testing purposes)
- CryptoPairTrading

# Entering The Codebase #
## Key Components ##
We will go over some important folders & concepts.
* mirage/algorithm -> Raw operations involving contacting broker. Borrowing funds, buying, selling etc.
* mirage/brokers -> The API to brokers used by the algorithms.
* mirage/channels -> What sources Mirage receives commands from & sends data to.
* mirage/config -> Handling configurations.
mirage/database -> API to different databases or storate methods.
* mirage/jobs -> Scheduled tasks that can be run every some time.
* mirage/performance -> Generating info to investigate strategy performance and relevant metrics
* mirage/strategy -> Handles different trading commands received from some channel
* mirage/strategy_manager -> It's basically a bank. It transfers money to strategies so they can use it for trades & manages money.

## Algorithms ##
Basically different operations you can perform with brokers. Repay funds, borrow funds, perform trade, fetch amount of crypto/stocks etc.

Used by strategies & strategy managers.

## Brokers ##
Implement API to send commands to your brokers. Whether it's rest API, or just declare variable using existing python package and use it's functions, it's the place to do so.

## Channels ##
Channel used to receive information. \
CommunicationChannel to send or receive data.

For example TradingViewChannel used for receiving trade entry/exits. \
Telegram used to receive commands from user, and send different information back like report csvs.

## Config ##
As Mirage open source, you need a place to hide your secrets. That's the .config folder.

Put there API Keys, strategies configuration and other sensitive files.

It supports division to environments. For example you could have 'prod' and 'dev' environment, and configure mirage to use one or another via changing variable in consts file.

See .example_config folder for required .config folder structure.

## Performance ##
Put there logic relevant to generating data for processing to learn different insights about strategies.

## Strategy ##
It's a bit tricky, as we said there are no strategies in Mirage. And it's still correct - stuff like buy on lower bb sell on higher is not on Mirage.

So what are strategies then? those are handlers for the real strategies, like TradingView PineScript, that process their commands and perform the needed actions.

Those Mirage Strategies manage risk correctly and execute algorithms to perform trades, or simple tasks like buying some bitcoin.

Strategies have their own configuration section. Each strategy can have multiple instances, and each instance has a separate configuration file. \
For example you execute strategy A on BTC/USDT and ETH/USDT chart. You can create two strategy configuration files - one let's say btc.json and the other eth.json.

This way you can configure btc.json to have 100$ allocated for the stratgegy and eth.json 500$, you can configure that with btc you can lose up to 5% per trade and with eth 2% and so on. \
Also the profits & losses calculated for each strategy+instance separately.

Anyway the main point is that you want to have separate strategy configuration file for each chart.

## Strategy Manager ##
Mirage can handle many strategies, many trade and exit signals, thanks to Strategy Managers. \
The idea is that they are like the bank that decides whether to execute strategy, whether it's enabled, whether have funds etc.

It is responsible for transferring funds to the strategy, and from the strategy when it is finished and recording trade profits or losses.

## Storage Methods ##
Mirage stores information in two main ways: logs and database(currently mongo only).

## Other Important Concepts ##
### MirageDict ###
Just improvement on regular dict. You can do: \
`miragedict.get('abc.def.ghi')` \
instead of \
`mydict['abc']['def']['ghi']`

Some objects, like Config, inherit from MirageDict.

### Init Files ###
Many python init files include variables that enable different components, like channels, telegram commands, jobs, strategies and so on. Configure them as you wish.

# Running Mirage #
## Python Requirements ##
Mirage was tested with Python 3.9 \
It may work with older versions too - just was not tested.


## Installations ##
### Pip ###
Create python virtual environment and select it. \
Install the requirements. You need the basic one's: \
`pip install -r requirements/requirements.txt`

Then install the requirements file specific to your operating system: windows_requirements or linux_requirements.

### Database ###
Currently, Mirage offers only mongodb. \
You need to install mongodb on your local machine. \
Also, you need to install mongodb tools if you are going to use the backup telegram command. \
You may need to add mongodump command to PATH.

### Git ###
Mirage can update itself via git. For the feature to work it must be installed.

## Selecting Correct Environment ##
Set the SELECTED_ENVIRONMENT variable in consts file to your selected environment.

## Executing Mirage ##
As mirage listens on https ports, you may need administrator privileges. \
On linux: \
`sudo .venv/bin/python main.py`

## Terminating Mirage ##
Currently you can do it via:
- Pressing CTRL+C key on console
- Sending terminate command via telegram

# Using Mirage For Trading #
Will expand on how I'm using it.

Have TradingView PineScript strategy, that generates entry & exit signals. Configure alerts to send json data to Mirage.

Have Mirage running on some server accessible to the internet. Copy the production environment config there too.

I have built some TradingView libraries that help with the task on the TradingView side, like implementing the MirageSecurity protocol. They are currently not available to the public.
