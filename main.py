import os
import dropbox
import requests
from flask import Flask, request, Response
from dotenv import load_dotenv
from twilio.twiml.voice_response import Record, Gather, VoiceResponse, Dial
from translationEngine import translate_text
import textToSpeechEngine
import watsonToneAnalyzer
from twilio.rest import Client

load_dotenv()
app = Flask(__name__)


def find_language(choice):
    if int(choice) == 1:
        return 'en-IN'
    if int(choice) == 2:
        return 'hi-IN'
    return 'de-DE'



def remove_indian_country_code(text):
    if str(text).startswith("+91"):
        return text[3:]
    return text




def attach_indian_country_code(text):
    if str(text).startswith("+91"):
        return text
    return "+91"+str(text)



@app.route('/inbound/voice/call', methods=['POST'])
def incoming_voice_call():
    response = VoiceResponse()
    gather = Gather(action='/outbound/voice/call', method='POST')
    gather.say('Please enter the number to dial, followed by the pound sign')
    response.append(gather)
    response.say('We didn\'t receive any input. Goodbye')
    return str(response)




def apology_call(phone_number, lang):
    account_sid = os.getenv('TWILIO_ACC_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    call = client.calls.create(
        url='http://9075b3e525c7.ngrok.io/say/sorry?lang='+lang,
        to=phone_number,
        from_=os.getenv('TWILIO_NUMBER'),
    )
    print("Saying sorry to "+phone_number+" in "+lang)
    print(call.sid)



@app.route('/say/sorry', methods=['POST'])
def apologise():
    response = VoiceResponse()

    lang = 'en-IN'

    if 'lang' in request.values:
        lang = request.values['lang']

    response.say(translate_text('We are very sorry for your recent experience with Flipkart. '
                                'A customer service executive will reach out to you very soon '
                                'to address your concerns.', 'en-IN', lang), language=lang)
    return str(response)





@app.route('/access/denied', methods=['POST'])
def access_denied():
    response = VoiceResponse()

    lang = 'en-IN'

    if 'lang' in request.values:
        lang = request.values['lang']

    response.say(translate_text('Thanks for your time!', 'en-IN', lang), language=lang)
    return str(response)




@app.route('/seek/consent', methods=['POST'])
def seek_consent():
    response = VoiceResponse()

    if 'Digits' in request.values:
        # Get which language the caller chose
        choice = request.values['Digits']
        lang = find_language(choice)

        gather = Gather(action='/access/denied?lang='+lang)
        gather.say(translate_text('This call is going to be recorded for taking up your qualitative feedback, '
                   'please enter any key to discontinue', 'en-IN', lang), language=lang)

        response.append(gather)
        print("Starting record")

        response.say(translate_text('Please enter your feedback after you hear a beep sound', 'en-IN', lang),
                   language=lang)
        response.record(action='/exit/graceful?lang='+lang, timeout=5, play_beep='true',
                        recording_status_callback='/recording/callback?lang='+lang+''
                                                  '&customer_number='+str(request.form["To"]).replace("+", "%2B"),
                        recording_status_callback_event='completed')

        return str(response)

    response.redirect('/seek/language')
    return str(response)





@app.route('/seek/language', methods=['POST'])
def get_language():
    response = VoiceResponse()
    gather = Gather(num_digits=1, action='/seek/consent')

    gather.say('Thanks for giving Flipkart a chance to serve you! For English, press 1', language='en-IN')
    gather.say(translate_text('Thanks for giving Flipkart a chance to serve you! For Hindi, press 2', 'en-IN', 'hi-IN'), language='hi-IN')
    gather.say(translate_text('Thanks for giving Flipkart a chance to serve you! For German, press 3', 'en-IN', 'de-DE'), language='de-DE')

    response.append(gather)
    response.redirect('/seek/language')
    return str(response)




@app.route('/exit/graceful', methods=['POST'])
def graceful_exit():
    print('Came here gracefully')

    lang = 'en-IN'

    if 'lang' in request.values:
        lang = request.values['lang']

    response = VoiceResponse()
    response.say(translate_text('We have got your feedback. Thanks for your time!', 'en-IN', lang), language=lang)
    return str(response)





@app.route('/recording/callback', methods=['POST'])
def upload_recording():

    lang = 'en-IN'

    if 'lang' in request.values:
        lang = request.values['lang']

    if 'RecordingStatus' in request.values and request.values['RecordingStatus'] == 'completed':
        dropbox_client = dropbox.Dropbox(os.getenv('DROPBOX_ACCESS_TOKEN'))
        recording_url = request.form['RecordingUrl']
        recording_sid = request.form['RecordingSid']
        upload_path = f"/twilio-recording/{recording_sid}.mp3"

        with requests.get(recording_url, stream=True) as r:
             dropbox_client.files_upload(r.raw.read(), upload_path)

        record_transcription = textToSpeechEngine.fetch_text(recording_url)
        en_transcription = translate_text(record_transcription, lang, 'en-IN')

        # Customer is unhappy, initiate a callback
        if watsonToneAnalyzer.is_customer_unhappy(en_transcription):
            print("Customer is unhappy, initiating callback")
            customer_number = request.values['customer_number']
            print(customer_number)
            apology_call(customer_number, lang)

    return Response(), 200



if __name__ == '__main__':
    app.run()
