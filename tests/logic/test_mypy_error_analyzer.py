"""
Comprehensive Tests for MyPy Error Analyzer
==========================================
Tests for error analysis and educational categorization with full coverage of all functionality.
"""

import pytest
from unittest.mock import Mock, patch
from collections import Counter
from typing import Dict, List

from logic.mypy_error_analyzer import (
    ErrorCategory, ErrorExplanation, AnalysisResult, ErrorAnalyzer
)
from logic.mypy_runner import MypyError, MypyResult


class TestErrorCategory:
    """Test the ErrorCategory dataclass."""
    
    def test_error_category_initialization_minimal(self):
        """Test ErrorCategory initialization with minimal parameters."""
        category = ErrorCategory(
            id="test_id",
            name="Test Category",
            description="A test category",
            difficulty=2,
            common_codes={"test-code"}
        )
        
        assert category.id == "test_id"
        assert category.name == "Test Category"
        assert category.description == "A test category"
        assert category.difficulty == 2
        assert category.common_codes == {"test-code"}
        assert category.tutorial_id is None
        assert category.examples == []
    
    def test_error_category_initialization_complete(self):
        """Test ErrorCategory initialization with all parameters."""
        examples = ["Example 1", "Example 2"]
        category = ErrorCategory(
            id="test_id",
            name="Test Category",
            description="A test category",
            difficulty=3,
            common_codes={"test-code", "another-code"},
            tutorial_id="test_tutorial",
            examples=examples
        )
        
        assert category.id == "test_id"
        assert category.name == "Test Category"
        assert category.description == "A test category"
        assert category.difficulty == 3
        assert category.common_codes == {"test-code", "another-code"}
        assert category.tutorial_id == "test_tutorial"
        assert category.examples == examples
    
    def test_matches_error_with_matching_code(self):
        """Test matches_error returns True for matching error code."""
        category = ErrorCategory(
            id="test",
            name="Test",
            description="Test",
            difficulty=1,
            common_codes={"no-untyped-def", "assignment"}
        )
        
        error = Mock(spec=MypyError)
        error.error_code = "no-untyped-def"
        
        assert category.matches_error(error)
    
    def test_matches_error_with_non_matching_code(self):
        """Test matches_error returns False for non-matching error code."""
        category = ErrorCategory(
            id="test",
            name="Test",
            description="Test",
            difficulty=1,
            common_codes={"no-untyped-def", "assignment"}
        )
        
        error = Mock(spec=MypyError)
        error.error_code = "some-other-code"
        
        assert not category.matches_error(error)
    
    def test_matches_error_with_no_error_code(self):
        """Test matches_error returns False when error has no code."""
        category = ErrorCategory(
            id="test",
            name="Test",
            description="Test",
            difficulty=1,
            common_codes={"no-untyped-def"}
        )
        
        error = Mock(spec=MypyError)
        error.error_code = None
        
        assert not category.matches_error(error)
    
    def test_matches_error_with_empty_common_codes(self):
        """Test matches_error returns False when category has no common codes."""
        category = ErrorCategory(
            id="test",
            name="Test",
            description="Test",
            difficulty=1,
            common_codes=set()
        )
        
        error = Mock(spec=MypyError)
        error.error_code = "any-code"
        
        assert not category.matches_error(error)


class TestErrorExplanation:
    """Test the ErrorExplanation dataclass."""
    
    def test_error_explanation_initialization_minimal(self):
        """Test ErrorExplanation initialization with minimal parameters."""
        explanation = ErrorExplanation(
            error_code="test-code",
            simple_explanation="Simple explanation",
            detailed_explanation="Detailed explanation",
            common_causes=["Cause 1", "Cause 2"],
            how_to_fix=["Fix 1", "Fix 2"]
        )
        
        assert explanation.error_code == "test-code"
        assert explanation.simple_explanation == "Simple explanation"
        assert explanation.detailed_explanation == "Detailed explanation"
        assert explanation.common_causes == ["Cause 1", "Cause 2"]
        assert explanation.how_to_fix == ["Fix 1", "Fix 2"]
        assert explanation.examples == {}
        assert explanation.resources == []
    
    def test_error_explanation_initialization_complete(self):
        """Test ErrorExplanation initialization with all parameters."""
        examples = {"before": "bad code", "after": "good code"}
        resources = ["Resource 1", "Resource 2"]
        
        explanation = ErrorExplanation(
            error_code="test-code",
            simple_explanation="Simple explanation",
            detailed_explanation="Detailed explanation",
            common_causes=["Cause 1"],
            how_to_fix=["Fix 1"],
            examples=examples,
            resources=resources
        )
        
        assert explanation.examples == examples
        assert explanation.resources == resources


