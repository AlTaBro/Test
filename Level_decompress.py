
import zlib
import re
import os
from _datetime import datetime

file_in_dir = []
path_for_search = "/home/user/Загрузки/БУЭ УП2/"

for (dirpath, dirnames, filenames) in os.walk(path_for_search):
    for f in filenames:
        if os.path.splitext(f)[1] == '.level':
            print(f)
            file_in_dir.append(dirpath + '/' + f)

print('Найдено {}!'.format(len(file_in_dir)))

for each_file in file_in_dir:
    print('\r\n--------------------------------------------------------------------------------------------------\r\n')
    file = open(each_file, "rb")
    data = file.read()
    file.close()
    print(data)
    decompress = zlib.decompress(data)
    text = decompress.decode('utf-8')
    print(text)

    split_text = re.split(',|;|\n', text)
    print(split_text)

    result = int(split_text[3], 16)
    print(datetime.fromtimestamp(result))
    result = int(split_text[4], 16)
    print('{} м'.format(result/1000))
    result = int(split_text[5], 16)
    print('{} градусов Цельсия'.format((result/10)-52))
    print('\r\n--------------------------------------------------------------------------------------------------\r\n')



