from apps.ai.rag import rag_engine

question = "Tu peux me donner des chiffres sur CHARGE MAXIMALE A LA PARCELLE (en kilogrammes par hectare) pour le vin blanc en cotes de duras?"
print(len(rag_engine.documents))
print(rag_engine.retrieve(question)[:800])
