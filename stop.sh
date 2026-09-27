#!/bin/zsh
# Stop everything start.sh started.
cd "${0:A:h}"
for name in brain bot screen awake; do
  if [[ -f logs/run/$name.pid ]] && kill $(cat logs/run/$name.pid) 2>/dev/null; then
    echo "  $name stopped"
  fi
  rm -f logs/run/$name.pid
done
pkill -f "user-data-dir=$PWD/logs/run/chrome-dogscreen" && echo "  dog screen window closed"
true
