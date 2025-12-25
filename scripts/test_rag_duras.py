import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monchai.settings')
django.setup()

from apps.ai.rag import rag_engine

query = "Tu peux me donner des chiffres sur CHARGE MAXIMALE À LA PARCELLE (en kilogrammes par hectare) pour le vin blanc en cotes de duras?"
print(f"Query: {query}\n")

print(f"Total docs loaded: {len(rag_engine.documents)}")
# Check if relevant docs are loaded
duras_docs = [k for k in rag_engine.documents.keys() if 'duras' in k.lower()]
print(f"Duras docs found: {duras_docs}\n")

results = rag_engine.retrieve(query)
print("-" * 40)
print("RETRIEVAL RESULTS:")
print("-" * 40)
print(results[:1000] + "..." if len(results) > 1000 else results)
