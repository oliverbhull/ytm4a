import nltk
import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download essential NLTK data
resources = [
    'punkt',
    'punkt_tab',
    'stopwords',
    'averaged_perceptron_tagger',
    'maxent_ne_chunker',
    'words',
    'tokenizers/punkt/english.pickle'
]

for resource in resources:
    print(f"Downloading {resource}...")
    try:
        nltk.download(resource)
    except Exception as e:
        print(f"Error downloading {resource}: {str(e)}")
    
print("\nNLTK data download complete!") 