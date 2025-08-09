"""
Coverage Insights Generator
============================
Generates actionable insights for improving test coverage.
"""

import os
import random
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from .models import CoverageInfo


@dataclass
class CoverageInsight:
    """A single actionable coverage insight."""
    filepath: str
    line_number: int
    code_line: str
    context_before: List[str]
    context_after: List[str]
    coverage_percent: float
    suggestion: str
    category: str  # e.g., "error_handling", "conditional", "return_value"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON export."""
        return asdict(self)
    
    @property
    def clickable_reference(self) -> str:
        """Get clickable file:line reference for terminals."""
        return f"{self.filepath}:{self.line_number}"


class CoverageInsights:
    """Generates actionable insights for improving coverage."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        
    def get_actionable_insights(
        self,
        coverage_data: Dict[str, CoverageInfo],
        num_files: int = 3,
        lines_per_file: int = 1
    ) -> List[CoverageInsight]:
        """Generate specific actionable insights for improving coverage."""
        insights = []
        
        # Filter files that need improvement (exclude _total and 100% covered)
        improvable_files = [
            (filepath, info) for filepath, info in coverage_data.items()
            if filepath != "_total" and info.coverage_percent < 100 and info.missing_lines
        ]
        
        if not improvable_files:
            return insights
        
        # Sort by coverage (lowest first) then take random sample
        improvable_files.sort(key=lambda x: x[1].coverage_percent)
        
        # Prioritize files with lowest coverage but also include some random ones
        priority_files = improvable_files[:num_files//2] if len(improvable_files) > num_files//2 else improvable_files
        remaining_files = [f for f in improvable_files if f not in priority_files]
        
        if remaining_files and len(priority_files) < num_files:
            sample_size = min(num_files - len(priority_files), len(remaining_files))
            random_files = random.sample(remaining_files, sample_size)
            selected_files = priority_files + random_files
        else:
            selected_files = priority_files[:num_files]
        
        # Generate insights for each selected file
        for filepath, info in selected_files:
            file_insights = self._get_file_insights(filepath, info, lines_per_file)
            insights.extend(file_insights)
            
        return insights
    
    def _get_file_insights(
        self,
        filepath: str,
        info: CoverageInfo,
        num_lines: int = 1
    ) -> List[CoverageInsight]:
        """Get insights for a specific file."""
        insights = []
        
        if not info.missing_lines:
            return insights
        
        # Construct full file path
        if filepath.startswith("/"):
            full_path = Path(filepath)
        else:
            full_path = self.project_root / filepath
        
        if not full_path.exists():
            return insights
        
        try:
            with open(full_path, 'r') as f:
                lines = f.readlines()
        except Exception:
            return insights
        
        # Select random uncovered lines
        selected_lines = random.sample(
            info.missing_lines,
            min(num_lines, len(info.missing_lines))
        )
        
        for line_num in selected_lines:
            if 0 < line_num <= len(lines):
                insight = self._create_insight(
                    filepath, line_num, lines, info.coverage_percent
                )
                if insight:
                    insights.append(insight)
                    
        return insights
    
    def _create_insight(
        self,
        filepath: str,
        line_num: int,
        lines: List[str],
        coverage_percent: float
    ) -> Optional[CoverageInsight]:
        """Create an insight for a specific line."""
        # Line numbers are 1-based, list is 0-based
        idx = line_num - 1
        
        if idx >= len(lines):
            return None
        
        code_line = lines[idx].rstrip()
        
        # Get context (2 lines before and after)
        context_before = []
        for i in range(max(0, idx - 2), idx):
            context_before.append(f"{i+1:4}: {lines[i].rstrip()}")
            
        context_after = []
        for i in range(idx + 1, min(len(lines), idx + 3)):
            context_after.append(f"{i+1:4}: {lines[i].rstrip()}")
        
        # Generate suggestion based on code pattern
        suggestion, category = self._generate_suggestion(code_line)
        
        return CoverageInsight(
            filepath=filepath,
            line_number=line_num,
            code_line=code_line.strip(),
            context_before=context_before,
            context_after=context_after,
            coverage_percent=coverage_percent,
            suggestion=suggestion,
            category=category
        )
    
    def _generate_suggestion(self, code_line: str) -> Tuple[str, str]:
        """Generate a test suggestion based on the code pattern."""
        line = code_line.strip()
        
        # Error handling patterns
        if 'raise' in line:
            exception_type = self._extract_exception_type(line)
            return (f"Add test for {exception_type} exception", "error_handling")
        
        if line.startswith('except'):
            exception_type = self._extract_exception_from_except(line)
            return (f"Add test that triggers {exception_type} exception", "exception_handling")
        
        # Conditional patterns
        if line.startswith('if '):
            condition = self._extract_condition(line)
            if 'not' in condition:
                return ("Add test for negative condition (when condition is False)", "conditional")
            elif 'is None' in condition:
                return ("Add test for None value case", "null_check")
            elif '==' in condition or '!=' in condition:
                return ("Add test for this equality condition", "equality_check")
            elif '<' in condition or '>' in condition:
                return ("Add test for boundary condition", "boundary_check")
            else:
                return ("Add test for this conditional branch", "conditional")
        
        if line.startswith('elif '):
            return ("Add test for this alternative condition branch", "conditional")
        
        if line.startswith('else:'):
            return ("Add test for else branch", "conditional")
        
        # Return patterns
        if 'return None' in line:
            return ("Add test for None return case", "return_value")
        
        if 'return False' in line or 'return false' in line.lower():
            return ("Add test for False return case", "return_value")
        
        if 'return True' in line or 'return true' in line.lower():
            return ("Add test for True return case", "return_value")
        
        if line.startswith('return '):
            return ("Add test for this return value", "return_value")
        
        # Loop patterns
        if line.startswith('for ') or line.startswith('while '):
            return ("Add test that enters this loop", "iteration")
        
        if 'break' in line:
            return ("Add test that triggers loop break", "control_flow")
        
        if 'continue' in line:
            return ("Add test that triggers loop continue", "control_flow")
        
        # Function/method calls
        if '(' in line and ')' in line and not line.startswith('def ') and not line.startswith('class '):
            return ("Add test that executes this function call", "function_call")
        
        # Default suggestion
        return ("Add test to cover this code path", "general")
    
    def _extract_exception_type(self, line: str) -> str:
        """Extract exception type from a raise statement."""
        if 'raise ' in line:
            parts = line.split('raise ')[1].split('(')[0].strip()
            return parts if parts else "exception"
        return "exception"
    
    def _extract_exception_from_except(self, line: str) -> str:
        """Extract exception type from an except clause."""
        if 'except ' in line:
            parts = line.split('except ')[1].split(':')[0].split(' as ')[0].strip()
            return parts if parts else "exception"
        return "exception"
    
    def _extract_condition(self, line: str) -> str:
        """Extract condition from an if statement."""
        if 'if ' in line:
            return line.split('if ')[1].rstrip(':').strip()
        return "condition"
    
    def get_ai_friendly_insights(
        self,
        coverage_data: Dict[str, CoverageInfo],
        num_files: int = 5
    ) -> Dict[str, Any]:
        """Return insights in a format easy for AI to use."""
        insights = self.get_actionable_insights(coverage_data, num_files, lines_per_file=3)
        
        # Group insights by file
        files_data = {}
        for insight in insights:
            if insight.filepath not in files_data:
                files_data[insight.filepath] = {
                    "path": insight.filepath,
                    "current_coverage": insight.coverage_percent,
                    "uncovered_samples": [],
                    "suggestions": []
                }
            
            files_data[insight.filepath]["uncovered_samples"].append({
                "line": insight.line_number,
                "code": insight.code_line,
                "category": insight.category,
                "context": {
                    "before": insight.context_before,
                    "after": insight.context_after
                }
            })
            files_data[insight.filepath]["suggestions"].append(
                f"Line {insight.line_number}: {insight.suggestion}"
            )
        
        return {
            "total_files_analyzed": len(files_data),
            "files_to_improve": list(files_data.values()),
            "quick_command": "python -m pytest tests/ --cov=storm_checker --cov-report=term-missing",
            "instructions": "Focus on the uncovered_samples to write targeted tests"
        }
    
    def export_insights(self, insights: List[CoverageInsight], filepath: str):
        """Export insights to JSON file."""
        data = {
            "insights": [insight.to_dict() for insight in insights],
            "summary": {
                "total_insights": len(insights),
                "files_covered": len(set(i.filepath for i in insights)),
                "categories": dict(
                    (cat, sum(1 for i in insights if i.category == cat))
                    for cat in set(i.category for i in insights)
                )
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
        return filepath