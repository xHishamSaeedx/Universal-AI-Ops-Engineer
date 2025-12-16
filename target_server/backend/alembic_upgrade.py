#!/usr/bin/env python3
"""
Script to upgrade database to latest migration.
Run this before creating new migrations.
"""

import subprocess
import sys

def upgrade_database():
    """Upgrade database to latest migration"""
    try:
        print("Upgrading database to latest migration...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True, cwd=".")

        if result.returncode == 0:
            print("✅ Database upgrade successful!")
            print(result.stdout)
        else:
            print("❌ Database upgrade failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)

    except Exception as e:
        print(f"❌ Error upgrading database: {e}")

if __name__ == "__main__":
    upgrade_database()