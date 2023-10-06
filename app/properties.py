"""."""
import os


def running_in_docker() -> bool:
    """Returns True if the code is running inside a Docker container"""
    # pylint: disable=unspecified-encoding
    path = "/proc/self/cgroup"
    return (
        os.path.exists("/.dockerenv")
        or os.path.isfile(path)
        and any("docker" in line for line in open(path, "r"))
    )
