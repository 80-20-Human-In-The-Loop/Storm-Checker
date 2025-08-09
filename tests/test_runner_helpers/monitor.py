"""
Process Monitor for Test Runner
================================
Monitors test execution for timeouts and memory limits.
"""

import os
import sys
import time
import threading
import resource
import subprocess
import signal
from typing import Optional, Callable
from .models import ProcessInfo


class ProcessMonitor:
    """Monitors running processes for timeout and memory violations."""
    
    def __init__(self, args):
        self.args = args
        self.timeout_per_file = getattr(args, 'timeout', 30)
        self.max_memory_mb = getattr(args, 'max_memory', 2048)
        self.safety_enabled = not getattr(args, 'safety_off', False)
        
        # Monitoring state
        self.monitor_thread: Optional[threading.Thread] = None
        self.process_info: Optional[ProcessInfo] = None
        self.stop_monitoring_flag = threading.Event()
        
    def start_monitoring(self, 
                        process: subprocess.Popen,
                        current_file: str,
                        timeout: Optional[float] = None,
                        on_kill: Optional[Callable] = None) -> ProcessInfo:
        """Start monitoring a process."""
        if not self.safety_enabled:
            return ProcessInfo(
                pid=process.pid,
                command=[],
                start_time=time.time(),
                timeout=timeout or self.timeout_per_file,
                memory_limit_mb=self.max_memory_mb,
                current_file=current_file
            )
            
        self.stop_monitoring_flag.clear()
        
        self.process_info = ProcessInfo(
            pid=process.pid,
            command=[],
            start_time=time.time(),
            timeout=timeout or self.timeout_per_file,
            memory_limit_mb=self.max_memory_mb,
            current_file=current_file
        )
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(process, on_kill),
            daemon=True
        )
        self.monitor_thread.start()
        
        return self.process_info
        
    def stop_monitoring(self):
        """Stop monitoring the current process."""
        self.stop_monitoring_flag.set()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
            
    def _monitor_loop(self, process: subprocess.Popen, on_kill: Optional[Callable]):
        """Main monitoring loop running in separate thread."""
        while not self.stop_monitoring_flag.is_set() and process.poll() is None:
            current_time = time.time()
            elapsed = current_time - self.process_info.start_time
            
            # Check timeout
            if elapsed > self.process_info.timeout:
                self.process_info.killed = True
                self.process_info.kill_reason = (
                    f"Timeout: Test file '{self.process_info.current_file}' "
                    f"exceeded {self.process_info.timeout}s limit"
                )
                self._kill_process(process)
                if on_kill:
                    on_kill(self.process_info)
                break
                
            # Check memory usage
            memory_mb = self.get_memory_usage_mb()
            if memory_mb > self.process_info.memory_limit_mb:
                self.process_info.killed = True
                self.process_info.kill_reason = (
                    f"Memory limit exceeded: {memory_mb:.0f}MB > "
                    f"{self.process_info.memory_limit_mb}MB limit"
                )
                self._kill_process(process)
                if on_kill:
                    on_kill(self.process_info)
                break
                
            # Small sleep to avoid busy waiting
            time.sleep(0.1)
            
    def _kill_process(self, process: subprocess.Popen):
        """Safely kill a process."""
        try:
            # Try graceful termination first
            process.terminate()
            
            # Give it a moment to terminate
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()
                process.wait(timeout=1)
        except Exception:
            # Process might already be dead
            pass
            
    def get_memory_usage_mb(self) -> float:
        """Get current process memory usage in MB."""
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux, bytes on macOS
            if sys.platform == 'darwin':
                return usage.ru_maxrss / (1024 * 1024)
            else:
                return usage.ru_maxrss / 1024
        except Exception:
            return 0
            
    def check_stdin_blocking(self, 
                            process: subprocess.Popen,
                            last_output_time: float,
                            timeout: float = 3.0) -> bool:
        """Check if process appears to be blocked on stdin."""
        if process.poll() is not None:
            return False
            
        elapsed_no_output = time.time() - last_output_time
        return elapsed_no_output > timeout
        
    def is_process_alive(self, process: subprocess.Popen) -> bool:
        """Check if a process is still running."""
        return process.poll() is None