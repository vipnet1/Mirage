# Server Security #
As mirage does trading operations, in our interests to protect it.
For that you need to configure everything correctly.

## Simple Operations ##
- Https only. Mirage should accept https traffic only
- Whitelist ips. Tradingview has known ips it can trigger webhooks from, put those in the whitelist and maybe your own ip for testing.
- Mirage applies rate limiting.

## What we are protecting ##
As server open to the internet for tradingview to access it, theoretically anyone can access it.
We need the following:
- Authentication. Only we can send commands to Mirage.
- Integrity. Noeone should tamper with the data.
- Encryption. To protect our strategy/keep amount of money secret. Least critical in mine opinion.

Of course, as long as we use https, building authentication method is fine.
But as humans make mistakes, and accidently may send http message. we need a way to minimize losses & easily recover from mistakes.

## Mirage Protection ##
To fulfill our protection requirements, we built multiple server validation algorithms.

### Xor HmacSha256 & Replay Protectio ###
As we need to do the encryption operations in tradingview pinescript, we are pretty limited, so we use whatever we can.
- We generate 3(or more) Xor keys, each of random size 32-64 characters.
- We generate secret 64 characters key.

The algorithm is as following:
- Generate nonce, current UNIX format time. Put it inside a message containing the nonce, time and the body to send.
- Apply HmacSha256 with the secret key to the message. Put the result alongsize the message.
- Encrypt the whole request using 3 Xor keys. Each xor applied to previous xor result.

On Mirage size we:
- Decrypt the whole content using 3 xor keys.
- Check if HmacSha256 on body with secret key indeed matches the hash provided by the client.
- Check if message with that nonce already received. If not insert it to database. If yes ignore request.
- Check if message isn't expired according to time field.

In this case we achieve:
- Authentication. Only we know the secret key. Integrity test will fail for others.
- Integrity. Changing the message or hash content will make Mirage to ignore request. 
- Encryption. Xor is debatable encryption method. But using 3 keys will make it harder to spot patterns and therefore understand content.
  Also, if https used(as it should), it includes better encryption.
- Replay protection. Malicious actor can't send same message multiple times as Mirage will reject it.

### API Key ###
As you know, doing xors and HmacSha256 when you want to test your server via postman is tricky.
For that we provide authentication method using API Key. Of course use for testing only, for production use the previous validation method.

## How To Recover From Mistakes ##
In any case, whether it's exposing the keys, sending http request to the whole internet or whatever - immediatly use terminate command to shutdown Mirage.
Now we will focus on how to recover. Let's suppose we send http request accidently.

### If we use Xor HmacSha256 ###
Mirage will reject the http request, but malicious actor can see the contents, and take it and try to embed it in https request.
He won't be able to understand the data, or change it. But he can send the request to Mirage once and the server will accept it.
He can send the request only once, whenever he wants, until you terminate Mirage & change the secret key. That's why we added
expiration to the messages to shorten this window.
The only risk here that he can send the request you already wanted to send, on unknown for you time until you or Mirage close that opportunity for him.

In this case, you should terminate Mirage, change the secret key used for HmacSha256 on tradingview & mirage configuration.

### If we use API Key ###
Request will be rejected by mirage, but attacker can see the entire body & the api key. Basically he can send any data he wants to Mirage.
You must terminate Mirage asap and replace the API Key.

## Minimal Efforts ##
The required protection is the API key at least. Https protocol protects the API key itself, and the API key protects Mirage from unauthorized access.
But of course, recommend the better protection method for production as you are dealing with finance here.

# Notes #
- TradingView pinescript can use only specific characters(ascii 32-128 I think)
- You can use key_generator file.

# Possible Future todos #
- TradingView client certificate veritication. The issue is that it is considered not easy and error prone to do this veritication on server side as need to do it manually, and often it caauses bugs/vulneraabilities. Also if want to give another ip Mirage access client certifiction verification will block it.
