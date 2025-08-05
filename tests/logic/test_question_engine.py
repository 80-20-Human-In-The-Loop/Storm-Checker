import pytest
from logic.question_engine import Question, QuestionEngine, QuestionState

@pytest.fixture
def sample_question():
    return Question(
        text="What is 2 + 2?",
        options=["3", "4", "5"],
        correct_index=1,
        explanation="It's simple math!",
        hint="Think about basic arithmetic"
    )

@pytest.fixture
def question_engine(sample_question):
    return QuestionEngine(sample_question)

def test_question_engine_initialization(sample_question):
    """Test that the QuestionEngine can be initialized."""
    engine = QuestionEngine(sample_question)
    assert isinstance(engine, QuestionEngine)
    assert engine.selected_index == 0
    assert engine.state == QuestionState.DISPLAYING
    assert engine.user_answer is None

def test_get_selected_index(question_engine):
    """Test get_selected_index method (line 41)."""
    assert question_engine.get_selected_index() == 0
    question_engine.selected_index = 1
    assert question_engine.get_selected_index() == 1

def test_can_move_up(question_engine):
    """Test can_move_up method (line 45)."""
    # At index 0, cannot move up
    assert question_engine.can_move_up() == False
    
    # At index 1, can move up
    question_engine.selected_index = 1
    assert question_engine.can_move_up() == True
    
    # At index 2, can move up
    question_engine.selected_index = 2
    assert question_engine.can_move_up() == True

def test_can_move_down(question_engine):
    """Test can_move_down method (line 49)."""
    # At index 0, can move down (3 options total)
    assert question_engine.can_move_down() == True
    
    # At index 1, can move down
    question_engine.selected_index = 1
    assert question_engine.can_move_down() == True
    
    # At index 2 (last), cannot move down
    question_engine.selected_index = 2
    assert question_engine.can_move_down() == False

def test_move_up(question_engine):
    """Test move_up method (lines 53-56)."""
    # Cannot move up from 0
    assert question_engine.move_up() == False
    assert question_engine.selected_index == 0
    
    # Move to index 2, then move up
    question_engine.selected_index = 2
    assert question_engine.move_up() == True
    assert question_engine.selected_index == 1
    
    # Move up again
    assert question_engine.move_up() == True
    assert question_engine.selected_index == 0
    
    # Cannot move up anymore
    assert question_engine.move_up() == False
    assert question_engine.selected_index == 0

def test_move_down(question_engine):
    """Test move_down method (lines 60-63)."""
    # Can move down from 0
    assert question_engine.move_down() == True
    assert question_engine.selected_index == 1
    
    # Can move down again
    assert question_engine.move_down() == True
    assert question_engine.selected_index == 2
    
    # Cannot move down from last position
    assert question_engine.move_down() == False
    assert question_engine.selected_index == 2

def test_select_by_number(question_engine):
    """Test select_by_number method."""
    # Valid selections (1-based)
    assert question_engine.select_by_number(1) == True
    assert question_engine.selected_index == 0
    
    assert question_engine.select_by_number(2) == True
    assert question_engine.selected_index == 1
    
    assert question_engine.select_by_number(3) == True
    assert question_engine.selected_index == 2
    
    # Invalid selections
    assert question_engine.select_by_number(0) == False  # Too low
    assert question_engine.select_by_number(4) == False  # Too high
    assert question_engine.select_by_number(-1) == False  # Negative

def test_submit_answer(question_engine):
    """Test submit_answer method."""
    # Submit wrong answer (selected index 0, correct is 1)
    is_correct, selected = question_engine.submit_answer()
    assert is_correct == False
    assert selected == 0
    assert question_engine.state == QuestionState.ANSWERED
    assert question_engine.user_answer == 0
    
    # Test submitting correct answer
    engine2 = QuestionEngine(question_engine.question)
    engine2.selected_index = 1  # Correct answer
    is_correct, selected = engine2.submit_answer()
    assert is_correct == True
    assert selected == 1

def test_is_answered(question_engine):
    """Test is_answered method."""
    assert question_engine.is_answered() == False
    
    question_engine.submit_answer()
    assert question_engine.is_answered() == True

def test_get_result_data(question_engine):
    """Test get_result_data method including line 92."""
    # Before answering, should return None
    assert question_engine.get_result_data() is None
    
    # Submit wrong answer
    question_engine.submit_answer()
    result = question_engine.get_result_data()
    
    assert result is not None
    assert result['is_correct'] == False
    assert result['user_answer'] == 0
    assert result['correct_answer'] == 1
    assert result['correct_option'] == "4"
    assert result['user_option'] == "3"
    assert result['explanation'] == "It's simple math!"
    
    # Test with correct answer
    engine2 = QuestionEngine(question_engine.question)
    engine2.selected_index = 1
    engine2.submit_answer()
    result2 = engine2.get_result_data()
    
    assert result2['is_correct'] == True
    assert result2['user_answer'] == 1
    assert result2['user_option'] == "4"

def test_get_display_data(question_engine):
    """Test get_display_data method."""
    # Before answering
    data = question_engine.get_display_data()
    assert data['question_text'] == "What is 2 + 2?"
    assert data['options'] == ["3", "4", "5"]
    assert data['selected_index'] == 0
    assert data['hint'] == "Think about basic arithmetic"
    assert data['is_answered'] == False
    assert data['user_answer'] is None
    assert data['correct_index'] == 1
    
    # After answering
    question_engine.submit_answer()
    data = question_engine.get_display_data()
    assert data['hint'] is None  # No hint after answering
    assert data['is_answered'] == True
    assert data['user_answer'] == 0

def test_reset(question_engine):
    """Test reset method."""
    # Make some changes
    question_engine.selected_index = 2
    question_engine.submit_answer()
    
    # Verify state before reset
    assert question_engine.selected_index == 2
    assert question_engine.state == QuestionState.ANSWERED
    assert question_engine.user_answer == 2
    
    # Reset
    question_engine.reset()
    
    # Verify reset state
    assert question_engine.selected_index == 0
    assert question_engine.state == QuestionState.DISPLAYING
    assert question_engine.user_answer is None

def test_question_without_hint():
    """Test question without hint."""
    question = Question(
        text="Test question",
        options=["A", "B"],
        correct_index=0,
        explanation="Test explanation"
        # No hint
    )
    engine = QuestionEngine(question)
    
    data = engine.get_display_data()
    assert data['hint'] is None

def test_question_state_enum():
    """Test QuestionState enum values."""
    assert QuestionState.DISPLAYING.value == "displaying"
    assert QuestionState.ANSWERED.value == "answered"
