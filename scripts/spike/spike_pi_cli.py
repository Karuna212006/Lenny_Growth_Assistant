import subprocess
import time
import os
import sys

def run_pi_trial(run_idx):
    prompt = "What did Ada Chen Rekhi say about leaving a job? You MUST call the retrieve_transcripts tool first."
    ext_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "pi_tool_ext.mjs"))
    cmd = [
        "pi.cmd",
        "--provider", "ollama",
        "--model", "qwen2.5:7b-instruct",
        "-e", ext_path,
        "--tools", "retrieve_transcripts",
        "-p", prompt
    ]
    t0 = time.time()
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True,
            timeout=10
        )
        stdout = res.stdout or ""
        stderr = res.stderr or ""
        tool_called = "[PI TOOL CALLED]" in stderr or "[PI TOOL CALLED]" in stdout
        cites_chunk = "Energy & Learning Matrix" in stdout or "60-day window" in stdout
        success = tool_called and cites_chunk
        return {
            "success": success,
            "tool_called": tool_called,
            "cites_chunk": cites_chunk,
            "error": None,
            "stdout": stdout,
            "stderr": stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "tool_called": False,
            "cites_chunk": False,
            "error": "TimeoutExpired: pi CLI hung indefinitely waiting for interactive TTY console on Windows"
        }
    except Exception as e:
        return {
            "success": False,
            "tool_called": False,
            "cites_chunk": False,
            "error": str(e)
        }

if __name__ == "__main__":
    runs = 5
    passes = 0
    print(f"=== Running Pi Coding Agent Spike ({runs} iterations) ===")
    for i in range(1, runs + 1):
        print(f"\n--- RUN {i}/{runs} ---")
        res = run_pi_trial(i)
        print(f"Run {i} Result: success={res['success']}, tool_called={res['tool_called']}, error={res.get('error')}")
        if res["success"]:
            passes += 1
    print(f"\n==========================================")
    print(f"Pi Coding Agent Final Score: {passes}/{runs} PASS")
    print(f"==========================================")
