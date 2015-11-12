# -*- coding: utf-8 -*-
import time
import telebot
import config
import telegram

bot = telebot.TeleBot(config.token)
bot1 = telegram.Bot(config.token)


#def echo_msg(message):
 #   bot.send_message(message.chat.id, message.text)
@bot.message_handler(func=lambda message: True, content_types=['text'])
def suka_msg(message):
    # print (message.text)
        if (message.text == u"сука") or (message.text == u"Сука") :
            bot.send_message(message.chat.id, u"Сам сука")
            bot.send_message(message.chat.id, text=telegram.Emoji.PILE_OF_POO)
            bot1.sendPhoto(chat_id=message.chat.id, photo='https://encrypted-tbn1.gstatic.com/images?q=tbn:ANd9GcQ_h_mJXGtErnK_jCaZNppMf92iozTrn1SAlcjSf8e55-p7Difa')
        if (message.text == u'Привет'):
            bot.send_message(message.chat.id, u"Ну привет")
        if (message.text == u'Как дела?'):
            bot.send_message(message.chat.id, u"Было нормально пока ты не написал")
        else:
            bot.send_message(message.chat.id, u"Конечно господин " + message.from_user.first_name +u", ща всё будет!")

if __name__ == '__main__':
    bot.polling(none_stop=True)