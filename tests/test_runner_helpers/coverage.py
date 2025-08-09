"""
Coverage Analyzer for Test Runner
==================================
Handles coverage collection and analysis.
"""

import subprocess
import sys
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import CoverageInfo
from .parser import ResultParser


class CoverageAnalyzer:
    """Handles coverage collection and reporting."""
    
    def __init__(self, args):
        self.args = args
        self.parser = ResultParser()
        self.test_dir = Path(__file__).parent.parent
        self.project_root = self.test_dir.parent
        
    def run_coverage(self, test_files: Optional[List[str]] = None) -> Dict[str, CoverageInfo]:
        """Run coverage collection on test files."""
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "--cov=storm_checker",
            "--cov-report=term-missing",
            "--cov-report=html",
            "-q", "--tb=no"
        ]
        
        # Add specific test files if provided
        if test_files:
            cmd.extend(test_files)
            
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0 or result.stdout:
                return self.parser.parse_coverage_output(result.stdout)
                
        except subprocess.TimeoutExpired:
            print("Coverage collection timed out")
        except Exception as e:
            print(f"Could not collect coverage: {e}")
            
        return {}
        
    def find_uncovered_lines(self, filepath: str, missing_lines: List[int]) -> List[Tuple[int, str]]:
        """Find actual code for uncovered lines."""
        uncovered = []
        full_path = self.project_root / filepath
        
        if not full_path.exists():
            return uncovered
            
        try:
            with open(full_path, 'r') as f:
                lines = f.readlines()
                
            for line_num in missing_lines[:10]:  # Limit to first 10
                if 0 < line_num <= len(lines):
                    code = lines[line_num - 1].strip()
                    if code and not code.startswith('#'):
                        uncovered.append((line_num, code))
                        
        except Exception:
            pass
            
        return uncovered
        
    def get_coverage_suggestions(self, coverage_data: Dict[str, CoverageInfo]) -> List[str]:
        """Generate suggestions for improving coverage."""
        suggestions = []
        
        # Find files with low coverage
        low_coverage = []
        for filepath, info in coverage_data.items():
            if filepath != "_total" and info.coverage_percent < 80:
                low_coverage.append((filepath, info))
                
        if low_coverage:
            # Sort by coverage percent
            low_coverage.sort(key=lambda x: x[1].coverage_percent)
            
            # Suggest focusing on worst files
            worst = low_coverage[0]
            suggestions.append(
                f"Focus on {worst[0]} - only {worst[1].coverage_percent:.1f}% covered "
                f"({worst[1].missed} lines missing)"
            )
            
            # Quick wins - files close to threshold
            quick_wins = [
                (f, i) for f, i in coverage_data.items()
                if f != "_total" and 75 <= i.coverage_percent < 80
            ]
            
            if quick_wins:
                suggestions.append(
                    f"Quick wins: {len(quick_wins)} files are close to 80% coverage"
                )
                
        # Overall coverage
        total = coverage_data.get("_total")
        if total:
            if total.coverage_percent < 80:
                suggestions.append(
                    f"Overall coverage is {total.coverage_percent:.1f}% - "
                    f"aim for at least 80%"
                )
            elif total.coverage_percent < 90:
                suggestions.append(
                    f"Good coverage at {total.coverage_percent:.1f}% - "
                    f"consider aiming for 90%+"
                )
            else:
                suggestions.append(
                    f"Excellent coverage at {total.coverage_percent:.1f}%!"
                )
                
        return suggestions
        
    def get_random_uncovered_line(self, 
                                 filepath: str,
                                 missing_lines: List[int]) -> Optional[Tuple[int, str]]:
        """Get a random uncovered line for display."""
        if not missing_lines:
            return None
            
        full_path = self.project_root / filepath
        if not full_path.exists():
            return None
            
        try:
            with open(full_path, 'r') as f:
                lines = f.readlines()
                
            # Try up to 10 times to find a meaningful line
            for _ in range(min(10, len(missing_lines))):
                line_num = random.choice(missing_lines)
                
                if 0 < line_num <= len(lines):
                    code = lines[line_num - 1].strip()
                    
                    # Skip empty lines, comments, and simple statements
                    if (code and 
                        not code.startswith('#') and
                        not code in ['pass', 'continue', 'break'] and
                        len(code) > 5):
                        return (line_num, code)
                        
        except Exception:
            pass
            
        return None
        
    def format_missing_lines(self, lines: List[int]) -> str:
        """Format missing line numbers compactly."""
        if not lines:
            return ""
            
        lines = sorted(lines)
        ranges = []
        start = lines[0]
        end = lines[0]
        
        for line in lines[1:]:
            if line == end + 1:
                end = line
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = line
                end = line
                
        # Add last range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")
            
        # Limit to first 5 ranges
        if len(ranges) > 5:
            return ", ".join(ranges[:5]) + "..."
            
        return ", ".join(ranges)