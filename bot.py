# -*- coding: utf-8 -*-
import time
import telebot
import config
import telegram

# import goslate
# import urllib2
from textblob import TextBlob

bot = telebot.TeleBot(config.token)
bot1 = telegram.Bot(config.token)
# gs = goslate.Goslate()

 # bot.send_message(message.chat.id, u"Конечно господин " + message.from_user.first_name +u", ща всё будет!")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def translate_msg(message):
    try:
        if (len(message.text) > 3):
            b = TextBlob(unicode(message.text))
            if (b.detect_language() == "ru"):
                tr_text = unicode(b.translate(to="en"))
                bot.send_message(message.chat.id, tr_text)
            if (b.detect_language() == "en"):
                tr_text = unicode(b.translate(to="ru"))
                bot.send_message(message.chat.id, tr_text)
    except Exception as e:
        print (e.message)
        bot.send_message(message.chat.id, "Sorry Boss,can't translate :("
                                          " Try another message, please " +
                                          telegram.Emoji.KISSING_FACE)


#def main_msg(message):
#    if (message.text == u"сука") or (message.text == u"Сука"):
#        bot.send_message(message.chat.id, u"Сам сука")
#        bot.send_message(message.chat.id, text=telegram.Emoji.PILE_OF_POO)
#        bot1.sendPhoto(chat_id=message.chat.id, photo='https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcQ_h_mJXGtErnK_jCaZNppMf92iozTrn1SAlcjSf8e55-p7Difa')
#    if (message.text == u'Привет'):
#        bot.send_message(message.chat.id, u"Ну привет")
#    if (message.text == u'Как дела?'):
#        bot.send_message(message.chat.id, u"Было нормально пока ты не написал")

if __name__ == '__main__':
    bot.polling(none_stop=True)
