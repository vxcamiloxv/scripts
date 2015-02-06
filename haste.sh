#!/bin/bash
haste(){ 

( echo "% $@"; eval "$@" ) | curl -F "$@=<-" http://vte.ardervegan.info/documents | awk 
-F '"' '{ print "http://vte.ardervegan.info/"$4 }'

}
