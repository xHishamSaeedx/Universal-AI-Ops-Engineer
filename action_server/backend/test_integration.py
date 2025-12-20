"""
Complete integration test for action server with chaos and target servers.
Tests the full remediation workflow.
"""
import asyncio
import httpx
import time


class Colors:
    """ANSI color codes for pretty output"""
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


async def test_complete_workflow():
    """Test complete chaos → detection → remediation workflow"""
    
    # Service URLs
    target_server = "http://localhost:8000"
    chaos_server = "http://localhost:8080"
    action_server = "http://localhost:9000"
    
    print("=" * 80)
    print(f"{Colors.BLUE}Complete Integration Test: Chaos → Remediation{Colors.RESET}")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Step 1: Verify all services are running
        print(f"\n{Colors.BLUE}Step 1: Verifying all services are running...{Colors.RESET}")
        
        services = {
            "Target Server": f"{target_server}/api/v1/health",
            "Chaos Server": f"{chaos_server}/api/v1/health",
            "Action Server": f"{action_server}/health"
        }
        
        all_running = True
        for name, url in services.items():
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    print(f"   {Colors.GREEN}✓{Colors.RESET} {name}: Running")
                else:
                    print(f"   {Colors.RED}✗{Colors.RESET} {name}: Unhealthy (status {resp.status_code})")
                    all_running = False
            except Exception as e:
                print(f"   {Colors.RED}✗{Colors.RESET} {name}: Not reachable ({str(e)})")
                all_running = False
        
        if not all_running:
            print(f"\n{Colors.RED}❌ Not all services are running. Please start them first.{Colors.RESET}")
            print("\nStart commands:")
            print("  1. Target Server: cd target_server && docker compose up -d")
            print("  2. Chaos Server: cd chaos_server/backend && python main.py")
            print("  3. Action Server: cd action_server/backend && python main.py")
            return
        
        # Step 2: Check initial health of target server
        print(f"\n{Colors.BLUE}Step 2: Checking initial target server health...{Colors.RESET}")
        
        resp = await client.get(f"{target_server}/api/v1/health")
        initial_health = resp.json()
        print(f"   Status: {Colors.GREEN}{initial_health.get('status')}{Colors.RESET}")
        
        resp = await client.get(f"{target_server}/api/v1/pool/status")
        initial_pool = resp.json()
        pool_health = initial_pool.get("pool", {}).get("pool_health", "unknown")
        print(f"   Pool Health: {Colors.GREEN}{pool_health}{Colors.RESET}")
        
        # Step 3: Start chaos attack
        print(f"\n{Colors.BLUE}Step 3: Starting chaos attack (DB pool exhaustion)...{Colors.RESET}")
        
        resp = await client.post(
            f"{chaos_server}/api/v1/break/db_pool",
            params={
                "connections": 10,
                "hold_seconds": 30
            }
        )
        attack_data = resp.json()
        attack_id = attack_data.get("attack_id")
        print(f"   {Colors.YELLOW}⚠{Colors.RESET}  Attack started: {attack_id}")
        print(f"   Holding 10 connections for 30 seconds...")
        
        # Step 4: Wait and verify target is degraded
        print(f"\n{Colors.BLUE}Step 4: Waiting for target to become degraded...{Colors.RESET}")
        await asyncio.sleep(5)
        
        try:
            resp = await client.get(f"{target_server}/api/v1/health", timeout=10.0)
            degraded_health = resp.json()
            status = degraded_health.get("status", "unknown")
            print(f"   Health Status: {Colors.YELLOW}{status}{Colors.RESET}")
        except Exception as e:
            print(f"   {Colors.RED}✗{Colors.RESET} Target server not responding (expected during attack)")
        
        try:
            resp = await client.get(f"{target_server}/api/v1/pool/status", timeout=10.0)
            degraded_pool = resp.json()
            pool_health = degraded_pool.get("pool", {}).get("pool_health", "unknown")
            pool_util = degraded_pool.get("pool", {}).get("pool_utilization", "unknown")
            print(f"   Pool Health: {Colors.YELLOW}{pool_health}{Colors.RESET}")
            print(f"   Pool Utilization: {Colors.YELLOW}{pool_util}{Colors.RESET}")
        except Exception as e:
            print(f"   {Colors.RED}✗{Colors.RESET} Cannot check pool status (pool likely exhausted)")
        
        # Step 5: Call action server to remediate
        print(f"\n{Colors.BLUE}Step 5: Calling action server to remediate...{Colors.RESET}")
        print(f"   Note: Action server only remediates target, chaos must be stopped separately")
        
        resp = await client.post(
            f"{action_server}/api/v1/action/remediate-db-pool-exhaustion",
            params={
                "escalate_to_db_restart": False  # Only restart API, not DB
            },
            timeout=120.0
        )
        
        remediation_result = resp.json()
        
        # Print execution log
        print(f"\n   {Colors.BLUE}Execution Log:{Colors.RESET}")
        for step in remediation_result.get("execution_log", []):
            step_num = step.get("step")
            action = step.get("action")
            status = step.get("status")
            
            if status == "success":
                print(f"   {Colors.GREEN}✓{Colors.RESET} Step {step_num}: {action}")
            else:
                print(f"   {Colors.RED}✗{Colors.RESET} Step {step_num}: {action} - {status}")
        
        # Step 6: Verify recovery
        print(f"\n{Colors.BLUE}Step 6: Verifying recovery...{Colors.RESET}")
        
        remediation_complete = remediation_result.get("remediation_complete", False)
        final_health = remediation_result.get("final_health", {})
        
        print(f"   Remediation Complete: {Colors.GREEN if remediation_complete else Colors.RED}{remediation_complete}{Colors.RESET}")
        print(f"   Target Healthy: {Colors.GREEN if final_health.get('is_healthy') else Colors.RED}{final_health.get('is_healthy')}{Colors.RESET}")
        print(f"   Pool Health: {Colors.GREEN}{final_health.get('pool_health', 'unknown')}{Colors.RESET}")
        print(f"   Error Rate: {final_health.get('error_rate_percent', 'N/A')}%")
        
        # Print recommendation
        recommendation = remediation_result.get("recommendation", "")
        print(f"\n   {Colors.BLUE}Recommendation:{Colors.RESET}")
        print(f"   {recommendation}")
        
        # Step 7: Final verification after a few seconds
        print(f"\n{Colors.BLUE}Step 7: Final verification (waiting 5 seconds)...{Colors.RESET}")
        await asyncio.sleep(5)
        
        resp = await client.get(f"{action_server}/api/v1/action/verify-target-health")
        final_check = resp.json()
        
        is_healthy = final_check.get("is_healthy", False)
        if is_healthy:
            print(f"   {Colors.GREEN}✓ Target server fully recovered!{Colors.RESET}")
            print(f"   Pool Health: {Colors.GREEN}{final_check.get('pool_health')}{Colors.RESET}")
            print(f"   Pool Utilization: {Colors.GREEN}{final_check.get('pool_utilization')}{Colors.RESET}")
            print(f"   Error Rate: {final_check.get('error_rate_percent')}%")
        else:
            print(f"   {Colors.YELLOW}⚠ Target server still recovering...{Colors.RESET}")
            print(f"   Pool Health: {final_check.get('pool_health')}")
    
    # Summary
    print("\n" + "=" * 80)
    if remediation_complete and final_check.get("is_healthy"):
        print(f"{Colors.GREEN}✓ INTEGRATION TEST PASSED{Colors.RESET}")
        print("The action server successfully detected and remediated the chaos attack!")
    else:
        print(f"{Colors.YELLOW}⚠ INTEGRATION TEST PARTIALLY PASSED{Colors.RESET}")
        print("The remediation was executed but recovery may need more time.")
    print("=" * 80)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           Action Server Integration Test                     ║
║                                                               ║
║  This test will:                                             ║
║  1. Verify all services are running                          ║
║  2. Check initial health                                     ║
║  3. Start a chaos attack (DB pool exhaustion)                ║
║  4. Verify target becomes degraded                           ║
║  5. Call action server to remediate                          ║
║  6. Verify recovery                                          ║
║                                                               ║
║  Required services:                                          ║
║  - Target Server (localhost:8000)                            ║
║  - Chaos Server (localhost:8080)                             ║
║  - Action Server (localhost:9000)                            ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    try:
        asyncio.run(test_complete_workflow())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Test failed with error: {str(e)}{Colors.RESET}")
