from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
import tensorflow_hub as hub
import numpy as np
from config import GOOGLE_USE_PATH

sbert = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
use = hub.load(GOOGLE_USE_PATH)
classifier = pipeline("zero-shot-classification", model='facebook/bart-large-mnli')
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
