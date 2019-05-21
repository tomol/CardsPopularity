# -*- coding:utf-8 -*-
import os

cardsList = []

files = os.listdir(r'script')

for file in files:
    f = open(r'script\\' + file, encoding='utf-8')
    line = f.readline()
    name = line.replace('--', '')
    name = name.replace('・', '')
    #name = name.replace('－', '')
    cardsList.append(name)

f.close()

fw = open('cardListReplaced.txt', 'w', encoding='utf-8')
fw.writelines(cardsList)