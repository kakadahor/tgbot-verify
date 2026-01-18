#!/bin/bash
# Bot restart script

# ./restart.sh  -- if in the root folder
# rb            -- if not in the root folder

cd /Users/kakada/Documents/GitHub/tgbot-verify
pkill -9 -f 'bot.py'
sleep 1
source venv/bin/activate
python3 bot.py
