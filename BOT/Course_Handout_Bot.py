#!/usr/bin/env python

"""
A telegram bot to fetch course handouts stored in google drive

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

To setup you will have to go to google projects, register a project and then get your credentials.json file

Usage:
Send any course code/name for the bot to fetch the results.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
from __future__ import print_function
import logging

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from telegram import ParseMode

#declare the type of scope to be allowed from google drive 
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
#A bot usually starts with the /start command. So this is usually only displayed in the first run.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hello !')
    update.message.reply_text('I Can Help You Find Handouts For Courses. Type /help For Instructions.')

#Any time a user sends /help, the help message is displayed which can be configured below
def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Type the Course Code (preferred) or Course Name to get the Handout for the particular course.\n\nIncase of Multiple Results, please alter the Search Term accordingly to get the exact file.\n\nPS : You Can Click On A Search Result To Copy It Onto Your Clipboard')

#The main function in the program which searches through the drive and returns the results or the file.
#This has been configured such that the results from the last four semesters are fetched comparing the filename.
def search(update: Update, context: CallbackContext) -> None:
    """Search Google Drive for the user message."""
    creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('drive', 'v3', credentials=creds)
    page_token = None
    #input the search term from the user
    term = update.message.text
    searchingmessage = update.message.reply_text('Searching...')
    chat_id = update.message.chat_id
    # Call the Drive v3 API
    
    #query is concatinated such that it is in a format to send to the drive api
    query = "name contains "+"'"+term+"'"
    results = service.files().list(q=query,spaces='drive',fields='nextPageToken, files(id, name)',pageToken=page_token).execute()
    items = results.get('files', [])
    
    #If there are no results
    if not items:
        searchingmessage.edit_text('No Results For The Particular Search Term. Please Try Again !')
    else:
        print('Files:')
        print('No of files '+ str(len(items)))
        #If there is only one result for the search, this code fetches the file from google drive.
        if(len(items)==1) :
            searchingmessage.edit_text('Found Your File ! Uploading...')
            for item in items:
                download_url = 'https://docs.google.com/uc?export=download&id=' + item['id']
                context.bot.send_document(chat_id=chat_id, document=download_url)
                searchingmessage.edit_text('Please Find Your File Below :')
        else :
            #if there is more than one result, list the results out (semwise)
            replytext = 'Found '+str(len(items))+ ' Results For Your Search :' + '\n(click on any filename to copy and send it back to me to get the file)'
            searchingmessage.edit_text(replytext)
            #SEM1
            #Sending a request to the drive api to fetch the files for the most recent semester using the naming convention followed.
            semterm = term + ' SEM1 (2020-21)'
            query = "name contains "+"'"+semterm+"'"
            results = service.files().list(q=query,spaces='drive',fields='nextPageToken, files(id, name)',pageToken=page_token).execute()
            items = results.get('files', [])
            if not items:
                #random variable assignment if no results (for future development)
                sem = 0
            else:
                #print result for the particular sem
                semtext = "SEM I (2020-21) :"
                update.message.reply_text(semtext)
                text = ""
                searchno = int(0)
                resultcount = int(0)
                for item in items:
                    searchno = searchno + 1
                    resultcount = resultcount + 1
                    text = text + str(searchno) + '. ' + "`" + u'{0}'.format(item['name']) + "`" + '\n\n'
                    #Set the nummber of search results per message
                    if(resultcount>=50) :
                        update.message.reply_text(text,parse_mode=ParseMode.MARKDOWN)
                        text = ""
                        resultcount = int(0)
                update.message.reply_text(text,parse_mode=ParseMode.MARKDOWN)
            #SEM2
            #Sending a request to the drive api to fetch the files for the second most recent semester using the naming convention followed.
            semterm = term + ' SEM2 (2019-20)'
            query = "name contains "+"'"+semterm+"'"
            results = service.files().list(q=query,spaces='drive',fields='nextPageToken, files(id, name)',pageToken=page_token).execute()
            items = results.get('files', [])
            if not items:
                #random variable assignment if no results (for future development)
                sem = 0
            else:
                semtext = "SEM II (2019-20) :"
                update.message.reply_text(semtext)
                text = ""
                searchno = int(0)
                resultcount = int(0)
                for item in items:
                    searchno = searchno + 1
                    resultcount = resultcount + 1
                    text = text + str(searchno) + '. ' + "`" + u'{0}'.format(item['name']) + "`" + '\n\n'
                    #Set the nummber of search results per message
                    if(resultcount>=50) :
                        update.message.reply_text(text,parse_mode=ParseMode.MARKDOWN)
                        text = ""
                        resultcount = int(0)
                update.message.reply_text(text,parse_mode=ParseMode.MARKDOWN)
            #SEM3
            semterm = term + ' SEM1 (2019-20)'
            query = "name contains "+"'"+semterm+"'"
            results = service.files().list(q=query,spaces='drive',fields='nextPageToken, files(id, name)',pageToken=page_token).execute()
            items = results.get('files', [])
            if not items:
                #searchingmessage.edit_text('No Results For The Particular Search Term. Please Try Again !')
                sem = 0
            else:
                semtext = "SEM I (2019-20) :"
                update.message.reply_text(semtext)
                text = ""
                searchno = int(0)
                resultcount = int(0)
                for item in items:
                    searchno = searchno + 1
                    resultcount = resultcount + 1
                    text = text + str(searchno) + '. ' + "`" + u'{0}'.format(item['name']) + "`" + '\n\n'
                    #Set the nummber of search results per message
                    if(resultcount>=50) :
                        update.message.reply_text(text,parse_mode=ParseMode.MARKDOWN)
                        text = ""
                        resultcount = int(0)
                update.message.reply_text(text,parse_mode=ParseMode.MARKDOWN)
            #SEM4
            semterm = term + ' SEM2 (2018-19)'
            query = "name contains "+"'"+semterm+"'"
            results = service.files().list(q=query,spaces='drive',fields='nextPageToken, files(id, name)',pageToken=page_token).execute()
            items = results.get('files', [])
            if not items:
                #searchingmessage.edit_text('No Results For The Particular Search Term. Please Try Again !')
                sem = 0
            else:
                semtext = "SEM II (2018-19) :"
                update.message.reply_text(semtext)
                text = ""
                searchno = int(0)
                resultcount = int(0)
                for item in items:
                    searchno = searchno + 1
                    resultcount = resultcount + 1
                    text = text + str(searchno) + '. ' + "`" + u'{0}'.format(item['name']) + "`" + '\n\n'
                    #Set the nummber of search results per message
                    if(resultcount>=50) :
                        update.message.reply_text(text,parse_mode=ParseMode.MARKDOWN)
                        text = ""
                        resultcount = int(0)
                update.message.reply_text(text,parse_mode=ParseMode.MARKDOWN)



def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    updater = Updater("TELEGRAM_BOT_TOKEN", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on noncommand i.e message - get the search item
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, search))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
