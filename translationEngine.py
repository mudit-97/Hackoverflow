from googletrans import Translator

def translate_text(text, from_lang, to_lang):
    translator = Translator(service_urls=['translate.googleapis.com'])
    translated_text = str(translator.translate(text, src=from_lang.split("-")[0], dest=to_lang.split("-")[0]).text)
    print('Translated Text: '+translated_text)
    return translated_text
