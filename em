#!/bin/sh
ps aux | grep 'emacs *--daemon' > /dev/null || DISPLAY='' emacs --daemon -nw --no-splash

if [ "x$1" = "x-nw" ]; then
  exec emacsclient -a "" $@
else
  exec emacsclient -a "" -nc  $@
fi

