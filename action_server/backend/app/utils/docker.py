import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DockerController:
    """
    Controller for Docker operations.
    Provides safe, audited container management.
    """
    
    async def restart_container(
        self,
        compose_file: str,
        service_name: str,
        timeout: int = 120
    ) -> dict:
        """
        Restart a Docker Compose service.
        
        Args:
            compose_file: Path to docker-compose.yml
            service_name: Name of the service to restart
            timeout: Command timeout in seconds
            
        Returns:
            Dict with stdout, stderr, and return code
            
        Raises:
            subprocess.CalledProcessError: If restart fails
        """
        command = [
            "docker", "compose",
            "-f", compose_file,
            "restart", service_name
        ]
        
        logger.info(f"Executing: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            logger.info(f"Container {service_name} restarted successfully")
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "command": " ".join(command)
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart container {service_name}: {e.stderr}")
            raise RuntimeError(f"Docker restart failed: {e.stderr}")
        
        except subprocess.TimeoutExpired:
            logger.error(f"Docker restart command timed out after {timeout}s")
            raise RuntimeError(f"Docker restart timed out after {timeout}s")
    
    async def get_container_status(
        self,
        compose_file: str,
        service_name: str
    ) -> dict:
        """
        Get the status of a Docker Compose service.
        
        Args:
            compose_file: Path to docker-compose.yml
            service_name: Name of the service
            
        Returns:
            Dict with container status information
        """
        command = [
            "docker", "compose",
            "-f", compose_file,
            "ps", service_name,
            "--format", "json"
        ]
        
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "status": "running" if result.returncode == 0 else "stopped",
                "output": result.stdout
            }
            
        except Exception as e:
            logger.error(f"Failed to get container status: {str(e)}")
            return {"status": "unknown", "error": str(e)}
    
    async def stop_container(
        self,
        compose_file: str,
        service_name: str,
        timeout: int = 30
    ) -> dict:
        """
        Stop a Docker Compose service gracefully.
        
        Args:
            compose_file: Path to docker-compose.yml
            service_name: Name of the service to stop
            timeout: Grace period before force kill
            
        Returns:
            Dict with operation results
        """
        command = [
            "docker", "compose",
            "-f", compose_file,
            "stop", "-t", str(timeout), service_name
        ]
        
        logger.info(f"Stopping container: {service_name}")
        
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout + 10
            )
            
            logger.info(f"Container {service_name} stopped successfully")
            
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except Exception as e:
            logger.error(f"Failed to stop container: {str(e)}")
            raise RuntimeError(f"Failed to stop container: {str(e)}")
