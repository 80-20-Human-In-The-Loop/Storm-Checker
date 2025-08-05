#!/usr/bin/env python3
"""Error analysis and educational categorization for MyPy errors.

This module analyzes MyPy errors to determine their educational value,
suggests appropriate tutorials, and helps prioritize which errors to fix first
for maximum learning benefit.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, Counter

from .mypy_runner import MypyError, MypyResult


@dataclass
class ErrorCategory:
    """Represents a category of type errors for educational purposes.
    
    Attributes:
        id: Unique identifier for the category.
        name: Display name of the category.
        description: Detailed description of what this category covers.
        difficulty: Difficulty level (1-5, where 1 is easiest).
        common_codes: Set of MyPy error codes that belong to this category.
        tutorial_id: ID of the tutorial that teaches about this category.
        examples: Example error messages for this category.
    """
    id: str
    name: str
    description: str
    difficulty: int
    common_codes: Set[str]
    tutorial_id: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    
    def matches_error(self, error: MypyError) -> bool:
        """Check if an error belongs to this category.
        
        Args:
            error: MyPy error to check.
            
        Returns:
            True if the error matches this category.
        """
        if error.error_code and error.error_code in self.common_codes:
            return True
        
        # Check message patterns for errors without codes
        # TODO: Add pattern matching for specific error messages
        
        return False


@dataclass
class ErrorExplanation:
    """Educational explanation for a specific error.
    
    Attributes:
        error_code: MyPy error code this explanation is for.
        simple_explanation: Simple, beginner-friendly explanation.
        detailed_explanation: More detailed technical explanation.
        common_causes: List of common causes for this error.
        how_to_fix: Step-by-step guide to fixing this error.
        examples: Code examples showing the error and fix.
        resources: Links or references for further learning.
    """
    error_code: str
    simple_explanation: str
    detailed_explanation: str
    common_causes: List[str]
    how_to_fix: List[str]
    examples: Dict[str, str] = field(default_factory=dict)
    resources: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Result of analyzing a set of MyPy errors.
    
    Attributes:
        total_errors: Total number of errors analyzed.
        by_category: Errors grouped by category.
        by_difficulty: Errors grouped by difficulty level.
        by_file: Errors grouped by file.
        suggested_tutorials: Recommended tutorials based on errors.
        learning_path: Suggested order to fix errors for best learning.
        complexity_score: Overall complexity score (0-100).
    """
    total_errors: int
    by_category: Dict[str, List[MypyError]]
    by_difficulty: Dict[int, List[MypyError]]
    by_file: Dict[str, List[MypyError]]
    suggested_tutorials: List[str]
    learning_path: List[MypyError]
    complexity_score: float


