"""Log monitoring service for target server and PostgreSQL"""
import asyncio
import logging
import subprocess
import shutil
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.config import settings

logger = logging.getLogger(__name__)


class LogMonitor:
    """Monitor logs from target server and PostgreSQL containers"""
    
    def __init__(self):
        self.target_container = settings.target_container_name
        self.db_container = settings.target_db_container_name
        self.tail_lines = settings.log_tail_lines
        self._docker_available = None  # Cache Docker availability check
        self._is_windows = sys.platform == "win32"
    
    def _check_docker_available(self) -> bool:
        """Check if Docker is available"""
        if self._docker_available is not None:
            return self._docker_available
        
        docker_path = shutil.which("docker")
        if docker_path is None:
            self._docker_available = False
            logger.debug("Docker command not found in PATH")
            return False
        
        self._docker_available = True
        return True
    
    async def _run_docker_command(self, cmd: List[str]) -> tuple[int, str, str]:
        """Run docker command and return (returncode, stdout, stderr)"""
        try:
            # On Windows, use subprocess.run in executor for better compatibility
            if self._is_windows:
                def run_cmd():
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    return result.returncode, result.stdout, result.stderr
                
                return await asyncio.to_thread(run_cmd)
            else:
                # On Unix-like systems, use asyncio subprocess
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                return (
                    process.returncode,
                    stdout.decode('utf-8', errors='ignore'),
                    stderr.decode('utf-8', errors='ignore')
                )
        except subprocess.TimeoutExpired:
            logger.debug(f"Docker command timed out: {' '.join(cmd)}")
            return 1, "", "Command timed out"
        except Exception as e:
            error_msg = str(e) if str(e) else repr(e)
            logger.debug(f"Error running docker command ({type(e).__name__}): {error_msg}")
            return 1, "", error_msg
    
    async def get_target_logs(self, lines: Optional[int] = None) -> List[str]:
        """Get recent logs from target server container"""
        lines = lines or self.tail_lines
        try:
            if not settings.use_docker_api:
                logger.debug("Docker API disabled in settings")
                return []
            
            if not self._check_docker_available():
                logger.debug("Docker not available, skipping log collection")
                return []
            
            # Use docker logs command (works on Windows with Docker Desktop)
            cmd = [
                "docker", "logs",
                "--tail", str(lines),
                "--timestamps",
                self.target_container
            ]
            
            returncode, stdout, stderr = await self._run_docker_command(cmd)
            
            if returncode == 0:
                logs = stdout.strip().split('\n') if stdout else []
                filtered_logs = [line for line in logs if line.strip()]
                logger.info(f"Fetched {len(filtered_logs)} log lines from target server container '{self.target_container}'")
                return filtered_logs
            else:
                error_msg = stderr.strip() if stderr else ""
                if "No such container" in error_msg:
                    logger.debug(f"Container '{self.target_container}' not found. Is the target server running?")
                elif not error_msg:
                    logger.debug(f"Failed to get target logs (exit code {returncode}, no error message)")
                else:
                    logger.debug(f"Failed to get target logs (exit code {returncode}): {error_msg}")
                return []
        except Exception as e:
            error_msg = str(e) if str(e) else repr(e)
            logger.debug(f"Error getting target logs ({type(e).__name__}): {error_msg}")
            return []
    
    async def get_postgresql_logs(self, lines: Optional[int] = None) -> List[str]:
        """Get recent logs from PostgreSQL container"""
        lines = lines or self.tail_lines
        try:
            if not settings.use_docker_api:
                logger.debug("Docker API disabled in settings")
                return []
            
            if not self._check_docker_available():
                logger.debug("Docker not available, skipping log collection")
                return []
            
            cmd = [
                "docker", "logs",
                "--tail", str(lines),
                "--timestamps",
                self.db_container
            ]
            
            returncode, stdout, stderr = await self._run_docker_command(cmd)
            
            if returncode == 0:
                logs = stdout.strip().split('\n') if stdout else []
                filtered_logs = [line for line in logs if line.strip()]
                logger.info(f"Fetched {len(filtered_logs)} log lines from PostgreSQL container '{self.db_container}'")
                return filtered_logs
            else:
                error_msg = stderr.strip() if stderr else ""
                if "No such container" in error_msg:
                    logger.debug(f"Container '{self.db_container}' not found. Is the target server running?")
                elif not error_msg:
                    logger.debug(f"Failed to get PostgreSQL logs (exit code {returncode}, no error message)")
                else:
                    logger.debug(f"Failed to get PostgreSQL logs (exit code {returncode}): {error_msg}")
                return []
        except Exception as e:
            error_msg = str(e) if str(e) else repr(e)
            logger.debug(f"Error getting PostgreSQL logs ({type(e).__name__}): {error_msg}")
            return []
    
    async def get_all_logs(self) -> Dict[str, List[str]]:
        """Get logs from both target server and PostgreSQL"""
        target_logs, db_logs = await asyncio.gather(
            self.get_target_logs(),
            self.get_postgresql_logs()
        )
        return {
            "target_server": target_logs,
            "postgresql": db_logs,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def extract_error_logs(self, logs: List[str]) -> List[str]:
        """Extract error-level logs from log lines"""
        error_keywords = [
            "ERROR", "error", "Error",
            "DB_ERROR",
            "Exception",
            "Traceback",
            "FATAL",
            "CRITICAL",
            "failed",
            "timeout",
            "503",
            "500"
        ]
        error_logs = []
        for line in logs:
            if any(keyword in line for keyword in error_keywords):
                error_logs.append(line)
        return error_logs
    
    def extract_chaos_indicators(self, logs: Dict[str, List[str]]) -> Dict[str, Any]:
        """Extract chaos indicators from logs"""
        indicators = {
            "target_errors": [],
            "db_errors": [],
            "pool_errors": [],
            "connection_errors": [],
            "timeout_errors": []
        }
        
        # Analyze target server logs
        target_logs = logs.get("target_server", [])
        target_errors = self.extract_error_logs(target_logs)
        indicators["target_errors"] = target_errors
        
        # Look for specific patterns
        for line in target_errors:
            line_lower = line.lower()
            if "pool" in line_lower and ("exhaust" in line_lower or "limit" in line_lower or "timeout" in line_lower):
                indicators["pool_errors"].append(line)
            if "connection" in line_lower and ("refused" in line_lower or "failed" in line_lower):
                indicators["connection_errors"].append(line)
            if "timeout" in line_lower:
                indicators["timeout_errors"].append(line)
        
        # Analyze PostgreSQL logs
        db_logs = logs.get("postgresql", [])
        db_errors = self.extract_error_logs(db_logs)
        indicators["db_errors"] = db_errors
        
        return indicators
