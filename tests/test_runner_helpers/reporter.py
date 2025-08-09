"""
Reporter for Test Runner
=========================
Handles all terminal output, progress display, and result reporting.
"""

import os
import sys
import time
import random
from pathlib import Path
from typing import List, Dict, Optional, Any
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.console import Console
from rich.theme import Theme

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from storm_checker.cli.colors import (
    ColorPrinter, print_header, print_success, print_error, print_warning, print_info,
    PALETTE, RESET, BOLD, DIM, CLEAR_SCREEN, CLEAR_LINE
)
from storm_checker.cli.components.border import Border, BorderStyle
from storm_checker.cli.components.progress_bar import ProgressBar

from .models import TestRunState, TestResult, TestFailure, SlowTest, CoverageInfo
from .coverage_insights import CoverageInsights, CoverageInsight


class Reporter:
    """Handles all output and display for the test runner."""
    
    def __init__(self, args):
        self.args = args
        self.terminal_width = self._get_terminal_width()
        self.console = Console()  # Use default theme
        self.border = Border(style=BorderStyle.ROUNDED, color="primary", show_left=False)
        self.progress_bar = ProgressBar()
        
    def _get_terminal_width(self) -> int:
        """Get terminal width for formatting."""
        try:
            return os.get_terminal_size().columns
        except OSError:
            return 80
            
    def clear_screen(self):
        """Clear the terminal screen."""
        if not self.args.no_color and not self.args.quiet:
            print(CLEAR_SCREEN)
            
    def print_header(self, test_count: Optional[int] = None):
        """Print beautiful header."""
        if self.args.quiet:
            return
            
        print_header(
            "⚡ Storm Checker Test Suite ⚡",
            "Running tests with style"
        )
        
        # Show configuration
        config_lines = [
            f"Test Pattern: {self.args.pattern or 'all tests'}",
            f"Markers: {self.args.mark or 'none'}",
            f"Coverage: {'enabled' if self.args.coverage else 'disabled'}",
            f"Mode: {self._get_mode_label()}",
            f"Verbosity: {self._get_verbosity_label()}"
        ]
        
        if test_count:
            config_lines.append(f"Tests Found: {test_count}")
            
        config_box = self.border.box(
            config_lines,
            width=60,
            padding=2
        )
        
        for line in config_box:
            print(line)
        print()
        
    def _get_mode_label(self) -> str:
        """Get mode label for display."""
        if self.args.quick:
            return "quick"
        elif self.args.diagnose:
            return "diagnostic"
        elif self.args.dashboard:
            return "dashboard"
        else:
            return "standard"
            
    def _get_verbosity_label(self) -> str:
        """Get verbosity label for display."""
        if self.args.quiet:
            return "quiet"
        elif self.args.verbose:
            return "verbose"
        else:
            return "normal"
            
    def print_results(self, state: TestRunState):
        """Print test results summary."""
        if self.args.dashboard:
            self._print_dashboard(state)
        else:
            self._print_summary(state)
            
        # Print failures if any
        if state.failures:
            self._print_failures(state.failures)
            
        # Print slow tests if any
        if state.slow_tests and not self.args.quiet:
            self._print_slow_tests(state.slow_tests)
            
        # Print coverage if available
        if self.args.coverage:
            if state.has_coverage:
                self._print_coverage_report(state.coverage_data)
                # Show actionable insights unless disabled
                if not getattr(self.args, 'no_insights', False):
                    self._print_actionable_insights(state.coverage_data)
            elif self.args.debug_runner:
                print(f"[DEBUG] No coverage data available (has_coverage={state.has_coverage}, data={len(state.coverage_data)} items)")
            
        # Print stdin-blocked files if any
        if state.stdin_blocked_files:
            self._print_stdin_blocked(state.stdin_blocked_files)
            
    def _print_summary(self, state: TestRunState):
        """Print basic test summary."""
        result = state.results
        elapsed = state.elapsed_time
        
        # Build summary header
        if result.success:
            status = ColorPrinter.success("✅ ALL TESTS PASSED!")
            color = "success"
        elif result.failed > 0:
            status = ColorPrinter.error(f"❌ {result.failed} TEST{'S' if result.failed != 1 else ''} FAILED")
            color = "error"
        else:
            status = ColorPrinter.warning("⚠️  TESTS COMPLETED WITH ISSUES")
            color = "warning"
            
        print()
        print_header(status)
        
        # Create summary stats
        stats = []
        if result.passed > 0:
            stats.append(ColorPrinter.success(f"✓ {result.passed} passed"))
        if result.failed > 0:
            stats.append(ColorPrinter.error(f"✗ {result.failed} failed"))
        if result.skipped > 0:
            stats.append(ColorPrinter.warning(f"→ {result.skipped} skipped"))
        if result.errors > 0:
            stats.append(ColorPrinter.error(f"! {result.errors} errors"))
        if result.not_run > 0:
            stats.append(DIM + f"- {result.not_run} not run" + RESET)
            
        # Print stats box
        summary_lines = [
            f"Total: {result.total} tests",
            f"Time: {elapsed:.2f}s",
            " | ".join(stats) if stats else "No tests run"
        ]
        
        # Create a border with the right color (no left border)
        colored_border = Border(style=BorderStyle.ROUNDED, color=color, show_left=False)
        summary_box = colored_border.box(
            summary_lines,
            width=self.terminal_width - 4,
            padding=1
        )
        
        for line in summary_box:
            print(line)
            
    def _print_dashboard(self, state: TestRunState):
        """Print dashboard-style results."""
        result = state.results
        elapsed = state.elapsed_time
        
        print()
        print_header("📊 TEST RESULTS DASHBOARD", "Comprehensive test metrics")
        
        # Main metrics cards
        metrics = [
            ("Tests Run", str(result.total), "primary"),
            ("Passed", str(result.passed), "success" if result.passed > 0 else "dim"),
            ("Failed", str(result.failed), "error" if result.failed > 0 else "dim"),
            ("Time", f"{elapsed:.1f}s", "info")
        ]
        
        # Print metrics in a grid
        metric_boxes = []
        for title, value, color in metrics:
            lines = [title, "", ColorPrinter.format(value, color=color, bold=True)]
            box = Border(style=BorderStyle.DOUBLE, color=color, show_left=False).box(
                lines, width=18, padding=1, align="center"
            )
            metric_boxes.append(box)
            
        # Print metrics side by side
        max_lines = max(len(box) for box in metric_boxes)
        for i in range(max_lines):
            line_parts = []
            for box in metric_boxes:
                if i < len(box):
                    line_parts.append(box[i])
                else:
                    line_parts.append(" " * 18)
            print("  ".join(line_parts))
            
        # Additional statistics
        if result.total > 0:
            pass_rate = (result.passed / result.total) * 100
            print()
            print(f"  Pass Rate: {self._create_progress_bar(pass_rate)} {pass_rate:.1f}%")
            
        # Performance metrics
        if result.total > 0:
            tests_per_second = result.total / elapsed if elapsed > 0 else 0
            print(f"  Speed: {ColorPrinter.info(f'{tests_per_second:.1f} tests/second')}")
            
    def _create_progress_bar(self, percentage: float, width: int = 30) -> str:
        """Create a simple progress bar."""
        filled = int((percentage / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        
        if percentage >= 95:
            color = "success"
        elif percentage >= 70:
            color = "warning"
        else:
            color = "error"
            
        return ColorPrinter.format(bar, color=color)
        
    def _print_failures(self, failures: List[TestFailure]):
        """Print detailed failure information."""
        if not failures:
            return
            
        print()
        print_error(f"Failed Tests ({len(failures)}):")
        print("=" * self.terminal_width)
        
        for i, failure in enumerate(failures, 1):
            print(f"\n{ColorPrinter.error(f'{i}.')} {ColorPrinter.warning(failure.path)}")
            print(f"   {DIM}Error: {failure.error}{RESET}")
            
    def _print_slow_tests(self, slow_tests: List[SlowTest]):
        """Print slow test summary."""
        if not slow_tests:
            return
            
        print()
        print_warning(f"Slow Tests (>{self.args.slow_test_threshold}s):")
        
        for test in sorted(slow_tests, key=lambda x: x.duration, reverse=True)[:5]:
            print(f"  • {test.file}: {ColorPrinter.warning(test.display_duration)}")
            if test.test_name:
                print(f"    {DIM}{test.test_name}{RESET}")
                
    def _print_coverage_report(self, coverage_data: Dict[str, CoverageInfo]):
        """Print coverage report with beautiful progress bars."""
        if not coverage_data:
            return
            
        print()
        print_header("📊 COVERAGE REPORT", "Code coverage analysis")
        print("=" * self.terminal_width)
        
        # Get total coverage
        total = coverage_data.get("_total")
        if total:
            # Create progress bar for overall coverage
            bar = self._create_coverage_bar(total.coverage_percent)
            coverage_color = self._get_coverage_color(total.coverage_percent)
            
            print(f"\n{BOLD}Overall Coverage:{RESET} {self._format_coverage_percent(total.coverage_percent)} {bar}")
            print(f"Statements: {ColorPrinter.primary(f'{total.covered}/{total.statements}')} covered")
            print()
            
        # Create detailed file coverage table
        print(f"{BOLD}File Coverage Details:{RESET}")
        print("─" * self.terminal_width)
        
        # Header
        header = f"{'File':<50} {'Stmts':>7} {'Miss':>6} {'Cover':>7}  Progress"
        print(DIM + header + RESET)
        print("─" * self.terminal_width)
        
        # Sort files by coverage percentage for better visibility
        sorted_files = []
        for filepath, info in coverage_data.items():
            if filepath != "_total":
                sorted_files.append((filepath, info))
        sorted_files.sort(key=lambda x: x[1].coverage_percent, reverse=True)
        
        # Group files by coverage level
        perfect_coverage = []
        good_coverage = []
        needs_work = []
        critical = []
        
        for filepath, info in sorted_files:
            if info.coverage_percent == 100:
                perfect_coverage.append((filepath, info))
            elif info.coverage_percent >= 80:
                good_coverage.append((filepath, info))
            elif info.coverage_percent >= 60:
                needs_work.append((filepath, info))
            else:
                critical.append((filepath, info))
        
        # Show perfect coverage files compactly
        if perfect_coverage:
            print(f"\n{ColorPrinter.success('✨ Perfect Coverage (100%):')} {len(perfect_coverage)} files")
            for i, (filepath, info) in enumerate(perfect_coverage[:10]):
                display_path = self._truncate_path(filepath, 40)
                print(ColorPrinter.success(f"  ✓ {display_path}"))
            if len(perfect_coverage) > 10:
                print(ColorPrinter.success(f"  ... and {len(perfect_coverage) - 10} more files"))
        
        # Show good coverage files
        if good_coverage:
            print(f"\n{ColorPrinter.primary('📊 Good Coverage (80-99%):')} {len(good_coverage)} files")
            for filepath, info in good_coverage[:10]:
                display_path = self._truncate_path(filepath, 40)
                mini_bar = self._create_mini_coverage_bar(info.coverage_percent)
                row = f"  {display_path:<40} {info.coverage_percent:>6.1f}%  {mini_bar}"
                print(ColorPrinter.primary(row))
        
        # Show files needing work
        if needs_work:
            print(f"\n{ColorPrinter.warning('⚠️  Needs Improvement (60-79%):')} {len(needs_work)} files")
            for filepath, info in needs_work[:10]:
                display_path = self._truncate_path(filepath, 40)
                mini_bar = self._create_mini_coverage_bar(info.coverage_percent)
                row = f"  {display_path:<40} {info.coverage_percent:>6.1f}%  {mini_bar}"
                print(ColorPrinter.warning(row))
        
        # Show critical files
        if critical:
            print(f"\n{ColorPrinter.error('🔴 Critical (<60%):')} {len(critical)} files")
            for filepath, info in critical[:15]:
                display_path = self._truncate_path(filepath, 40)
                mini_bar = self._create_mini_coverage_bar(info.coverage_percent)
                row = f"  {display_path:<40} {info.coverage_percent:>6.1f}%  {mini_bar}"
                print(ColorPrinter.error(row))
                
        print("\n" + "─" * self.terminal_width)
        
        # Coverage summary statistics
        total_files = len(sorted_files)
        if total_files > 0:
            print(f"\n{ColorPrinter.primary('📈 Coverage Summary:')}")
            print(f"  Total files tracked: {total_files}")
            print(f"  Perfect (100%): {len(perfect_coverage)} files")
            print(f"  Good (80-99%): {len(good_coverage)} files")
            print(f"  Needs work (60-79%): {len(needs_work)} files")
            print(f"  Critical (<60%): {len(critical)} files")
            
        print("─" * self.terminal_width)
        
        # Quick wins section
        self._print_quick_wins(coverage_data)
        
        # Show files with low coverage
        low_coverage = []
        for filepath, info in coverage_data.items():
            if filepath != "_total" and info.coverage_percent < 80:
                low_coverage.append((filepath, info))
                
        if low_coverage and len(low_coverage) > 0:
            print(f"\n{ColorPrinter.warning('⚠️  Files needing attention:')}")
            for filepath, info in sorted(low_coverage, key=lambda x: x[1].coverage_percent)[:5]:
                bar = self._create_mini_coverage_bar(info.coverage_percent)
                print(f"  • {self._truncate_path(filepath, 40)}: {bar} {self._format_coverage_percent(info.coverage_percent)}")
                    
    def _format_coverage_percent(self, percent: float) -> str:
        """Format coverage percentage with color."""
        if percent >= 95:
            return ColorPrinter.success(f"{percent:.1f}%")
        elif percent >= 80:
            return ColorPrinter.primary(f"{percent:.1f}%")
        elif percent >= 60:
            return ColorPrinter.warning(f"{percent:.1f}%")
        else:
            return ColorPrinter.error(f"{percent:.1f}%")
            
    def _create_coverage_bar(self, percent: float, width: int = 30) -> str:
        """Create a coverage progress bar."""
        filled = int((percent / 100) * width)
        empty = width - filled
        
        # Choose color based on coverage
        if percent >= 80:
            bar_color = ColorPrinter.success
        elif percent >= 60:
            bar_color = ColorPrinter.warning
        else:
            bar_color = ColorPrinter.error
            
        bar = bar_color("█" * filled) + DIM + "░" * empty + RESET
        return f"[{bar}]"
        
    def _create_mini_coverage_bar(self, percent: float, width: int = 20) -> str:
        """Create a mini coverage progress bar."""
        filled = int((percent / 100) * width)
        empty = width - filled
        
        # Choose color based on coverage
        if percent >= 80:
            bar_filled = ColorPrinter.success("█" * filled)
        elif percent >= 60:
            bar_filled = ColorPrinter.warning("█" * filled)
        else:
            bar_filled = ColorPrinter.error("█" * filled)
            
        bar_empty = DIM + "░" * empty + RESET
        return bar_filled + bar_empty
        
    def _get_coverage_color(self, percent: float) -> str:
        """Get color name based on coverage percentage."""
        if percent >= 80:
            return "success"
        elif percent >= 60:
            return "warning"
        else:
            return "error"
            
    def _truncate_path(self, filepath: str, max_length: int) -> str:
        """Truncate file path to fit in given width."""
        if len(filepath) <= max_length:
            return filepath
            
        # Try to keep the filename and truncate the directory
        parts = filepath.split('/')
        if len(parts) > 1:
            filename = parts[-1]
            if len(filename) < max_length - 4:
                # Show start of path and filename
                available = max_length - len(filename) - 4  # 4 for ".../""
                if available > 0:
                    start = filepath[:available]
                    return f"{start}.../{filename}"
                    
        # Just truncate from the end
        return filepath[:max_length-3] + "..."
        
    def _print_quick_wins(self, coverage_data: Dict[str, CoverageInfo]):
        """Print files that are close to coverage threshold."""
        quick_wins = []
        
        for filepath, info in coverage_data.items():
            if filepath != "_total" and 75 <= info.coverage_percent < 80:
                missing = info.missed
                quick_wins.append((filepath, missing, info.coverage_percent))
                
        if quick_wins:
            print(f"\n{ColorPrinter.primary('🎯 Quick Wins')} (files close to 80% coverage):")
            quick_wins.sort(key=lambda x: x[1])  # Sort by missing lines
            
            for filepath, missing, percent in quick_wins[:3]:
                display_path = self._truncate_path(filepath, 40)
                print(f"  • {display_path}: Just {ColorPrinter.success(str(missing))} "
                      f"line{'s' if missing != 1 else ''} to reach 80% (currently {percent:.1f}%)")
            
    def _print_stdin_blocked(self, files: List[str]):
        """Print files that were blocked on stdin."""
        if not files:
            return
            
        print()
        print_warning("⚠️  Files blocked waiting for input:")
        for filepath in files:
            print(f"  {ColorPrinter.warning(filepath)}")
        print(f"  {DIM}💡 Fix: Mock input() or sys.stdin in these tests{RESET}")
    
    def _print_actionable_insights(self, coverage_data: Dict[str, CoverageInfo]):
        """Print actionable insights for improving coverage."""
        if not coverage_data:
            return
        
        # Generate insights
        insights_gen = CoverageInsights(project_root=Path.cwd())
        insights = insights_gen.get_actionable_insights(
            coverage_data,
            num_files=3,
            lines_per_file=1
        )
        
        if not insights:
            return
        
        print()
        print("=" * self.terminal_width)
        print_header("🎯 ACTIONABLE COVERAGE IMPROVEMENTS", 
                    "Specific lines to test for better coverage")
        print("=" * self.terminal_width)
        
        for i, insight in enumerate(insights, 1):
            print()
            # Clickable file:line reference (works in most terminals)
            print(f"📍 {ColorPrinter.primary(insight.clickable_reference)}")
            print(f"   Coverage: {self._format_coverage_percent(insight.coverage_percent)}")
            
            # Show code context
            print(f"\n   {DIM}Code context:{RESET}")
            
            # Show lines before
            for line in insight.context_before:
                print(f"   {DIM}{line}{RESET}")
            
            # Highlight the uncovered line
            line_num = insight.line_number
            print(f"   {ColorPrinter.error(f'{line_num:4}:')} → {ColorPrinter.warning(insight.code_line)} {ColorPrinter.error('← NOT COVERED')}")
            
            # Show lines after
            for line in insight.context_after:
                print(f"   {DIM}{line}{RESET}")
            
            # Show suggestion
            print(f"\n   💡 {ColorPrinter.success('Suggestion:')} {insight.suggestion}")
            
            if i < len(insights):
                print("   " + "─" * 60)
        
        print()
        print(f"{DIM}Tip: Ctrl+click on file:line references to jump to code{RESET}")
        
        # Show export option if available
        if getattr(self.args, 'export_insights', None):
            insights_gen.export_insights(insights, self.args.export_insights)
            print(f"✅ Insights exported to: {self.args.export_insights}")
        
    def create_progress_context(self):
        """Create a progress context for real-time updates."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False
        )
        
    def print_diagnostic_summary(self, report):
        """Print diagnostic report summary."""
        print()
        print_header("Diagnostic Summary")
        
        if not report.issues:
            print_success("✅ No critical issues found!")
            print_info("\nRecommendations:")
            print("  • Use --quick mode for faster test runs")
            print("  • Use --debug-runner for detailed debugging")
            print("  • Add pytest-timeout to prevent hanging tests")
        else:
            counts = report.issue_count
            print_error(f"Found {sum(counts.values())} potential issues:")
            print(f"  • {counts['error']} errors")
            print(f"  • {counts['warning']} warnings")
            print(f"  • {counts['info']} suggestions")
            
            print_info("\nTop issues:")
            for issue in report.issues[:5]:
                icon = "❌" if issue.severity == "error" else "⚠️" if issue.severity == "warning" else "ℹ️"
                print(f"  {icon} {issue.message}")
                if issue.suggestion:
                    print(f"     💡 {issue.suggestion}")