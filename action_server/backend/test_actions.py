"""
Simple test script for action server endpoints.
Run this to verify the action server is working correctly.
"""
import asyncio
import httpx


async def test_action_server():
    """Test all action server endpoints"""
    base_url = "http://localhost:9000"
    
    print("=" * 60)
    print("Testing Action Server")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        print("\n1. Testing health check...")
        try:
            resp = await client.get(f"{base_url}/health")
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✅ Health check passed: {data['status']}")
                print(f"   Capabilities: {', '.join(data['capabilities'])}")
            else:
                print(f"   ❌ Health check failed: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Test 2: Verify target health (dry run)
        print("\n2. Testing target health verification...")
        try:
            resp = await client.get(f"{base_url}/api/v1/action/verify-target-health")
            if resp.status_code == 200:
                data = resp.json()
                is_healthy = data.get("is_healthy", False)
                status = "✅ Healthy" if is_healthy else "⚠️ Unhealthy"
                print(f"   {status}")
                print(f"   Pool health: {data.get('pool_health', 'unknown')}")
                print(f"   Error rate: {data.get('error_rate_percent', 'N/A')}%")
            else:
                print(f"   ❌ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ⚠️ Target server may not be running: {str(e)}")
        
        # Test 3: Restart API (dry run)
        print("\n3. Testing restart API (dry run)...")
        try:
            resp = await client.post(
                f"{base_url}/api/v1/action/restart-target-api",
                params={"dry_run": True}
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✅ Dry run successful")
                print(f"   Would execute: {data['details']['command']}")
                print(f"   Risk level: {data['details']['risk_level']}")
            else:
                print(f"   ❌ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        
        # Test 4: Restart DB (dry run)
        print("\n4. Testing restart DB (dry run)...")
        try:
            resp = await client.post(
                f"{base_url}/api/v1/action/restart-target-db",
                params={"dry_run": True}
            )
            if resp.status_code == 200:
                data = resp.json()
                print(f"   ✅ Dry run successful")
                print(f"   Would execute: {data['details']['command']}")
                print(f"   Risk level: {data['details']['risk_level']}")
            else:
                print(f"   ❌ Failed: {resp.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start target server if not running")
    print("2. Run actual restart commands (remove dry_run=True)")
    print("3. Test complete remediation workflow")
    print("\nAPI Documentation: http://localhost:9000/docs")


if __name__ == "__main__":
    asyncio.run(test_action_server())
