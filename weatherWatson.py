'''
 * WeatherWatson Venezuela 
  *
 * This is a small experiment of the IBM Watson's image recognition functions. 
 * This bot tries to determine the state of the sky by classifying it in one 
 * of these categories: Clear, slightly cloudy, partially cloudy, cloudy.
 * You can send it a picture of the sky where you are and the bot will do its 
 * best effort in predict how is the sky's state, the bot will respond with 
 * a voice note with its prediction.
 * You also can send it the /now command and the bot will show you how 
 * looks the sky in my town with the result of its prediction.
 *
 *  Copyright 2016 by Alfredo Chamberlain <geckotronic@gmail.com>
 *
 * This file is part of some open source application.
 * 
 * Some open source application is free software: you can redistribute 
 * it and/or modify it under the terms of the GNU General Public 
 * License as published by the Free Software Foundation, either 
 * version 3 of the License, or (at your option) any later version.
 * 
 * Some open source application is distributed in the hope that it will 
 * be useful, but WITHOUT ANY WARRANTY; without even the implied warranty 
 * of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
 *
 * @license GPL-3.0+ <http://spdx.org/licenses/GPL-3.0+>
''' 

import os
import time
import sys
import json
from os import environ
from random import randint
import telebot
from watson_developer_cloud import VisualRecognitionV3
import requests
import uuid
import urllib

#Constants
TOKEN_TELEGRAM_ID = "<TELEGRAM API KEY>"
API_WATSON_ID = "<WATSON VR API KEY>"
CLASSIFIER_ID = ["<SPECICIFC_CLASSIFIER_ID>", "default"]
API_TTS_NAME = "<WATSON_TTS_USER>"
API_TTS_PASS = "<WATSON_TTS_PASS>"
THRESHOLD = 0.90

#URL of local weather image
URL_LOCAL_IMAGE = "http://txta.me/watson/last.jpg"

# Some list data
SPECIFIC_VALID_CLASSES = {"despejado","nublado","ligeramente","parcialmente"}
GENERAL_VALID_CLASSES = {"sky","cloud", "blue sky"}

#Messages constants
englishTxt = {}
englishTxt['despejado'] = "clear"
englishTxt['nublado'] = "cloudy"
englishTxt['ligeramente'] = "slightly cloudy"
englishTxt['parcialmente'] = "partly cloudy"
englishTxt['I_CANT'] = "I can not determine the weather"
englishTxt['HELP'] = "This is a small experiment of the IBM Watson's image recognition functions." +\
						" This bot tries to determine the state of the sky by classifying it in one" +\
						" of these categories:\n\nclear\nslightly cloudy\npartially cloudy\ncloudy" +\
						"\n\nYou can send it a picture of the sky where you are and the bot will do its" +\
						" best effort in predict how is the sky's state, the bot will respond with a " +\
						"voice note with its prediction.\n\nYou also can send it the /now command and" +\
						" the bot will show you how looks the sky in my town with the result of its " +\
						"prediction.\n\nIf you want to know a little bit more about this bot's programming" +\
						" write me to geckotronic@gmail.com"
englishTxt['CMDERROR'] = "Unknown command\n" +\
						"You can send it a picture of the sky where you are and the bot will do its" +\
						" best effort in predict how is the sky's state, the bot will respond with a " +\
						"voice note with its prediction.\n\nYou also can send it the /now command and" +\
						" the bot will show you how looks the sky in my town with the result of its " +\
						"prediction."
englishTxt['RESPONSE_ONE'] = "I am in doubt if the sky is {0} or {1}, although "
englishTxt['RESPONSE_SELECTED'] = "I am almost sure the sky is {0}."
englishTxt['INVALID_IMAGE'] = "This is not the sky, it seems more like a {0}."
englishTxt['NOT_CLASSES'] = "I am can not determine what is it."
englishTxt['PROCESSING'] = "Processing..."
englishTxt['RECORDING'] = "Recording..."

def getClasses(dataClassify):
	resultList = []
	weatherCondition = dataClassify['images'][0]['classifiers']
	for allConditionValue in weatherCondition:
		print allConditionValue
		for conditionValue in allConditionValue['classes']:
			resultList.append((conditionValue['class'],conditionValue['score']))
	resultList.sort(key=lambda tup: tup[1], reverse=True)
	elements = [i[0] for i in resultList]
	status = False
	print resultList
	valid = []
	invalid = []
	for element in elements:
		if (element in SPECIFIC_VALID_CLASSES):
			valid.append(element)
		elif (element in GENERAL_VALID_CLASSES):
			status = True
		else: 
			invalid.append(element)
	response = dict()
	response['status'] = status
	if status==True:
		response['classes'] = valid
	else:
		response['classes'] = invalid
	return response

