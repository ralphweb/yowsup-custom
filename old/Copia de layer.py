# -*- coding: utf-8 -*-
from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities     import DownloadableMediaMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
from pymongo import MongoClient
import datetime


class EchoLayer(YowInterfaceLayer):
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

    @ProtocolEntityCallback("message")
    def onMessage(self, messageProtocolEntity):
        #send receipt otherwise we keep receiving the same message over and over
        
        if True:
            receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), 'read', messageProtocolEntity.getParticipant())
            
            if messageProtocolEntity.getType()=='text':
                number = messageProtocolEntity.getFrom().split('@')[0]
                if messageProtocolEntity.getBody().find('#')!=-1:
                    #Contiene hashtag, puede ser voto
                    isVote = False
                    topicFound = ""
                    cant = 0
                    for topic in topiclist:
                         if messageProtocolEntity.getBody().lower().find(topic[1].lower())!=-1:
                            isVote = True
                            cant += 1
                            topicFound = topic[0]
                    if isVote:  
                        if cant>1:
                            #Tiene mas de un voto a la vez
                            outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                                "Sólo puedes votar por 1 participante a la vez. Por favor elige uno y vuelve a intentar",
                                to = messageProtocolEntity.getFrom())
                            self.toLower(outgoingMessageProtocolEntity)
                            msg = {"name": messageProtocolEntity.getNotify(),"number": number,"text": messageProtocolEntity.getBody(),"vote":False,"date": datetime.datetime.utcnow()}
                            whatsapp.insert_one(msg)  
                        else:
                            currentCampaign = campaign.find_one({"active":True})

                            if currentCampaign==None:
                                outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                                        "❌ CIERRE DE VOTACIÓN. Atento a los resultados en tu televisor y recuerda seguirme en Twitter @ISA_Vertigo. Gracias por participar.",
                                        to = messageProtocolEntity.getFrom())
                                msg = {"name": messageProtocolEntity.getNotify(),"number": number,"text": messageProtocolEntity.getBody(),"vote":False,"date": datetime.datetime.utcnow()}
                                whatsapp.insert_one(msg)
                            else:
                                votes = whatsapp.find_one({"$and":[{"number": number},{"vote":True},{"campaign":currentCampaign["token"]}]})
                                if votes==None:
                                    outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                                        "Hemos recibido tu voto. Gracias por participar 👍🏻",
                                        to = messageProtocolEntity.getFrom())
                                    msg = {"name": messageProtocolEntity.getNotify(),"number": number,"text": messageProtocolEntity.getBody(),"vote":True,"campaign":currentCampaign["token"],"topic":topicFound,"date": datetime.datetime.utcnow()}
                                    whatsapp.insert_one(msg)
                                else:
                                    outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                                        "Sólo puedes votar 1 vez. Por favor espera la próxima votación. Tu último voto fue por "+votes["topic"].encode('utf8'),
                                        to = messageProtocolEntity.getFrom())
                                    msg = {"name": messageProtocolEntity.getNotify(),"number": number,"text": messageProtocolEntity.getBody(),"vote":False,"date": datetime.datetime.utcnow()}
                                    whatsapp.insert_one(msg)
                            self.toLower(outgoingMessageProtocolEntity)
                    else:        
                        invitadoslist = ', '.join(invitados)
                        outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                            "Recuerda votar por uno de los invitados: "+invitadoslist,
                            to = messageProtocolEntity.getFrom())
                        self.toLower(outgoingMessageProtocolEntity)
                        msg = {"name": messageProtocolEntity.getNotify(),"number": number,"text": messageProtocolEntity.getBody(),"vote":False,"date": datetime.datetime.utcnow()}
                        whatsapp.insert_one(msg)
                else:
                    msg = {"name": messageProtocolEntity.getNotify(),"number": number,"text": messageProtocolEntity.getBody(),"vote":False,"date": datetime.datetime.utcnow()}
                    whatsapp.insert_one(msg)                
                
                print messageProtocolEntity.getFrom(),messageProtocolEntity.getBody()
            elif messageProtocolEntity.getType()=='media':
                outgoingMessageProtocolEntity = TextMessageProtocolEntity(
                    "Lo siento, no estamos recibiendo archivos",
                    to = messageProtocolEntity.getFrom())
                self.toLower(outgoingMessageProtocolEntity)
                print 'media message'
            
            self.toLower(receipt)

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", entity.getType(), entity.getFrom())
        self.toLower(ack)