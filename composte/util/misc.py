"""For miscellaneous bits of code that don't fit cleanly anywhere else."""


class VersionNotFoundException(Exception):
    """Raised if the version number can't be found."""

    pass


def get_version() -> str:
    """Try a couple ways of getting a git commit hash to use as a version number."""
    try:
        import git

        try:
            return git.Repo(search_parent_directories=True).head.object.hexsha
        except git.exc.InvalidGitRepositoryError:
            pass
    except ImportError:
        pass

    import subprocess

    g = subprocess.Popen(["git", "rev-parse", "HEAD"], stdout=subprocess.PIPE)
    ver = g.stdout.read().strip().decode()

    if ver:
        return ver
    else:
        raise VersionNotFoundException(
            "Could not find git commit hash to use as version number."
        )
