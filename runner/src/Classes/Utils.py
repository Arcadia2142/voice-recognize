import subprocess, os


class Utils(object):

    # Call command in shell.
    @staticmethod
    def run_shell_command(command: str, env=None):
        environment = {}
        for k, v in os.environ.items():
            environment[k] = v

        if env is not None:
            for env_key in env:
                environment[env_key] = env[env_key]

        subprocess.call(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            env=environment
        )
