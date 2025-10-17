import sys
from getopt import GetoptError

import ipdb

from chatdbg.chatdbg_pdb import ChatDBG
from chatdbg.util.config import chatdbg_config
from chatdbg.util.help import print_help


def main() -> None:
    # Check for Java debugging flag
    java_debugging = False
    java_class = None
    java_args = []

    # Parse arguments manually to detect --java flag
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--java" and not java_debugging:
            java_debugging = True
            # Look for class name in next argument
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
                java_class = sys.argv[i + 1]
                i += 1  # Skip the class name argument
        elif arg.startswith("--java="):
            java_debugging = True
            java_class = arg[7:]  # Remove --java= prefix
        elif java_debugging and java_class and not arg.startswith("--"):
            # Collect remaining arguments as Java args
            java_args.append(arg)
        i += 1

    if java_debugging:
        if not java_class:
            print("Error: --java flag requires a Java class name")
            print("Usage: chatdbg --java <main-class> [args...]")
            sys.exit(1)

        # Import here to avoid circular imports
        from chatdbg.chatdbg_jdb import start_jdb_session

        # Start JDB session
        dialog = start_jdb_session(java_class, java_args)

        if dialog:
            # Start the chat dialog
            dialog.dialog("Java debugging session started")
        else:
            print("Failed to start JDB session")
            sys.exit(1)
        return

    # Default Python debugging behavior
    ipdb.__main__._get_debugger_cls = lambda: ChatDBG

    args = chatdbg_config.parse_user_flags(sys.argv[1:])

    if "-h" in args or "--help" in args:
        print_help()

    sys.argv = [sys.argv[0]] + args

    try:
        ipdb.__main__.main()
    except GetoptError as e:
        print(f"Unrecognized option: {e.opt}\n")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
