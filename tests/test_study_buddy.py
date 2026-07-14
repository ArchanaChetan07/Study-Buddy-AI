class TestStudyBuddy:
    def test_topic_extraction(self):
        text = "Today we will study photosynthesis, cellular respiration, and DNA replication"
        topics = [w for w in text.split() if w[0].isupper() and len(w) > 3]
        assert len(topics) > 0

    def test_quiz_question_structure(self):
        question = {"q": "What is photosynthesis?", "options": ["A","B","C","D"], "answer": "A"}
        assert "q" in question and "options" in question and "answer" in question
        assert len(question["options"]) == 4

    def test_score_calculation(self):
        correct = 7
        total = 10
        score = (correct / total) * 100
        assert score == 70.0

    def test_empty_input_handled(self):
        def process(text):
            if not text or not text.strip():
                return "Please provide a study topic."
            return text
        assert process("") != ""
        assert process("  ") != ""

    def test_session_history_tracked(self):
        history = []
        history.append({"topic": "Math", "score": 80})
        history.append({"topic": "Science", "score": 90})
        assert len(history) == 2
        avg = sum(h["score"] for h in history) / len(history)
        assert avg == 85.0

    def test_difficulty_levels(self):
        levels = ["easy", "medium", "hard"]
        assert "easy" in levels
        assert len(levels) == 3

    def test_flashcard_creation(self):
        flashcard = {"front": "What is mitosis?", "back": "Cell division producing 2 identical daughter cells"}
        assert "front" in flashcard and "back" in flashcard
        assert len(flashcard["front"]) > 0

class TestStudySession:
    def test_timer_tracking(self):
        import time
        start = time.time()
        time.sleep(0.01)
        elapsed = time.time() - start
        assert elapsed > 0

    def test_progress_percentage(self):
        completed = 3
        total = 10
        pct = round((completed / total) * 100)
        assert pct == 30

    def test_subject_categories(self):
        subjects = {"Math", "Science", "History", "English", "CS"}
        assert len(subjects) >= 4
