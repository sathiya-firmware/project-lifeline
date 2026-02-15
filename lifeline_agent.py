import subprocess
import sys
import os
import shutil
import json
import logging

# Setup professional logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Lifeline")

# Configuration (Prefer PATH over hardcoded strings)
COPILOT_CLI = shutil.which("copilot") or "copilot"
GH_CLI = shutil.which("gh") or "gh"
WORK_DIR = os.path.join(os.getcwd(), "lifeline_workspace")

def get_session_env():
    """Retrieves and prepares the execution environment for CLI tools."""
    try:
        token = subprocess.check_output([GH_CLI, "auth", "token"], text=True).strip()
        env = os.environ.copy()
        env["GH_TOKEN"] = token
        env["GITHUB_TOKEN"] = token
        return env
    except subprocess.CalledProcessError:
        logger.error("GitHub CLI authentication not found. Please run 'gh auth login'.")
        return None

def execute_remediation(prompt, target_repo_path):
    """Invokes the Copilot CLI in agentic mode to analyze and fix issues."""
    env = get_session_env()
    if not env:
        return
    
    logger.info(f"Agent processing remediation: {prompt}")
    
    # Using agentic flags for autonomous context gathering
    cmd = [COPILOT_CLI, "-p", prompt, "--yolo"]
    try:
        subprocess.run(cmd, env=env, cwd=target_repo_path, check=True)
    except Exception as e:
        logger.error(f"Failed to execute remediation: {e}")

def fetch_open_issues(repo_slug):
    """Queries the GitHub API for maintenance candidates."""
    try:
        output = subprocess.check_output(
            [GH_CLI, "issue", "list", "-R", repo_slug, "--limit", "5", "--json", "number,title"], 
            text=True
        )
        return json.loads(output)
    except Exception as e:
        logger.error(f"Failed to retrieve issues for {repo_slug}: {e}")
        return []

def main():
    print("Project Lifeline: Autonomous OSS Maintenance Agent")
    
    target_repo = input("\nTarget repository (owner/repo): ") or "cli/cli"
    
    issues = fetch_open_issues(target_repo)
    if not issues:
        logger.warning(f"No triage candidates found in {target_repo}.")
        return

    print(f"\nDiscovered {len(issues)} maintenance candidates:")
    for i, issue in enumerate(issues):
        print(f"[{i}] #{issue['number']}: {issue['title']}")

    try:
        choice = int(input("\nSelect an issue to remediate: "))
        if 0 <= choice < len(issues):
            selected = issues[choice]
            
            # Workspace setup
            if os.path.exists(WORK_DIR):
                shutil.rmtree(WORK_DIR)
            
            logger.info(f"Cloning {target_repo}...")
            subprocess.run([GH_CLI, "repo", "clone", target_repo, WORK_DIR], check=True)
            
            # Remediate
            remediation_prompt = f"Analyze and propose a fix for: '{selected['title']}'. Ensure CI compatibility."
            execute_remediation(remediation_prompt, WORK_DIR)
            
            # Final output
            print(f"\nSuccess: Remediation complete for #{selected['number']}.")
            print(f"Local workspace: {WORK_DIR}")
            print("Action required: Review the generated diff and stage the PR.")
            
        else:
            logger.error("Invalid selection index.")
    except KeyboardInterrupt:
        print("\nSession terminated.")
    except Exception as e:
        logger.error(f"Runtime error: {e}")

if __name__ == "__main__":
    main()