class ErrorAnalyzer:
    """Analyzes MyPy errors for educational insights."""
    
    # Error categories for educational grouping
    CATEGORIES = [
        ErrorCategory(
            id="configuration",
            name="Configuration Issues",
            description="MyPy setup and configuration problems",
            difficulty=0,  # Must fix first
            common_codes={"config-error"},
            tutorial_id="pyproject_setup",
            examples=[
                "Source file found twice under different module names",
                "Library stubs not installed",
                "Missing pyproject.toml configuration"
            ]
        ),
        ErrorCategory(
            id="missing_annotations",
            name="Missing Type Annotations",
            description="Functions or variables lacking type hints",
            difficulty=1,
            common_codes={"no-untyped-def", "no-untyped-call", "var-annotated"},
            tutorial_id="type_annotations_basics",
            examples=[
                "Function is missing a type annotation",
                "Call to untyped function",
                "Need type annotation for variable"
            ]
        ),
        ErrorCategory(
            id="incompatible_types",
            name="Type Incompatibility",
            description="Assigning or passing values of wrong types",
            difficulty=2,
            common_codes={"assignment", "arg-type", "return-value", "no-any-return", "valid-type"},
            tutorial_id="type_compatibility",
            examples=[
                "Incompatible types in assignment",
                "Argument has incompatible type",
                "Incompatible return value type"
            ]
        ),
        ErrorCategory(
            id="optional_none",
            name="Optional and None Handling",
            description="Issues with nullable types and None checks",
            difficulty=3,
            common_codes={"union-attr", "possibly-undefined", "optional-operand"},
            tutorial_id="optional_types",
            examples=[
                "Item of Union has no attribute",
                "Variable may be undefined",
                "Unsupported operand types (None)"
            ]
        ),
        ErrorCategory(
            id="generics",
            name="Generic Types",
            description="Problems with generic types like List, Dict",
            difficulty=3,
            common_codes={"type-arg", "missing-type-arg", "index"},
            tutorial_id="generic_types",
            examples=[
                "Missing type parameters",
                "Invalid type argument",
                "Invalid index type"
            ]
        ),
        ErrorCategory(
            id="inheritance",
            name="Inheritance and Protocols",
            description="Issues with class inheritance and protocols",
            difficulty=4,
            common_codes={"override", "misc", "type-abstract", "override-error"},
            tutorial_id="inheritance_protocols",
            examples=[
                "Signature incompatible with supertype",
                "Cannot instantiate abstract class",
                "Protocol member not implemented"
            ]
        ),
        ErrorCategory(
            id="imports",
            name="Import and Module Issues",
            description="Problems with imports and module types",
            difficulty=2,
            common_codes={"import", "import-untyped", "import-not-found", "no-redef", "attr-defined", "name-defined"},
            tutorial_id="imports_modules",
            examples=[
                "Cannot find module",
                "Module has no attribute",
                "Name already defined"
            ]
        ),
        ErrorCategory(
            id="advanced",
            name="Advanced Type Features",
            description="Complex typing features like overloads, type vars",
            difficulty=5,
            common_codes={"overload-impl", "type-var", "literal-required"},
            tutorial_id="advanced_typing",
            examples=[
                "Overloaded implementation not consistent",
                "Invalid type variable usage",
                "Literal type required"
            ]
        ),
    ]
    
    # Common error explanations
    EXPLANATIONS = {
        "no-untyped-def": ErrorExplanation(
            error_code="no-untyped-def",
            simple_explanation="This function needs type hints to specify what types of arguments it accepts and what it returns.",
            detailed_explanation="MyPy requires function signatures to have type annotations. This helps catch type-related bugs early and makes code more readable.",
            common_causes=[
                "Function definition without type hints",
                "Legacy code that hasn't been updated",
                "Quick prototypes that grew into production code"
            ],
            how_to_fix=[
                "Add type hints to all function parameters",
                "Add a return type annotation with ->",
                "Use 'Any' temporarily if unsure of the type",
                "Run MyPy with --no-untyped-def to find all occurrences"
            ],
            examples={
                "before": "def calculate_total(items, tax_rate):\n    return sum(items) * (1 + tax_rate)",
                "after": "def calculate_total(items: List[float], tax_rate: float) -> float:\n    return sum(items) * (1 + tax_rate)"
            },
            resources=[
                "PEP 484 - Type Hints",
                "MyPy documentation on function annotations"
            ]
        ),
        "assignment": ErrorExplanation(
            error_code="assignment",
            simple_explanation="You're trying to assign a value of one type to a variable of a different type.",
            detailed_explanation="Type safety means variables should only hold values of their declared type. This error occurs when trying to violate that constraint.",
            common_causes=[
                "Mixing strings and numbers",
                "Assigning None to non-optional variables",
                "Incorrect type annotations",
                "API changes that return different types"
            ],
            how_to_fix=[
                "Check the types on both sides of the assignment",
                "Use type casting if the conversion is safe",
                "Update the variable's type annotation",
                "Use Union types if the variable can hold multiple types"
            ],
            examples={
                "before": "count: int = '42'  # Error: incompatible types",
                "after": "count: int = int('42')  # Convert string to int"
            }
        ),
        "arg-type": ErrorExplanation(
            error_code="arg-type",
            simple_explanation="You're passing the wrong type of argument to a function.",
            detailed_explanation="Functions expect specific types for their parameters. This error means the argument type doesn't match what the function expects.",
            common_causes=[
                "Passing string instead of number",
                "Forgetting to convert types",
                "API misunderstanding",
                "Optional parameters without None checks"
            ],
            how_to_fix=[
                "Check the function's expected parameter types",
                "Convert the argument to the correct type",
                "Use isinstance() to check types at runtime",
                "Update function signature if it should accept multiple types"
            ],
            examples={
                "before": "math.sqrt('16')  # Error: expects float, not str",
                "after": "math.sqrt(float('16'))  # Convert to float first"
            }
        ),
        "union-attr": ErrorExplanation(
            error_code="union-attr",
            simple_explanation="You're trying to access an attribute that might not exist because the variable could be None or another type.",
            detailed_explanation="When a variable can be multiple types (Union), you must check which type it is before accessing type-specific attributes.",
            common_causes=[
                "Forgetting to check for None",
                "Not narrowing Union types",
                "Assuming optional values are always present"
            ],
            how_to_fix=[
                "Add explicit None checks",
                "Use isinstance() to narrow types",
                "Use the walrus operator for concise checks",
                "Consider using TypeGuard functions"
            ],
            examples={
                "before": "def get_length(text: Optional[str]) -> int:\n    return len(text)  # Error: text might be None",
                "after": "def get_length(text: Optional[str]) -> int:\n    if text is None:\n        return 0\n    return len(text)"
            }
        ),
    }
    
    def __init__(self):
        """Initialize the error analyzer."""
        pass
    
    def analyze_errors(self, result: MypyResult) -> AnalysisResult:
        """Analyze MyPy errors for educational insights.
        
        Args:
            result: MyPy result containing errors to analyze.
            
        Returns:
            Analysis result with categorized errors and recommendations.
            
        Example:
            >>> analyzer = ErrorAnalyzer()
            >>> analysis = analyzer.analyze_errors(mypy_result)
            >>> print(f"Complexity score: {analysis.complexity_score:.1f}/100")
            Complexity score: 42.5/100
        """
        errors = result.errors
        
        # Group by category
        by_category = self._categorize_errors(errors)
        
        # Group by difficulty
        by_difficulty = self._group_by_difficulty(errors, by_category)
        
        # Group by file
        by_file = result.get_errors_by_file()
        
        # Suggest tutorials
        suggested_tutorials = self._suggest_tutorials(by_category)
        
        # Create learning path
        learning_path = self._create_learning_path(errors, by_category)
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(by_difficulty, errors)
        
        return AnalysisResult(
            total_errors=len(errors),
            by_category=by_category,
            by_difficulty=by_difficulty,
            by_file=by_file,
            suggested_tutorials=suggested_tutorials,
            learning_path=learning_path,
            complexity_score=complexity_score
        )
    
    def get_explanation(self, error: MypyError) -> Optional[ErrorExplanation]:
        """Get educational explanation for a specific error.
        
        Args:
            error: MyPy error to explain.
            
        Returns:
            Explanation if available, None otherwise.
            
        Example:
            >>> analyzer = ErrorAnalyzer()
            >>> explanation = analyzer.get_explanation(mypy_error)
            >>> if explanation:
            ...     print(explanation.simple_explanation)
        """
        if error.error_code and error.error_code in self.EXPLANATIONS:
            return self.EXPLANATIONS[error.error_code]
        
        # TODO: Add dynamic explanation generation based on error message
        
        return None
    
    def suggest_fix_order(self, errors: List[MypyError]) -> List[MypyError]:
        """Suggest order to fix errors for best learning experience.
        
        Args:
            errors: List of errors to order.
            
        Returns:
            Ordered list of errors, easiest to hardest.
            
        Example:
            >>> analyzer = ErrorAnalyzer()
            >>> ordered = analyzer.suggest_fix_order(errors)
            >>> for error in ordered[:5]:
            ...     print(f"Fix: {error}")
        """
        # First categorize errors
        by_category = self._categorize_errors(errors)
        
        # Sort by difficulty and educational value
        def sort_key(error: MypyError) -> Tuple[int, int, str]:
            # Find category difficulty
            difficulty = 5  # Default to hardest
            for category in self.CATEGORIES:
                if category.matches_error(error):
                    difficulty = category.difficulty
                    break
            
            # Prioritize errors with explanations
            has_explanation = 0 if error.error_code in self.EXPLANATIONS else 1
            
            # Secondary sort by file path for grouping
            return (difficulty, has_explanation, error.file_path)
        
        return sorted(errors, key=sort_key)
    
    def _categorize_errors(self, errors: List[MypyError]) -> Dict[str, List[MypyError]]:
        """Categorize errors by educational category.
        
        Args:
            errors: List of errors to categorize.
            
        Returns:
            Dictionary mapping category IDs to errors.
        """
        categorized: Dict[str, List[MypyError]] = defaultdict(list)
        uncategorized: List[MypyError] = []
        
        for error in errors:
            matched = False
            for category in self.CATEGORIES:
                if category.matches_error(error):
                    categorized[category.id].append(error)
                    matched = True
                    break
            
            if not matched:
                uncategorized.append(error)
        
        if uncategorized:
            categorized["uncategorized"] = uncategorized
        
        return dict(categorized)
    
    def _group_by_difficulty(
        self,
        errors: List[MypyError],
        by_category: Dict[str, List[MypyError]]
    ) -> Dict[int, List[MypyError]]:
        """Group errors by difficulty level.
        
        Args:
            errors: All errors.
            by_category: Errors already grouped by category.
            
        Returns:
            Dictionary mapping difficulty (1-5) to errors.
        """
        by_difficulty: Dict[int, List[MypyError]] = defaultdict(list)
        
        # Map categories to difficulties
        category_difficulty = {cat.id: cat.difficulty for cat in self.CATEGORIES}
        
        for category_id, category_errors in by_category.items():
            difficulty = category_difficulty.get(category_id, 5)  # Default to hardest
            by_difficulty[difficulty].extend(category_errors)
        
        return dict(by_difficulty)
    
    def _suggest_tutorials(self, by_category: Dict[str, List[MypyError]]) -> List[str]:
        """Suggest tutorials based on error categories.
        
        Args:
            by_category: Errors grouped by category.
            
        Returns:
            List of tutorial IDs, ordered by priority.
        """
        # Count errors per category
        category_counts = {
            cat_id: len(errors) for cat_id, errors in by_category.items()
        }
        
        # Get tutorials for categories with errors
        tutorials = []
        for category in self.CATEGORIES:
            if category.id in category_counts and category.tutorial_id:
                # Weight by error count and difficulty
                weight = category_counts[category.id] * (6 - category.difficulty)
                tutorials.append((category.tutorial_id, weight))
        
        # Sort by weight (highest first)
        tutorials.sort(key=lambda x: x[1], reverse=True)
        
        return [tutorial_id for tutorial_id, _ in tutorials]
    
    def _create_learning_path(
        self,
        errors: List[MypyError],
        by_category: Dict[str, List[MypyError]]
    ) -> List[MypyError]:
        """Create optimal learning path through errors.
        
        Args:
            errors: All errors.
            by_category: Errors grouped by category.
            
        Returns:
            Ordered list of errors for best learning experience.
        """
        learning_path = []
        
        # Start with easiest categories
        for category in sorted(self.CATEGORIES, key=lambda c: c.difficulty):
            if category.id in by_category:
                category_errors = by_category[category.id]
                
                # Within category, prioritize errors with explanations
                with_explanation = []
                without_explanation = []
                
                for error in category_errors:
                    if error.error_code in self.EXPLANATIONS:
                        with_explanation.append(error)
                    else:
                        without_explanation.append(error)
                
                # Add errors with explanations first
                learning_path.extend(sorted(with_explanation, key=lambda e: e.file_path))
                learning_path.extend(sorted(without_explanation, key=lambda e: e.file_path))
        
        # Add any uncategorized errors at the end
        if "uncategorized" in by_category:
            learning_path.extend(sorted(by_category["uncategorized"], key=lambda e: e.file_path))
        
        return learning_path
    
    def _calculate_complexity_score(
        self,
        by_difficulty: Dict[int, List[MypyError]],
        errors: List[MypyError]
    ) -> float:
        """Calculate overall complexity score (0-100).
        
        Args:
            by_difficulty: Errors grouped by difficulty.
            errors: All errors.
            
        Returns:
            Complexity score from 0 (simple) to 100 (very complex).
        """
        if not errors:
            return 0.0
        
        # Weight errors by difficulty
        weighted_sum = 0
        for difficulty, diff_errors in by_difficulty.items():
            weighted_sum += len(diff_errors) * difficulty
        
        # Normalize to 0-100 scale
        # Assume average of 10 errors per difficulty level is "moderate" (50)
        normalized = (weighted_sum / (len(errors) * 3)) * 50
        
        # Cap at 100
        return min(100.0, normalized)
    
    def generate_summary_report(self, analysis: AnalysisResult) -> str:
        """Generate a human-readable summary of the analysis.
        
        Args:
            analysis: Analysis result to summarize.
            
        Returns:
            Formatted summary report.
            
        Example:
            >>> analyzer = ErrorAnalyzer()
            >>> analysis = analyzer.analyze_errors(mypy_result)
            >>> print(analyzer.generate_summary_report(analysis))
        """
        lines = [
            "## Type Error Analysis Summary",
            "",
            f"**Total Errors:** {analysis.total_errors}",
            f"**Complexity Score:** {analysis.complexity_score:.1f}/100",
            "",
            "### Error Distribution by Category:",
            ""
        ]
        
        # Show categories sorted by error count
        sorted_categories = sorted(
            analysis.by_category.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )
        
        for cat_id, errors in sorted_categories:
            category = next((c for c in self.CATEGORIES if c.id == cat_id), None)
            if category:
                lines.append(f"- **{category.name}**: {len(errors)} errors (Difficulty: {category.difficulty}/5)")
            else:
                lines.append(f"- **Uncategorized**: {len(errors)} errors")
        
        lines.extend([
            "",
            "### Recommended Learning Path:",
            ""
        ])
        
        if analysis.suggested_tutorials:
            lines.append("1. Start with these tutorials:")
            for i, tutorial_id in enumerate(analysis.suggested_tutorials[:3], 1):
                lines.append(f"   - `stormcheck tutorial {tutorial_id}`")
        
        lines.append("")
        lines.append("2. Fix errors in this order (showing first 5):")
        for i, error in enumerate(analysis.learning_path[:5], 1):
            lines.append(f"   - {error.file_path}:{error.line_number} - {error.message[:50]}...")
        
        lines.extend([
            "",
            "### Quick Stats:",
            ""
        ])
        
        # Files with most errors
        sorted_files = sorted(
            analysis.by_file.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:3]
        
        if sorted_files:
            lines.append("Files with most errors:")
            for file_path, errors in sorted_files:
                lines.append(f"- {file_path}: {len(errors)} errors")
        
        return "\n".join(lines)
    
    def find_patterns(self, errors: List[MypyError]) -> Dict[str, int]:
        """Find common patterns in errors for educational insights.
        
        Args:
            errors: List of errors to analyze.
            
        Returns:
            Dictionary of pattern descriptions to counts.
            
        Example:
            >>> analyzer = ErrorAnalyzer()
            >>> patterns = analyzer.find_patterns(errors)
            >>> for pattern, count in patterns.items():
            ...     print(f"{pattern}: {count} occurrences")
        """
        patterns: Counter[str] = Counter()
        
        for error in errors:
            # Pattern: Missing return type
            if "return type" in error.message.lower():
                patterns["Missing return type annotations"] += 1
            
            # Pattern: Optional not handled
            if "none" in error.message.lower() and "optional" in error.message.lower():
                patterns["Optional/None not properly handled"] += 1
            
            # Pattern: Import issues
            if error.error_code and "import" in error.error_code:
                patterns["Import-related issues"] += 1
            
            # Pattern: List/Dict without type parameters
            if re.search(r'(List|Dict|Set|Tuple)\[?\]?', error.message):
                patterns["Generic types without parameters"] += 1
            
            # Pattern: Incompatible overrides
            if "override" in error.message.lower():
                patterns["Incompatible method overrides"] += 1
            
            # Pattern: Untyped decorators
            if "decorator" in error.message.lower():
                patterns["Issues with decorators"] += 1
        
        return dict(patterns)


# TODO: Add machine learning to improve error categorization
# TODO: Add support for custom error explanations
# TODO: Add integration with documentation links
# TODO: Add support for framework-specific error patterns
# TODO: Add error complexity scoring based on fix difficulty
# TODO: Create interactive error exploration mode