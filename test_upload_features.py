import os
import sys

# Add current directory to path so we can import our modules
sys.path.append(os.getcwd())

from query_pipeline import generate_flash_notes, generate_quiz, generate_flowchart

def test_new_features():
    test_text = """
    Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water. 
    In plants, photosynthesis generally involves the green pigment chlorophyll and generates oxygen as a byproduct. 
    The process can be divided into two main stages: the light-dependent reactions and the light-independent reactions (Calvin cycle).
    """

    print("--- Testing Flash Notes ---")
    flash_notes = generate_flash_notes(test_text)
    print(flash_notes)
    assert len(flash_notes) > 0, "Flash notes should not be empty"

    print("\n--- Testing Quiz ---")
    quiz = generate_quiz(test_text)
    print(quiz)
    assert isinstance(quiz, list), "Quiz should be a list"
    assert len(quiz) > 0, "Quiz should not be empty"
    if len(quiz) > 0:
        first_q = quiz[0]
        assert "question" in first_q
        assert "options" in first_q
        assert "answer" in first_q

    print("\n--- Testing Flowchart ---")
    flowchart = generate_flowchart(test_text)
    print(flowchart)
    assert isinstance(flowchart, dict), "Flowchart should be a dictionary"
    assert "nodes" in flowchart and "edges" in flowchart, "Flowchart should have nodes and edges"

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    try:
        test_new_features()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