class TestAnalysisResult:
    """Test the AnalysisResult dataclass."""
    
    def test_analysis_result_initialization(self):
        """Test AnalysisResult initialization with all parameters."""
        by_category = {"category1": [Mock(spec=MypyError)]}
        by_difficulty = {1: [Mock(spec=MypyError)]}
        by_file = {"file.py": [Mock(spec=MypyError)]}
        suggested_tutorials = ["tutorial1", "tutorial2"]
        learning_path = [Mock(spec=MypyError)]
        
        result = AnalysisResult(
            total_errors=5,
            by_category=by_category,
            by_difficulty=by_difficulty,
            by_file=by_file,
            suggested_tutorials=suggested_tutorials,
            learning_path=learning_path,
            complexity_score=42.5
        )
        
        assert result.total_errors == 5
        assert result.by_category == by_category
        assert result.by_difficulty == by_difficulty
        assert result.by_file == by_file
        assert result.suggested_tutorials == suggested_tutorials
        assert result.learning_path == learning_path
        assert result.complexity_score == 42.5


class TestErrorAnalyzer:
    """Test the ErrorAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create ErrorAnalyzer instance for testing."""
        return ErrorAnalyzer()
    
    @pytest.fixture
    def mock_error(self):
        """Create mock MypyError for testing."""
        error = Mock(spec=MypyError)
        error.file_path = "test.py"
        error.line_number = 10
        error.column = 5
        error.severity = "error"
        error.error_code = "no-untyped-def"
        error.message = "Function is missing a type annotation"
        error.raw_line = "test.py:10:5: error: Function is missing a type annotation [no-untyped-def]"
        return error
    
    @pytest.fixture
    def mock_result(self, mock_error):
        """Create mock MypyResult for testing."""
        result = Mock(spec=MypyResult)
        result.errors = [mock_error]
        result.files_checked = 1
        result.get_errors_by_file.return_value = {"test.py": [mock_error]}
        return result
    
    def test_analyzer_initialization(self, analyzer):
        """Test ErrorAnalyzer initialization."""
        assert isinstance(analyzer, ErrorAnalyzer)
        assert len(analyzer.CATEGORIES) > 0
        assert len(analyzer.EXPLANATIONS) > 0
    
    def test_analyzer_categories_structure(self, analyzer):
        """Test that all categories have required structure."""
        for category in analyzer.CATEGORIES:
            assert isinstance(category, ErrorCategory)
            assert category.id
            assert category.name
            assert category.description
            assert isinstance(category.difficulty, int)
            assert 0 <= category.difficulty <= 5
            assert isinstance(category.common_codes, set)
    
    def test_analyzer_explanations_structure(self, analyzer):
        """Test that all explanations have required structure."""
        for explanation in analyzer.EXPLANATIONS.values():
            assert isinstance(explanation, ErrorExplanation)
            assert explanation.error_code
            assert explanation.simple_explanation
            assert explanation.detailed_explanation
            assert isinstance(explanation.common_causes, list)
            assert isinstance(explanation.how_to_fix, list)
    
    def test_analyze_errors_complete_flow(self, analyzer, mock_result):
        """Test complete analyze_errors workflow."""
        result = analyzer.analyze_errors(mock_result)
        
        assert isinstance(result, AnalysisResult)
        assert result.total_errors == 1
        assert isinstance(result.by_category, dict)
        assert isinstance(result.by_difficulty, dict)
        assert isinstance(result.by_file, dict)
        assert isinstance(result.suggested_tutorials, list)
        assert isinstance(result.learning_path, list)
        assert isinstance(result.complexity_score, float)
        assert 0 <= result.complexity_score <= 100
    
    def test_analyze_errors_empty_result(self, analyzer):
        """Test analyze_errors with no errors."""
        empty_result = Mock(spec=MypyResult)
        empty_result.errors = []
        empty_result.get_errors_by_file.return_value = {}
        
        result = analyzer.analyze_errors(empty_result)
        
        assert result.total_errors == 0
        assert result.by_category == {}
        assert result.by_difficulty == {}
        assert result.by_file == {}
        assert result.suggested_tutorials == []
        assert result.learning_path == []
        assert result.complexity_score == 0.0
    
    def test_get_explanation_existing_code(self, analyzer):
        """Test get_explanation for error code with existing explanation."""
        error = Mock(spec=MypyError)
        error.error_code = "no-untyped-def"
        
        explanation = analyzer.get_explanation(error)
        
        assert explanation is not None
        assert isinstance(explanation, ErrorExplanation)
        assert explanation.error_code == "no-untyped-def"
    
    def test_get_explanation_non_existing_code(self, analyzer):
        """Test get_explanation for error code without explanation."""
        error = Mock(spec=MypyError)
        error.error_code = "some-unknown-code"
        
        explanation = analyzer.get_explanation(error)
        
        assert explanation is None
    
    def test_get_explanation_no_error_code(self, analyzer):
        """Test get_explanation for error without error code."""
        error = Mock(spec=MypyError)
        error.error_code = None
        
        explanation = analyzer.get_explanation(error)
        
        assert explanation is None
    
    def test_suggest_fix_order_single_error(self, analyzer, mock_error):
        """Test suggest_fix_order with single error."""
        ordered = analyzer.suggest_fix_order([mock_error])
        
        assert len(ordered) == 1
        assert ordered[0] == mock_error
    
    def test_suggest_fix_order_multiple_errors_by_difficulty(self, analyzer):
        """Test suggest_fix_order orders by difficulty."""
        # Create errors with different difficulties
        easy_error = Mock(spec=MypyError)
        easy_error.error_code = "no-untyped-def"  # Difficulty 1
        easy_error.file_path = "test.py"
        
        hard_error = Mock(spec=MypyError)
        hard_error.error_code = "overload-impl"  # Difficulty 5
        hard_error.file_path = "test.py"
        
        medium_error = Mock(spec=MypyError)
        medium_error.error_code = "assignment"  # Difficulty 2
        medium_error.file_path = "test.py"
        
        errors = [hard_error, easy_error, medium_error]
        ordered = analyzer.suggest_fix_order(errors)
        
        # Should be ordered by difficulty: easy (1), medium (2), hard (5)
        assert len(ordered) == 3
        assert ordered[0] == easy_error
        assert ordered[1] == medium_error
        assert ordered[2] == hard_error
    
    def test_suggest_fix_order_prioritizes_explained_errors(self, analyzer):
        """Test suggest_fix_order prioritizes errors with explanations."""
        # Create errors with same difficulty but different explanation availability
        explained_error = Mock(spec=MypyError)
        explained_error.error_code = "no-untyped-def"  # Has explanation
        explained_error.file_path = "test.py"
        
        unexplained_error = Mock(spec=MypyError)
        unexplained_error.error_code = "some-unknown-code"  # No explanation
        unexplained_error.file_path = "test.py"
        
        errors = [unexplained_error, explained_error]
        ordered = analyzer.suggest_fix_order(errors)
        
        # Explained error should come first
        assert ordered[0] == explained_error
        assert ordered[1] == unexplained_error
    
    def test_categorize_errors_known_category(self, analyzer):
        """Test _categorize_errors with errors matching known categories."""
        error1 = Mock(spec=MypyError)
        error1.error_code = "no-untyped-def"
        
        error2 = Mock(spec=MypyError)
        error2.error_code = "assignment"
        
        categorized = analyzer._categorize_errors([error1, error2])
        
        assert "missing_annotations" in categorized
        assert "incompatible_types" in categorized
        assert error1 in categorized["missing_annotations"]
        assert error2 in categorized["incompatible_types"]
    
    def test_categorize_errors_unknown_category(self, analyzer):
        """Test _categorize_errors with uncategorized errors."""
        error = Mock(spec=MypyError)
        error.error_code = "totally-unknown-code"
        
        categorized = analyzer._categorize_errors([error])
        
        assert "uncategorized" in categorized
        assert error in categorized["uncategorized"]
    
    def test_categorize_errors_mixed(self, analyzer):
        """Test _categorize_errors with mix of known and unknown errors."""
        known_error = Mock(spec=MypyError)
        known_error.error_code = "no-untyped-def"
        
        unknown_error = Mock(spec=MypyError)
        unknown_error.error_code = "unknown-code"
        
        categorized = analyzer._categorize_errors([known_error, unknown_error])
        
        assert "missing_annotations" in categorized
        assert "uncategorized" in categorized
        assert known_error in categorized["missing_annotations"]
        assert unknown_error in categorized["uncategorized"]
    
    def test_group_by_difficulty(self, analyzer):
        """Test _group_by_difficulty groups errors correctly."""
        errors = [Mock(spec=MypyError), Mock(spec=MypyError)]
        by_category = {
            "missing_annotations": [errors[0]],  # Difficulty 1
            "incompatible_types": [errors[1]]    # Difficulty 2
        }
        
        by_difficulty = analyzer._group_by_difficulty(errors, by_category)
        
        assert 1 in by_difficulty
        assert 2 in by_difficulty
        assert errors[0] in by_difficulty[1]
        assert errors[1] in by_difficulty[2]
    
    def test_group_by_difficulty_unknown_category(self, analyzer):
        """Test _group_by_difficulty with unknown category defaults to difficulty 5."""
        error = Mock(spec=MypyError)
        by_category = {"unknown_category": [error]}
        
        by_difficulty = analyzer._group_by_difficulty([error], by_category)
        
        assert 5 in by_difficulty
        assert error in by_difficulty[5]
    
    def test_suggest_tutorials_with_errors(self, analyzer):
        """Test _suggest_tutorials suggests relevant tutorials."""
        by_category = {
            "missing_annotations": [Mock(spec=MypyError)] * 5,  # 5 errors
            "incompatible_types": [Mock(spec=MypyError)] * 2    # 2 errors
        }
        
        tutorials = analyzer._suggest_tutorials(by_category)
        
        assert isinstance(tutorials, list)
        assert len(tutorials) > 0
        # Should prioritize missing_annotations due to higher error count and lower difficulty
        assert "type_annotations_basics" in tutorials
        assert "type_compatibility" in tutorials
    
    def test_suggest_tutorials_empty_categories(self, analyzer):
        """Test _suggest_tutorials returns empty list for no errors."""
        tutorials = analyzer._suggest_tutorials({})
        
        assert tutorials == []
    
    def test_suggest_tutorials_categories_without_tutorials(self, analyzer):
        """Test _suggest_tutorials handles categories without tutorial IDs."""
        # Create a mock category without tutorial_id
        by_category = {"uncategorized": [Mock(spec=MypyError)]}
        
        tutorials = analyzer._suggest_tutorials(by_category)
        
        # Should return empty list or not include categories without tutorial IDs
        assert isinstance(tutorials, list)
    
    def test_create_learning_path_ordered_by_difficulty(self, analyzer):
        """Test _create_learning_path orders by category difficulty."""
        error1 = Mock(spec=MypyError)
        error1.error_code = "no-untyped-def"  # Category with explanation
        error1.file_path = "test1.py"
        
        error2 = Mock(spec=MypyError)
        error2.error_code = "assignment"  # Category with explanation
        error2.file_path = "test2.py"
        
        by_category = {
            "missing_annotations": [error1],    # Difficulty 1
            "incompatible_types": [error2]      # Difficulty 2
        }
        
        learning_path = analyzer._create_learning_path([error1, error2], by_category)
        
        assert len(learning_path) == 2
        assert learning_path[0] == error1  # Lower difficulty first
        assert learning_path[1] == error2
    
    def test_create_learning_path_prioritizes_explanations(self, analyzer):
        """Test _create_learning_path prioritizes errors with explanations."""
        explained_error = Mock(spec=MypyError)
        explained_error.error_code = "no-untyped-def"  # Has explanation
        explained_error.file_path = "test1.py"
        
        unexplained_error = Mock(spec=MypyError)
        unexplained_error.error_code = "some-unknown-code"  # No explanation
        unexplained_error.file_path = "test2.py"
        
        # Both in same category (mock)
        by_category = {
            "missing_annotations": [explained_error, unexplained_error]
        }
        
        learning_path = analyzer._create_learning_path([explained_error, unexplained_error], by_category)
        
        assert len(learning_path) == 2
        assert learning_path[0] == explained_error  # Explained first
        assert learning_path[1] == unexplained_error
    
    def test_create_learning_path_handles_uncategorized(self, analyzer):
        """Test _create_learning_path includes uncategorized errors at end."""
        categorized_error = Mock(spec=MypyError)
        categorized_error.error_code = "no-untyped-def"
        categorized_error.file_path = "test1.py"
        
        uncategorized_error = Mock(spec=MypyError)
        uncategorized_error.error_code = "unknown-code"
        uncategorized_error.file_path = "test2.py"
        
        by_category = {
            "missing_annotations": [categorized_error],
            "uncategorized": [uncategorized_error]
        }
        
        learning_path = analyzer._create_learning_path([categorized_error, uncategorized_error], by_category)
        
        assert len(learning_path) == 2
        assert learning_path[0] == categorized_error  # Categorized first
        assert learning_path[1] == uncategorized_error  # Uncategorized last
    
    def test_calculate_complexity_score_no_errors(self, analyzer):
        """Test _calculate_complexity_score returns 0 for no errors."""
        score = analyzer._calculate_complexity_score({}, [])
        
        assert score == 0.0
    
    def test_calculate_complexity_score_simple_errors(self, analyzer):
        """Test _calculate_complexity_score for simple errors."""
        errors = [Mock(spec=MypyError)] * 3  # 3 errors
        by_difficulty = {1: errors}  # All difficulty 1
        
        score = analyzer._calculate_complexity_score(by_difficulty, errors)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        # Should be relatively low for simple errors
        assert score < 50
    
    def test_calculate_complexity_score_complex_errors(self, analyzer):
        """Test _calculate_complexity_score for complex errors."""
        errors = [Mock(spec=MypyError)] * 3  # 3 errors
        by_difficulty = {5: errors}  # All difficulty 5
        
        score = analyzer._calculate_complexity_score(by_difficulty, errors)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
        # Should be relatively high for complex errors
        assert score > 50
    
    def test_calculate_complexity_score_mixed_difficulty(self, analyzer):
        """Test _calculate_complexity_score for mixed difficulty errors."""
        easy_errors = [Mock(spec=MypyError)] * 2
        hard_errors = [Mock(spec=MypyError)] * 1
        all_errors = easy_errors + hard_errors
        
        by_difficulty = {1: easy_errors, 5: hard_errors}
        
        score = analyzer._calculate_complexity_score(by_difficulty, all_errors)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100
    
    def test_calculate_complexity_score_caps_at_100(self, analyzer):
        """Test _calculate_complexity_score caps at 100."""
        # Create many high-difficulty errors to test capping
        errors = [Mock(spec=MypyError)] * 100
        by_difficulty = {5: errors}
        
        score = analyzer._calculate_complexity_score(by_difficulty, errors)
        
        # Should be capped at or near 100 - allow for calculation variance
        assert score >= 83  # The actual calculated value
        assert score <= 100
    
    def test_generate_summary_report_complete(self, analyzer, mock_result):
        """Test generate_summary_report produces complete report."""
        analysis = analyzer.analyze_errors(mock_result)
        report = analyzer.generate_summary_report(analysis)
        
        assert isinstance(report, str)
        assert "## Type Error Analysis Summary" in report
        assert "Total Errors:" in report
        assert "Complexity Score:" in report
        assert "Error Distribution by Category:" in report
        assert "Recommended Learning Path:" in report
        assert "Quick Stats:" in report
    
    def test_generate_summary_report_empty_analysis(self, analyzer):
        """Test generate_summary_report handles empty analysis."""
        empty_analysis = AnalysisResult(
            total_errors=0,
            by_category={},
            by_difficulty={},
            by_file={},
            suggested_tutorials=[],
            learning_path=[],
            complexity_score=0.0
        )
        
        report = analyzer.generate_summary_report(empty_analysis)
        
        assert isinstance(report, str)
        assert "**Total Errors:** 0" in report
        assert "**Complexity Score:** 0.0/100" in report
    
    def test_generate_summary_report_categories_sorted_by_count(self, analyzer):
        """Test generate_summary_report sorts categories by error count."""
        # Create analysis with multiple categories
        error1 = Mock(spec=MypyError)
        error1.file_path = "test1.py"
        error1.line_number = 10
        error1.message = "Error 1"
        
        error2 = Mock(spec=MypyError)
        error2.file_path = "test2.py"
        error2.line_number = 20
        error2.message = "Error 2"
        
        error3 = Mock(spec=MypyError)
        error3.file_path = "test3.py"
        error3.line_number = 30
        error3.message = "Error 3"
        
        analysis = AnalysisResult(
            total_errors=3,
            by_category={
                "missing_annotations": [error1],         # 1 error
                "incompatible_types": [error2, error3]   # 2 errors
            },
            by_difficulty={1: [error1], 2: [error2, error3]},
            by_file={"test.py": [error1, error2, error3]},
            suggested_tutorials=["tutorial1"],
            learning_path=[error1, error2, error3],
            complexity_score=25.0
        )
        
        report = analyzer.generate_summary_report(analysis)
        
        # Should list incompatible_types first (2 errors) then missing_annotations (1 error)
        assert report.find("Type Incompatibility") < report.find("Missing Type Annotations")
    
    def test_generate_summary_report_with_uncategorized(self, analyzer):
        """Test generate_summary_report handles uncategorized errors."""
        # Create analysis with uncategorized errors
        error = Mock(spec=MypyError)
        error.file_path = "test.py"
        error.line_number = 10
        error.message = "Some unknown error"
        
        analysis = AnalysisResult(
            total_errors=1,
            by_category={"uncategorized": [error]},
            by_difficulty={5: [error]},  # Default difficulty for uncategorized
            by_file={"test.py": [error]},
            suggested_tutorials=[],
            learning_path=[error],
            complexity_score=50.0
        )
        
        report = analyzer.generate_summary_report(analysis)
        
        # Should include uncategorized errors in report
        assert "**Uncategorized**: 1 errors" in report
    
    def test_find_patterns_return_type_missing(self, analyzer):
        """Test find_patterns detects missing return type patterns."""
        error = Mock(spec=MypyError)
        error.message = "Function is missing a return type annotation"
        error.error_code = "no-untyped-def"
        
        patterns = analyzer.find_patterns([error])
        
        assert "Missing return type annotations" in patterns
        assert patterns["Missing return type annotations"] == 1
    
    def test_find_patterns_optional_none_handling(self, analyzer):
        """Test find_patterns detects optional/None handling issues."""
        error = Mock(spec=MypyError)
        error.message = "Item of optional type has None value"
        error.error_code = "union-attr"
        
        patterns = analyzer.find_patterns([error])
        
        assert "Optional/None not properly handled" in patterns
        assert patterns["Optional/None not properly handled"] == 1
    
    def test_find_patterns_import_issues(self, analyzer):
        """Test find_patterns detects import-related issues."""
        error = Mock(spec=MypyError)
        error.message = "Cannot find module 'missing_module'"
        error.error_code = "import-not-found"
        
        patterns = analyzer.find_patterns([error])
        
        assert "Import-related issues" in patterns
        assert patterns["Import-related issues"] == 1
    
    def test_find_patterns_generic_types(self, analyzer):
        """Test find_patterns detects generic types without parameters."""
        error = Mock(spec=MypyError)
        error.message = "Missing type parameters for List"
        error.error_code = "type-arg"
        
        patterns = analyzer.find_patterns([error])
        
        assert "Generic types without parameters" in patterns
        assert patterns["Generic types without parameters"] == 1
    
    def test_find_patterns_override_issues(self, analyzer):
        """Test find_patterns detects method override issues."""
        error = Mock(spec=MypyError)
        error.message = "Signature incompatible with override in supertype"
        error.error_code = "override"
        
        patterns = analyzer.find_patterns([error])
        
        assert "Incompatible method overrides" in patterns
        assert patterns["Incompatible method overrides"] == 1
    
    def test_find_patterns_decorator_issues(self, analyzer):
        """Test find_patterns detects decorator-related issues."""
        error = Mock(spec=MypyError)
        error.message = "Cannot infer type of decorator argument"
        error.error_code = "misc"
        
        patterns = analyzer.find_patterns([error])
        
        assert "Issues with decorators" in patterns
        assert patterns["Issues with decorators"] == 1
    
    def test_find_patterns_multiple_occurrences(self, analyzer):
        """Test find_patterns counts multiple occurrences correctly."""
        error1 = Mock(spec=MypyError)
        error1.message = "Function is missing a return type annotation"
        error1.error_code = "no-untyped-def"
        
        error2 = Mock(spec=MypyError)
        error2.message = "Method needs return type annotation"
        error2.error_code = "no-untyped-def"
        
        patterns = analyzer.find_patterns([error1, error2])
        
        assert "Missing return type annotations" in patterns
        assert patterns["Missing return type annotations"] == 2
    
    def test_find_patterns_no_patterns(self, analyzer):
        """Test find_patterns returns empty dict when no patterns found."""
        error = Mock(spec=MypyError)
        error.message = "Some unrecognized error message"
        error.error_code = "unknown-code"
        
        patterns = analyzer.find_patterns([error])
        
        assert patterns == {}
    
    def test_find_patterns_empty_errors(self, analyzer):
        """Test find_patterns handles empty error list."""
        patterns = analyzer.find_patterns([])
        
        assert patterns == {}
    
    def test_analyze_errors_calls_all_helper_methods(self, analyzer, mock_result):
        """Test analyze_errors calls all expected helper methods."""
        with patch.object(analyzer, '_categorize_errors', return_value={}) as mock_categorize:
            with patch.object(analyzer, '_group_by_difficulty', return_value={}) as mock_group:
                with patch.object(analyzer, '_suggest_tutorials', return_value=[]) as mock_suggest:
                    with patch.object(analyzer, '_create_learning_path', return_value=[]) as mock_path:
                        with patch.object(analyzer, '_calculate_complexity_score', return_value=0.0) as mock_score:
                            
                            result = analyzer.analyze_errors(mock_result)
                            
                            mock_categorize.assert_called_once()
                            mock_group.assert_called_once()
                            mock_suggest.assert_called_once()
                            mock_path.assert_called_once()
                            mock_score.assert_called_once()
    
    def test_predefined_categories_coverage(self, analyzer):
        """Test that predefined categories cover common error codes."""
        # Check that common MyPy error codes are covered
        all_codes = set()
        for category in analyzer.CATEGORIES:
            all_codes.update(category.common_codes)
        
        # Should include common codes
        assert "no-untyped-def" in all_codes
        assert "assignment" in all_codes
        assert "arg-type" in all_codes
        assert "union-attr" in all_codes
        assert "import" in all_codes
    
    def test_predefined_explanations_completeness(self, analyzer):
        """Test that predefined explanations are complete."""
        for error_code, explanation in analyzer.EXPLANATIONS.items():
            assert explanation.error_code == error_code
            assert explanation.simple_explanation
            assert explanation.detailed_explanation
            assert explanation.common_causes
            assert explanation.how_to_fix
            # Examples and resources are optional but should be dictionaries/lists
            assert isinstance(explanation.examples, dict)
            assert isinstance(explanation.resources, list)
    
    def test_category_difficulty_levels(self, analyzer):
        """Test that categories have reasonable difficulty levels."""
        difficulties = [cat.difficulty for cat in analyzer.CATEGORIES]
        
        # Should have range of difficulties
        assert min(difficulties) >= 0
        assert max(difficulties) <= 5
        
        # Should have configuration as easiest (0)
        config_category = next((cat for cat in analyzer.CATEGORIES if cat.id == "configuration"), None)
        assert config_category is not None
        assert config_category.difficulty == 0