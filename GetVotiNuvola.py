#!/usr/bin/python3

import base64
import bisect
import email
import hashlib
import http.client
import io
import os
import posixpath
import re
import socket
import string
import sys
import time
import tempfile
import contextlib
import warnings
import urllib.request
import asyncio
from pyppeteer import launch
import os
import telepot
import requests
import asyncio
from telepot.loop import MessageLoop    

from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
#qui dovresti inserire il bot token per poterlo integrare con la api di telegram (per creare un bot di telegram devi usare @BotFather)
bot_token = ''
#qui dovreste inserire le vostre credenziali 
os.environ['nuvola_username'] = ""
os.environ['nuvola_password'] = ""
bot = telepot.Bot(bot_token)

state = ["", False]

page = None
browser = None
loggedin = False

async def login(): 
    global browser
    global page
    global loggedin 
    
    if loggedin == False:   
    
        browser=await launch(options={'args': ['--no-sandbox']})
        page = await browser.newPage()
        time.sleep(1) 
        #questa parte serve a dire al pyppeteer dove andare  
        await page.goto('https://nuvola.madisoft.it/login')
        time.sleep(1)
        #tutti questi time sleep servono a far funzionare sempre il login, ogni tanto se è troppo veloce è possibile che non registri le credenziali
        await page.type('#username',os.environ['nuvola_username'],{'delattr': 300})
        time.sleep(1)
        await page.type('#password',os.environ['nuvola_password'],{'delattr': 300})
        time.sleep(2)
        await page.click('button')
        loggedin = True 
        time.sleep(1)
        
async def get_voti(query):
    await login()

   
    await page.goto('https://nuvola.madisoft.it/area_tutore/voto/situazione')
    time.sleep(1)
    #qui dovreste mettere i chatID delle chat dove volete che il bot possa mandare messaggi, per vedere i chat id prima bisogna mandare un messaggio
    #al bot che si stà creando e andare su https://api.telegram.org/bot<inserirequiilbottoken)/getUpdates
    chats = [''] 
    try: 
        #questa parte serve a fargli prendere i voti, materie e colonne 
        materie = await page.querySelectorAll('tbody th')
        voti = await page.querySelectorAll ('tbody td')
        head = await page.querySelectorAll ('thead th')
        ncol = len(head)
        print("test" + str(ncol))
                                                                
        mats = []
        #time.sleep(3)
        for materia in materie:
            mat = await page.evaluate('(element) => element.textContent', materia)
            mats.append(mat)
        indiceMateria = mats.index(query)
        

        votiFloat = []   
        for i in range(indiceMateria*ncol, (indiceMateria+1)*ncol):
            voto = voti[i]    
            vo = await page.evaluate ('(element) => element.textContent', voto)
            vo = vo.strip()[6:].replace("½",".5")
            vo = vo.replace("+",".25")
            vo = vo.replace("-","")
            
            try:
                votiFloat.append(float(vo))
                print (vo)
            except:
                a=0

        print ("Media: ")
           

            #questa parte serve a fargli calcolare e scrivere la media dei voti 
        try:
            Media_voti = int(sum(votiFloat) / len(votiFloat))
        except ZeroDivisionError:
            Media_voti = 0
        text = 'La media di '+query +": " + str(Media_voti)
        voti = ''
        for v in votiFloat:
            voti = voti + str(v) + "  "

        for chatId in chats:
            telegram_bot_sendtext(chatId, Media_voti, text + ' voti: ' + voti)
    except ValueError:
        for chatId in chats:
    #questa parte serve a non far crashare il codice se cambiano il nome di una materia 
            telegram_bot_sendtext(chatId, '', 'la materia non è presente su nuvola')
    #await browser.close() 

def on_callback_query(msg):

    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('Callback Query:', query_id, from_id, query_data)

    bot.answerCallbackQuery(query_id, text='Got it')
    state[0] = query_data
    
    

    #questa parte serve ad fargli prendere gli input da un bot di telegram 
def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    print(msg.keys())
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                   [InlineKeyboardButton(text='Italiano', callback_data='ITALIANO')],
                   [InlineKeyboardButton(text='Matematica', callback_data='MATEMATICA')],
                   [InlineKeyboardButton(text='Inglese', callback_data='INGLESE')],
                   [InlineKeyboardButton(text='Diritto ed economia', callback_data='DIRITTO ED ECONOMIA')],
                   [InlineKeyboardButton(text='Biologia e scienze della terra', callback_data='SCI. INT. SC. TERRA E BIOLOGIA')],
                   [InlineKeyboardButton(text='Chimica', callback_data='SCI. INT. CHIMICA')],
                   [InlineKeyboardButton(text='Fisica', callback_data='SCI. INT. FISICA')],
                   [InlineKeyboardButton(text='TRG', callback_data='TECNOLOGIE E TECNICHE DI RAPPRESENTAZIONE GRAFICA')],
                   [InlineKeyboardButton(text='Informatica', callback_data='SCIENZE E TECNOLOGIE APPLICATE')],
                   [InlineKeyboardButton(text='Motoria', callback_data='SCIENZE MOTORIE E SPORTIVE')],
                   #potete usare la linea commentata sottostante per aggiungere altre materie (se ne avete altre)
                   #[InlineKeyboardButton(text='nomemateria', callback_data='nomemateria sul sito')],
            ])
    if content_type == 'text':
        if msg["text"] == '/start':
            bot.sendMessage(chat_id, 'ok, ora dimmi la materia di cui vuoi sapere voti e media', reply_markup=keyboard)

def telegram_bot_sendtext(bot_chatID, bot_message, testo):
      send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text='+testo
      response = requests.get(send_text)
      return response.json()

async def main(state):
    print('Listening ...') 
  
    MessageLoop(bot, {'chat': on_chat_message,
                  'callback_query': on_callback_query}).run_as_thread()
    
    while 1:
        currentQuery = state[0]
        running = state[1]
        if running != True and currentQuery != "":
            state[1] = True
            print (currentQuery)
            await get_voti(currentQuery)
            state[0] = ""
            state[1] = False

    #   await page.screenshot({'path': 'example.png'})

    

asyncio.get_event_loop().run_until_complete(main(state))
