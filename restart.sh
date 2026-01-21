#!/bin/bash
# Bot restart script

# ./restart.sh  -- if in the root folder
# rb            -- if not in the root folder

cd /Users/kakada/Documents/GitHub/tgbot-verify
# Kill any existing bot processes
# Using more specific matching to avoid killing the script itself
PROCESS_NAME="bot.py"
PIDS=$(pgrep -f "$PROCESS_NAME")
if [ ! -z "$PIDS" ]; then
    echo "Found existing $PROCESS_NAME processes: $PIDS. Killing..."
    kill -9 $PIDS 2>/dev/null
fi
sleep 2
source venv/bin/activate
pip install -r requirements.txt
python3 bot.py
