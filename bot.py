# -*- coding: utf-8 -*-
import telebot
import config

from textblob import TextBlob

bot = telebot.TeleBot(config.token)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def translate_msg(message):
    try:
        if (len(message.text) > 3):
            b = TextBlob(unicode(message.text))
            if (b.detect_language() == "ru"):
                tr_text = unicode(b.translate(to="en"))
                bot.send_message(message.chat.id, tr_text)
                if tr_text is None:
                    bot.send_message(message.chat.id,
                                     "Sorry, I don't know translation."
                                     )

            elif (b.detect_language() == "en"):
                tr_text = unicode(b.translate(to="ru"))
                bot.send_message(message.chat.id, tr_text)
                if tr_text is None:
                    bot.send_message(message.chat.id,
                                     "Sorry, I don't know translation."
                                     )

            else:
                bot.send_message(message.chat.id,
                                 "Sorry, I understand only Russian and English."
                                 )
        else:
            bot.send_message(message.chat.id,
                             "Sorry, I understand only Russian and English.")
    except Exception as e:
        print (e.message)


if __name__ == '__main__':
    bot.polling(none_stop=True)
