# NTManager

## About
A discord bot for managing your NitroType team.  

## How to run
To run the NTManager you will need to supply it with a .env file, a python 3.12 virtual environment and you must install the dependencies found in the requirements.txt file.  
The .env file must have the following structure:  
```
discord_bot_token=<Insert your Discord Bot token from the developer portal here>
operation_mode=<development or production>
dev_server_id=<optional id of your development guild / server>
```
To run the bot, just call `python src/main.py`.
