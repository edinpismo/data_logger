#!/usr/bin/python3.7

import socket
from glob import glob
from os import remove
from time import sleep

sleep(12)

#set absolute path of this script
MAIN='/absolute/script/path'
#set absolute path of directory where data stored
DATA='/absolute/data/path'
#set IP and port of server to send to
ADDR=('IP', port)

SIZE=1024
FileList=glob(f'{DATA}/*')
if len(FileList)>0:
    for fajl in FileList:
        try:
            client_connection=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_connection.connect(ADDR)
            with open(fajl, "rb") as file4send:
                while True:
                    bytes_read = file4send.read(SIZE)
                    if not bytes_read:
                        break
                    client_connection.send(bytes_read)
            remove(fajl)
            client_connection.close()
        except:
            client_connection.close()
exit()
