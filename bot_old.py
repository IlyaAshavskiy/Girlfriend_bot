# -*- coding: utf-8 -*-
import time
import telebot
import config
import httplib
import urllib
import json
import datetime



#def get_instagram(latitude, longitude, distance, min_timestamp, max_timestamp, access_token):
#    get_request =  '/v1/media/search?lat=' + latitude
#    get_request+= '&lng=' + longitude
#    get_request += '&distance=' + distance
#    get_request += '&min_timestamp=' + str(min_timestamp)
#    get_request += '&max_timestamp=' + str(max_timestamp)
#    get_request += '&access_token=' + access_token
#    local_connect = httplib.HTTPSConnection('api.instagram.com', 443)
#    local_connect.request('GET', get_request)
#    return local_connect.getresponse().read()

#def get_vk(latitude, longitude, distance, min_timestamp, max_timestamp):
 #   get_request =  '/method/photos.search?lat=' + location_latitude
 #   get_request+= '&long=' + location_longitude
  #  get_request+= '&count=100'
  #  get_request+= '&radius=' + distance
  #  get_request+= '&start_time=' + str(min_timestamp)
  #  get_request+= '&end_time=' + str(max_timestamp)
  #  local_connect = httplib.HTTPSConnection('api.vk.com', 443)
  #  local_connect.request('GET', get_request)
   # return local_connect.getresponse().read()





#def echo_msg(message):
 #   bot.send_message(message.chat.id, "сука")




if __name__ == '__main__':
     bot = telebot.TeleBot(config.token)
     bot.set_update_listener(listener)
     bot.polling(none_stop=True)
    @bot.message_handler(func=lambda message: True, content_types=['text'])
    def suka_msg(message):
    # print (message.text)
        if (message.text == u"сука"):
            bot.send_mesage(message.chat.id, u"Сам сука")
        if (message.text == u'Привет'):
            bot.send_message(message.chat.id, u"Ну привет")
        if (message.text == u'Как дела?'):
            bot.send_message(message.chat.id, u"Было нормально пока ты не написал")
