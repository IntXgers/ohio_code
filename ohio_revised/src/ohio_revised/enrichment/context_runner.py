# generate_title_context.py
from title_context_analyzer import ModelManager
import json

analyzer = ModelManager()

# Analyze each title
for title_num in range(1, 64, 2):  # Ohio uses odd numbers
    print(f"Analyzing Title {title_num}...")
    context = analyzer.analyze_title(title_num)

    # Save context
    with open(f'contexts/title_{title_num}_context.json', 'w') as f:
        json.dump(context, f, indent=2)

    print(f"Context saved for Title {title_num}")

    # Run for all titles
    if __name__ == "__main__":
        analyzer = ModelManager()

        # Ohio titles (odd numbers mostly)
        titles = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51, 53,
                  55,
                  57, 58, 59, 61, 63]

        for title in titles:
            try:
                analyzer.analyze_title(title)
            except Exception as e:
                print(f"Error on title {title}: {e}")