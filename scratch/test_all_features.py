"""Test script for all features."""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from features.quiz import generate_quiz
from features.flashcards import generate_flashcards
from features.notes import generate_notes
from features.doubts import resolve_doubt

if __name__ == "__main__":
    print("\n--- TESTING NOTES GENERATION ---")
    notes_res = generate_notes(
        topic="Data Structures",
        subject="python",
        semester=1
    )
    if notes_res["success"]:
        print("Revision Notes:")
        print(notes_res["notes_md"][:300] + "\n...")
    else:
        print(f"Failed: {notes_res.get('message')}")

    print("\n--- TESTING FLASHCARDS GENERATION ---")
    flash_res = generate_flashcards(
        topic="Data Structures",
        subject="python",
        semester=1,
        num_cards=3
    )
    if flash_res["success"]:
        print(f"Generated {len(flash_res['cards'])} flashcards:")
        for idx, card in enumerate(flash_res["cards"]):
            print(f"Card {idx+1}: Front: {card['front']} | Back: {card['back']}")
    else:
        print(f"Failed: {flash_res.get('message')}")

    print("\n--- TESTING QUIZ GENERATION ---")
    quiz_res = generate_quiz(
        topic="Data Structures",
        subject="python",
        semester=1,
        num_questions=3
    )
    if quiz_res["success"]:
        print(f"Generated {len(quiz_res['questions'])} quiz questions:")
        for idx, q in enumerate(quiz_res["questions"]):
            print(f"Q{idx+1}: {q['question']}")
            for opt in q["options"]:
                print(f"  - {opt}")
            print(f"  Correct: {q['answer']}")
            print(f"  Explanation: {q['explanation']}")
    else:
        print(f"Failed: {quiz_res.get('message')}")

    print("\n--- TESTING DOUBTS RESOLUTION ---")
    doubt_res = resolve_doubt(
        doubt="What is a sequence type data structure?",
        subject="python",
        semester=1
    )
    if doubt_res["success"]:
        print("Doubt Resolved:")
        print(doubt_res["answer"])
    else:
        print(f"Failed: {doubt_res.get('message')}")
