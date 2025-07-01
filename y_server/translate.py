import os
import re
import json
import deepl
from deep_translator import GoogleTranslator

def translate(text, src_lang="english", tgt_lang="italian", translator=None):
    config = json.load(open(f"config_files{os.sep}exp_config.json"))
    translator = config.get("translator", "google") if translator is None else translator

    locales = json.load(open("config_files/locales.json", "r", encoding="utf-8"))
    src_lang = locales[src_lang]
    tgt_lang = locales[tgt_lang]

    if src_lang == tgt_lang:
        return text
    
    if translator.lower() == "google":
        text_loc = translate_google(text, src_lang, tgt_lang)
    elif translator.lower() == "deepl":
        text_loc = translate_deepl(text, src_lang, tgt_lang)
    else:
        print(f"Translator {translator} not supported. Using Google as default.")
        text_loc = translate_google(text, src_lang, tgt_lang)
    
    return text_loc

def translate_google(text, src_lang="en", tgt_lang="it"):
    text_loc = GoogleTranslator(source=src_lang, target=tgt_lang).translate(text)
    text_loc = re.sub(r'\brdc\b', 'il reddito di cittadinanza', text_loc, flags=re.IGNORECASE)
    return text_loc

def translate_deepl(text, src_lang="en", tgt_lang="it"):
    auth_key = os.getenv("DEEPL_API_KEY")
    glossary_id = os.getenv("DEEPL_GLOSSARY_ID")
    deepl_client = deepl.DeepLClient(auth_key)

    if glossary_id:
        result = deepl_client.translate_text(text, source_lang=src_lang, target_lang=tgt_lang, glossary=glossary_id)
    else:
        result = deepl_client.translate_text(text, source_lang=src_lang, target_lang=tgt_lang)

    #print(f"\n{print(result.billed_characters)}\n")
    return result.text