from ibm_watson import ToneAnalyzerV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
import json
from dotenv import load_dotenv

load_dotenv()

authenticator = IAMAuthenticator(os.getenv('WATSON_IAM_API_KEY'))
tone_analyzer = ToneAnalyzerV3(
    version=os.getenv('WATSON_VERSION'),
    authenticator=authenticator
)

tone_analyzer.set_service_url(os.getenv('WATSON_URL'))
tone_analyzer.set_disable_ssl_verification(True)

def is_customer_unhappy(input_text):
    tone_analysis = tone_analyzer.tone(
        {'text': input_text},
        content_type='application/json'
    ).get_result()
    tone_collection = json.dumps(tone_analysis, indent=2)
    print(tone_collection)

    for emotion in tone_analysis['document_tone']['tones']:
        if emotion['tone_name'] == 'Sadness' or emotion['tone_name'] == 'Anger':
            return True

    return False
