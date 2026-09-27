#!/bin/zsh
# Start the whole dog device and keep it live:
#   dog screen (web page) + Telegram bot + brain (camera watching) + no laptop sleep.
# Run from a terminal that has camera and mic permission:  ./start.sh
# Stop everything:  ./stop.sh      Logs: logs/run/*.log
cd "${0:A:h}"
mkdir -p logs/run
PY=.venv/bin/python

start() {  # start NAME COMMAND... unless it's already running
  local name=$1; shift
  if [[ -f logs/run/$name.pid ]] && kill -0 $(cat logs/run/$name.pid) 2>/dev/null; then
    echo "  $name already running"
  else
    nohup "$@" >> logs/run/$name.log 2>&1 &
    echo $! > logs/run/$name.pid
    echo "  $name started"
  fi
}

echo "Starting the dog device..."
start screen $PY -m http.server 8000 -d dogscreen
start bot    $PY -u -m owner.ask_bot
start brain  zsh -c "cd brain && ../$PY -u main.py"
start awake  caffeinate -di   # keep the laptop and its screen awake

# The dog screen: its own full-screen Chrome window, allowed to play sound without a tap.
if pgrep -f "user-data-dir=$PWD/logs/run/chrome-dogscreen" > /dev/null; then
  echo "  dog screen already open"
else
  open -na "Google Chrome" --args --user-data-dir="$PWD/logs/run/chrome-dogscreen" \
    --autoplay-policy=no-user-gesture-required --kiosk --no-first-run http://localhost:8000
  echo "  dog screen opened full screen (Cmd+Q in that window to close it)"
fi
echo "Stop everything: ./stop.sh"
