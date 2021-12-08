gcc -Wall -I/usr/include/python3.8 -lpython3.8 -c client.c
gcc client.o -o client $(/usr/bin/python3.8-config --embed --ldflags)
unlink client.o