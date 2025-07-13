import argparse
import requests

BASE_URL = "http://localhost:8000"

def submit(args):
    payload = {
        "org_id": args.org_id,
        "app_version_id": args.app_version_id,
        "test_path": args.test,
        "priority": args.priority,
        "target": args.target
    }
    try:
        r = requests.post(f"{BASE_URL}/submit", json=payload)
        r.raise_for_status()
        print(r.json())
    except requests.RequestException as e:
        print(f"Error submitting job: {e}")

def status(args):
    try:
        r = requests.get(f"{BASE_URL}/status/{args.job_id}")
        r.raise_for_status()
        print(r.json())
    except requests.RequestException as e:
        print(f"Error checking status: {e}")

def main():
    parser = argparse.ArgumentParser(prog="qgjob")
    subparsers = parser.add_subparsers(dest="command")

    submit_parser = subparsers.add_parser("submit", help="Submit a test job")
    submit_parser.add_argument("--org-id", required=True)
    submit_parser.add_argument("--app-version-id", required=True)
    submit_parser.add_argument("--test", required=True)
    submit_parser.add_argument("--target", required=True, choices=["emulator", "device", "browserstack"])
    submit_parser.add_argument("--priority", type=int, default=1)
    submit_parser.set_defaults(func=submit)

    status_parser = subparsers.add_parser("status", help="Check job status")
    status_parser.add_argument("--job-id", required=True)
    status_parser.set_defaults(func=status)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()