"""
check_environment.py
Practical 10: Environment and Dependency Verifier
Checks Python, Java, and PySpark versions as required by Practical 10 instructions.
"""

import sys
import subprocess
import shutil

def check_env():
    print("==================================================")
    print("PRACTICAL 10: ENVIRONMENT VERIFICATION")
    print("==================================================")
    
    # 1. Python version
    print(f"Python Version: {sys.version.split()[0]} ({sys.executable})")
    
    # 2. Java version
    java_path = shutil.which("java")
    if java_path:
        try:
            res = subprocess.run(["java", "-version"], capture_output=True, text=True)
            java_ver = res.stderr.splitlines()[0] if res.stderr else "Unknown"
            print(f"Java Runtime:   {java_ver} ({java_path})")
        except Exception as e:
            print(f"Java Runtime:   Found at {java_path} but error checking version: {e}")
    else:
        print("Java Runtime:   Not found in PATH.")
        
    # 3. PySpark check
    try:
        import pyspark
        print(f"PySpark:        Installed (Version {pyspark.__version__})")
    except ImportError:
        print("PySpark:        Not installed (Using Pandas and Python datetime streaming engine per instructions).")
        
    print("==================================================\n")

if __name__ == "__main__":
    check_env()