def getWeather( imgData ):
	visualRecognition = VisualRecognitionV3('2016-05-20', api_key=API_WATSON_ID)
	try:
		dataIA = visualRecognition.classify(images_file=imgData, classifier_ids=CLASSIFIER_ID, threshold=THRESHOLD)
		resultData = getClasses(dataIA)
		print "-----------"
		print resultData
		print "-----------"
		if (resultData['status']):
			if len(resultData['classes']) >= 2:
				resultText = englishTxt['RESPONSE_ONE'].format(englishTxt[resultData['classes'][0]], englishTxt[resultData['classes'][1]])
				resultText = resultText + englishTxt['RESPONSE_SELECTED'].format(englishTxt[resultData['classes'][0]])
			elif len(resultData['classes']) == 1:
				resultText = englishTxt['RESPONSE_SELECTED'].format(englishTxt[resultData['classes'][0]])
			else:
				resultText = englishTxt['I_CANT'];
		else: 
			if len(resultData['classes']) > 0:
				resultText = englishTxt['INVALID_IMAGE'].format(resultData['classes'][0])		
			else: 
				resultText = englishTxt['NOT_CLASSES']
	except:
		resultText = englishTxt['I_CANT'];
	return resultText;

def downloadFile (urlData, userName, passWord, destFilename):
	dataDownload = requests.get(urlData, auth=(userName,passWord), stream=True)
	with open(destFilename, 'wb') as fd:
	    for blockData in dataDownload.iter_content():
	        fd.write(blockData)
	return destFilename;

bot = telebot.TeleBot(TOKEN_TELEGRAM_ID)

@bot.message_handler(commands=['start', 'help'])
def sendWelcome(message):
    bot.send_message(message.chat.id, englishTxt['HELP'])

@bot.message_handler(commands=['now'])
def sendWelcome(message):
	bot.send_message(message.chat.id, englishTxt['PROCESSING'])
	uniqueFilenameImg = "/tmp/" + str(uuid.uuid4()) + "_" + os.path.basename(URL_LOCAL_IMAGE)
	downloadFile (URL_LOCAL_IMAGE, "", "", uniqueFilenameImg)
	fileData = open(uniqueFilenameImg, 'rb')
	infoTxt = getWeather(fileData)
	bot.send_photo(message.chat.id, URL_LOCAL_IMAGE+"?"+str(randint(0,99999)), infoTxt)
	os.remove(uniqueFilenameImg)

@bot.message_handler(func=lambda message: True)
def echoAll(message):
	bot.send_message(message.chat.id, englishTxt['CMDERROR'])

@bot.message_handler(content_types=['photo'])
def seePhoto(message):
	bot.send_message(message.chat.id, englishTxt['PROCESSING'])
	pathImg = bot.get_file(message.photo[-1].file_id).file_path
	urlImg = ('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN_TELEGRAM_ID, pathImg))	
	uniqueFilenameImg = "/tmp/" + str(uuid.uuid4()) + "_" + os.path.basename(pathImg)
	downloadFile (urlImg, "", "", uniqueFilenameImg)
	fileData = open(uniqueFilenameImg, 'rb')
	infoTxt = getWeather(fileData)
	bot.send_message(message.chat.id, englishTxt['RECORDING'])
	urlAudio = "https://stream.watsonplatform.net/text-to-speech/api/v1/synthesize?" +\
				"accept=audio/ogg&text=" + urllib.quote_plus(infoTxt) + "&voice=en-US_AllisonVoice"
	uniqueFilenameAudio = "/tmp/" + str(uuid.uuid4()) + ".ogg"
	downloadFile (urlAudio, API_TTS_NAME, API_TTS_PASS, uniqueFilenameAudio)
	duration = int((os.stat(uniqueFilenameAudio)).st_size / 8192)
	bot.send_voice(message.chat.id, open(uniqueFilenameAudio, 'rb'), infoTxt, duration)
	os.remove(uniqueFilenameImg)
	os.remove(uniqueFilenameAudio)
    
bot.polling()