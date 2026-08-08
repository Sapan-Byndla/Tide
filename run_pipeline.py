import subprocess
import time
import sys
import os

# Subprocesses list to clean up on exit
processes = []

def start_service(name, command):
    print(f"Starting {name} service: {command}")
    # Run in current virtual environment/python path
    proc = subprocess.Popen(
        [sys.executable] + command.split()[1:],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processes.append(proc)
    return proc

def wait_for_log(proc, name, trigger_phrase, timeout=60):
    print(f"Waiting for {name} to start up...")
    start_time = time.time()
    while True:
        if time.time() - start_time > timeout:
            print(f"Error: Timeout waiting for {name} to start.")
            cleanup()
            sys.exit(1)
            
        line = proc.stdout.readline()
        if line:
            print(f"[{name}] {line.strip()}")
            if trigger_phrase in line:
                print(f"-> {name} is READY!")
                break
        else:
            # Check if process terminated early
            ret = proc.poll()
            if ret is not None:
                print(f"Error: {name} terminated unexpectedly with code {ret}.")
                cleanup()
                sys.exit(1)
        time.sleep(0.1)

def cleanup():
    print("\nTerminating background services...")
    for proc in processes:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
    print("Services cleaned up successfully.")

def run_script(name, module_path):
    print(f"\n--- Running: {name} ({module_path}) ---")
    proc = subprocess.Popen(
        [sys.executable, "-m", module_path],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    proc.wait()
    if proc.returncode != 0:
        print(f"Warning: {name} exited with non-zero code {proc.returncode}.")
    else:
        print(f"Successfully completed {name}!")

def main():
    try:
        # 1. Start Embedding Service
        emb_proc = start_service("Embedding", "python -m src.embedding.main")
        wait_for_log(emb_proc, "Embedding", "Application startup complete.")

        # 2. Start Ingest Service
        ing_proc = start_service("Ingest", "python -m src.ingest.main")
        wait_for_log(ing_proc, "Ingest", "Application startup complete.")

        # 3. Seed Database
        run_script("Seed Concepts Database", "src.jobs.bootstrap_seeds")

        # 4. Prompt to run verification or scrapers
        print("\n" + "="*50)
        print("Tide Pipeline Services are now Running!")
        print("="*50)
        print("Options to test and ingest:")
        print("  1. Run Pipeline Integration Tests (tests/test_ingest.py)")
        print("  2. Run Live Scrapers (pull and ingest actual live data)")
        print("  3. Run Scraper Verify Only (tests/test_scrapers.py)")
        print("  4. Do nothing, keep servers running")
        
        choice = input("\nEnter choice (1-4): ").strip()
        if choice == "1":
            run_script("Pipeline Integration Tests", "tests.test_ingest")
        elif choice == "2":
            # Run live scrapers
            print("\nRunning all enabled live scrapers concurrently...")
            cmd = "import asyncio; from src.scrapers import run_all_scrapers; asyncio.run(run_all_scrapers())"
            proc = subprocess.Popen([sys.executable, "-c", cmd], stdout=sys.stdout, stderr=sys.stderr)
            proc.wait()
            print("Live scrapers run finished!")
        elif choice == "3":
            run_script("Scraper Verification", "tests.test_scrapers")
            
        print("\nServices are running. Press Ctrl+C to stop services and exit.")
        while True:
            # Let services output log messages
            line1 = emb_proc.stdout.readline()
            if line1:
                print(f"[Embedding] {line1.strip()}")
            line2 = ing_proc.stdout.readline()
            if line2:
                print(f"[Ingest] {line2.strip()}")
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nShutdown signal received.")
    finally:
        cleanup()

if __name__ == "__main__":
    main()
