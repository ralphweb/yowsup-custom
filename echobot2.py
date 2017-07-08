#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.
"""
This Bot uses the Updater class to handle the bot.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from pymongo import MongoClient
import datetime
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    update.message.reply_text('Bienvenido a Vértigo. Soy ISA y estoy esperando tu voto.')
    vote(bot, update)

def vote(bot, update):
    number = update.message.chat.id
    message = update.message.text
    name = update.message.chat.first_name+" "+update.message.chat.last_name

    currentCampaign = campaign.find_one({"active":True})
    if currentCampaign==None:
        update.message.reply_text("VOTACIÓN CERRADA. Atento a los resultados en tu televisor y recuerda seguirme en Twitter @ISA_Vertigo. Gracias por participar.")
    else:
        votes = whatsapp.find_one({"$and":[{"number": number},{"vote":True},{"campaign":currentCampaign["token"]}]})
        if votes==None:
            keyboard = []
            boton = []
            i = 0;

            for invitado in invitados:
                boton.append(InlineKeyboardButton(invitado, callback_data=invitado+"@@"+currentCampaign["token"]))
                i += 1
                if(i%1==0):
                    keyboard.append(boton)
                    boton = []
            if boton:
                keyboard.append(boton)

            reply_markup = InlineKeyboardMarkup(keyboard)
            bot.sendPhoto(chat_id=update.message.chat_id, photo=currentCampaign["image"])
            update.message.reply_text('Elige a tu eliminado:', reply_markup=reply_markup)
        else:
            update.message.reply_text("Sólo puedes votar 1 vez. Por favor espera la próxima votación. Tu último voto fue por "+votes["topic"].encode('utf8'))

def help(bot, update):
    update.message.reply_text('Ayuda pendiente!')

def echo(bot, update):
    number = update.message.chat.id
    message = update.message.text
    name = update.message.chat.first_name+" "+update.message.chat.last_name

    if message.find('#')!=-1:
        #Contiene hashtag, puede ser voto
        isVote = False
        topicFound = ""
        cant = 0
        for topic in topiclist:
             if message.lower().find(topic[1].lower())!=-1:
                isVote = True
                cant += 1
                topicFound = topic[0]
        if isVote:  
            if cant>1:
                #Tiene mas de un voto a la vez
                update.message.reply_text("Sólo puedes votar por 1 participante a la vez. Por favor elige uno y vuelve a intentar")
                msg = {"name": name,"number": number,"text": message,"vote":False,"date": datetime.datetime.utcnow()}
                whatsapp.insert_one(msg)  
            else:
                currentCampaign = campaign.find_one({"active":True})

                if currentCampaign==None:
                    update.message.reply_text("CIERRE DE VOTACIÓN. Atento a los resultados en tu televisor y recuerda seguirme en Twitter @ISA_Vertigo. Gracias por participar.")
                    msg = {"name": name,"number": number,"text": message,"vote":False,"date": datetime.datetime.utcnow()}
                    whatsapp.insert_one(msg)
                else:
                    votes = whatsapp.find_one({"$and":[{"number": number},{"vote":True},{"campaign":currentCampaign["token"]}]})
                    if votes==None:
                        update.message.reply_text("Hemos recibido tu voto. Gracias por participar 👍🏻")
                        msg = {"name": name,"number": number,"text": message,"vote":True,"campaign":currentCampaign["token"],"topic":topicFound,"date": datetime.datetime.utcnow()}
                        whatsapp.insert_one(msg)
                    else:
                        update.message.reply_text("Sólo puedes votar 1 vez. Por favor espera la próxima votación. Tu último voto fue por "+votes["topic"].encode('utf8'))
                        msg = {"name": name,"number": number,"text": message,"vote":False,"date": datetime.datetime.utcnow()}
                        whatsapp.insert_one(msg)
                
        else:        
            vote(bot,update)
    else:
        msg = {"name": name,"number": number,"text": message,"vote":False,"date": datetime.datetime.utcnow()}
        whatsapp.insert_one(msg)

def button(bot, update):
    query = update.callback_query
    number = query.message.chat.id
    name = query.message.chat.first_name+" "+query.message.chat.last_name
    queryData = query.data.split("@@")
    currCampaign = queryData[1]
    selection = queryData[0]

    bot.edit_message_text(text="Hemos recibido tu voto. Gracias por participar. Votaste por %s" % selection,
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id)
    msg = {"name": name,"number": number,"text": selection,"vote":True,"campaign":currCampaign,"topic":selection,"date": datetime.datetime.utcnow()}
    whatsapp.insert_one(msg)

def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


def main():
    global client 
    client = MongoClient('mongodb://localhost:27017/')
    global db 
    db = client.whatsapp
    global whatsapp 
    whatsapp = db.messages
    global campaign 
    campaign = db.campaign
    global topics 
    topics = db.topics

    global topiclist
    topiclist = []
    global invitados
    invitados = []

    for topic in topics.find():
        if topic["active"]:
            invitados.append(topic["hash"])
            for keyword in topic["keywords"]:
                topiclist.append([topic["hash"],keyword])

    # Create the EventHandler and pass it your bot's token.
    updater = Updater("350668229:AAEtUeL6UuJ0edx_ny9FuBpkc7vqDPCGEjI")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CallbackQueryHandler(button))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
