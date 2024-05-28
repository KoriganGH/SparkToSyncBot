from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
import tensorflow_hub as hub
import numpy as np
from openai import OpenAI
from config import GOOGLE_USE_PATH, CHAT_GPT_API_KEY

sbert = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
use = hub.load(GOOGLE_USE_PATH)
classifier = pipeline("zero-shot-classification", model='facebook/bart-large-mnli')
client = OpenAI(api_key=CHAT_GPT_API_KEY)
personality_traits = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]


def personality_classification(profile):
    result = classifier(profile, personality_traits)
    trait = max(zip(result['labels'], result['scores']), key=lambda x: x[1])
    return trait[0]


def compare_profiles_sbert(profile1, profile2):
    embedding1 = sbert.encode(profile1, convert_to_tensor=True)
    embedding2 = sbert.encode(profile2, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(embedding1, embedding2)
    return round(similarity.item(), 2)


def compare_profiles_use(profile1, profile2):
    embedding1 = use([profile1])
    embedding2 = use([profile2])
    similarity = np.inner(embedding1, embedding2)
    return round(similarity.item(), 2)


def compare_profiles_gpt(profile1, profile2):
    response = client.chat.completions.create(model="gpt-4o", messages=[
        {"role": "system", "content": "You are a helpful psychologist's assistant."},
        {"role": "user", "content": f"Напиши мне процент совместимости этих двух людей. В ответе от тебя жду только "
                                    f"число от 0 до 100 в зависимости от совместимости этих людей.\n"
                                    f"Человек 1\n{profile1}\nЧеловек 2\n{profile2}"},
    ])
    return response.choices[0].message.content
