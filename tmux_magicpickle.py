#!/usr/bin/env python3
import subprocess
from typing import List


def run_command(args):
    # https://stackoverflow.com/questions/4760215/running-shell-command-and-capturing-the-output
    return subprocess.run(args, stdout=subprocess.PIPE).stdout.decode("utf-8")


def get_pane_ids() -> List[str]:
    output = run_command(["tmux", "list-panes", "-a", "-F", "#{pane_id}"])
    output = output.split("\n")
    assert len(set(output)) == len(output)
    return [x for x in output if x]


def main(last_n_lines=2):
    remote_code = None
    local_pane_id = None
    for pane in get_pane_ids():
        output = run_command(["tmux", "capture-pane", "-t", pane, "-p", "-J", "-S-"])
        output = [x.rstrip() for x in output.split("\n")]
        output = [x for x in output if x][-last_n_lines:]
        output = "\n".join(output)

        if "Enter wormhole command:" in output:
            assert local_pane_id is None, "multiple local panes"
            local_pane_id = pane

        if "wormhole receive" in output:
            assert remote_code is None, "multiple remote codes"
            remote_code = output.split("wormhole receive ")[1].split("\n")[0]
            remote_code = "wormhole receive " + remote_code
    if local_pane_id is None or remote_code is None:
        print(f"local_pane_id: {local_pane_id}")
        print(f"remote_code: {remote_code}")
        print("exiting")
        return

    run_command(["tmux", "send-keys", "-t", local_pane_id, remote_code, "Enter"])


if __name__ == "__main__":
    main()
