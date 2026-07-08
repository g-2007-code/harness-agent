# harness/cli.py
import argparse
import getpass
import os
import sys
import logging

import keyring

from harness.config import load_config
from harness.llm.mock import MockLLM
from harness.loop import AgentLoop
from harness.memory import Memory
from harness.governance import Governance
from harness.tools import ToolRegistry
from harness.tools.file_tools import read_file, write_file
from harness.tools.shell import run_shell

PROVIDERS = ["openai", "anthropic", "google"]
KEYRING_SERVICE = "harness-agent"


def keyring_setup():
    print("Select LLM provider:")
    for i, p in enumerate(PROVIDERS):
        print(f"  {i + 1}. {p}")
    choice = input("Enter number: ").strip()
    try:
        provider = PROVIDERS[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid choice")
        return
    key = getpass.getpass(f"Enter API key for {provider}: ")
    keyring.set_password(KEYRING_SERVICE, provider, key)
    print(f"API key for {provider} stored.")


def keyring_status():
    for provider in PROVIDERS:
        key = keyring.get_password(KEYRING_SERVICE, provider)
        status = "已配置" if key else "未配置"
        print(f"  {provider}: {status}")


def keyring_clear(provider: str = None):
    if provider:
        try:
            keyring.delete_password(KEYRING_SERVICE, provider)
            print(f"Cleared key for {provider}")
        except keyring.errors.PasswordDeleteError:
            print(f"No key found for {provider}")
    else:
        for p in PROVIDERS:
            try:
                keyring.delete_password(KEYRING_SERVICE, p)
            except keyring.errors.PasswordDeleteError:
                pass
        print("Cleared all keys")


def cmd_run(args):
    config = load_config(args.config)

    os.makedirs(config.log_dir, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(config.log_dir, "harness.log")),
        ],
    )

    if config.llm_provider == "mock":
        llm = MockLLM([
            '{"tool": "task_complete", "args": {"summary": "Mock: no real LLM configured"}}'
        ])
    else:
        from harness.llm.openai import OpenAILLM
        api_key = keyring.get_password(KEYRING_SERVICE, config.llm_provider)
        if not api_key:
            api_key = os.environ.get(f"{config.llm_provider.upper()}_API_KEY")
        if not api_key:
            print(f"No API key found for {config.llm_provider}. Run: harness keyring setup")
            sys.exit(1)
        llm = OpenAILLM(api_key=api_key, model=config.llm_model)

    registry = ToolRegistry()
    registry.register("read_file", read_file)
    registry.register("write_file", write_file)
    registry.register("run_shell", run_shell)

    governance = Governance(
        blocked_commands=config.blocked_commands,
        auto_deny=config.auto_deny,
    )
    memory = Memory(task=args.task, session_dir=config.session_dir)

    loop = AgentLoop(
        llm=llm, registry=registry, governance=governance,
        memory=memory, max_turns=config.max_turns,
    )
    result = loop.run(args.task)
    print(result)


def main():
    parser = argparse.ArgumentParser(prog="harness", description="Coding agent harness")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run agent on a task")
    run_parser.add_argument("task", help="Task description")
    run_parser.add_argument("--config", default="config.yaml", help="Config file path")

    keyring_parser = subparsers.add_parser("keyring", help="Manage API keys")
    keyring_sub = keyring_parser.add_subparsers(dest="keyring_command")
    keyring_sub.add_parser("setup", help="Set up API key")
    keyring_sub.add_parser("status", help="Show key status")
    clear_parser = keyring_sub.add_parser("clear", help="Clear key(s)")
    clear_parser.add_argument("--provider", default=None, help="Provider to clear")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "keyring":
        if args.keyring_command == "setup":
            keyring_setup()
        elif args.keyring_command == "status":
            keyring_status()
        elif args.keyring_command == "clear":
            keyring_clear(args.provider)
        else:
            keyring_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
