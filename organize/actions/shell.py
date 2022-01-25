from schema import Or, Optional
import shlex
import logging
import subprocess
from subprocess import PIPE

from ..utils import JinjaEnv
from . import Action

logger = logging.getLogger(__name__)


class Shell(Action):
    """
    Executes a shell command

    :param str cmd: The command to execute.

    Example:
      - (macOS) Open all pdfs on your desktop:

        .. code-block:: yaml
          :caption: config.yaml

          rules:
            - folders: '~/Desktop'
              filters:
                - extension: pdf
              actions:
                - shell: 'open "{path}"'
    """

    name = "shell"
    arg_schema = Or(
        str,
        {
            "cmd": str,
            Optional("run_in_simulation"): bool,
            Optional("ignore_errors"): bool,
        },
    )

    def __init__(self, cmd: str, run_in_simulation=False, ignore_errors=False):
        self.cmd = JinjaEnv.from_string(cmd)
        self.run_in_simulation = run_in_simulation
        self.ignore_errors = ignore_errors

    def pipeline(self, args: dict, simulate: bool) -> None:
        full_cmd = self.cmd.render(**args)
        self.print("$ %s" % full_cmd)
        if not simulate or self.run_in_simulation:
            # we use call instead of run to be compatible with python < 3.5
            logger.info('Executing command "%s" in shell.', full_cmd)
            try:
                lexed = shlex.split(full_cmd)
                call = subprocess.run(
                    lexed,
                    check=True,
                    stdout=PIPE,
                    stderr=subprocess.STDOUT,
                )
                return {
                    self.get_name(): {
                        "output": call.stdout.decode("utf-8"),
                        "returncode": 0,
                    }
                }
            except subprocess.CalledProcessError as e:
                if not self.ignore_errors:
                    raise e
                return {
                    self.get_name(): {
                        "output": e.stdout.decode("utf-8"),
                        "returncode": e.returncode,
                    }
                }

    def __str__(self) -> str:
        return 'Shell(cmd="%s")' % self.cmd
