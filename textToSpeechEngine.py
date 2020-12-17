import speech_recognition as spr
import requests
import time
import os


recog = spr.Recognizer()

def fetch_text(audio_url):
    audio = requests.get(audio_url)
    file_loc = 'C:/Users/Admin/Desktop/twilio-outbound-dropbox/recordings/recording_'+str(time.time())+'.wav'

    open(file_loc, 'wb').write(audio.content)
    audio_file = spr.AudioFile(file_loc)

    with audio_file as source:
        recog.adjust_for_ambient_noise(source, duration=0.5)
        audio_data = recog.listen(source)
        recognised_text = recog.recognize_google(audio_data)
        print(recognised_text)

    os.remove(file_loc)

    return recognised_text

