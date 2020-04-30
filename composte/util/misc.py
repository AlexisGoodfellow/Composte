"""For miscellaneous bits of code that don't fit cleanly anywhere else."""
import git


class VersionNotFoundException(Exception):
    """Raised if the version number can't be found."""

    pass


def get_version() -> str:
    """Get a git commit hash to use as a version number."""
    try:
        return git.Repo(search_parent_directories=True).head.object.hexsha
    except git.exc.InvalidGitRepositoryError:
        raise VersionNotFoundException(
            "Could not find git commit hash to use as version number."
        )
