class Pool:
    """
    Pool objects to hopefully reduce the number of copies floating around in memory.

    Does some manual reference counting, which may be a bad idea.
    """

    __objects = {}

    def __init__(self):
        pass

    def put(self, tag, contructor):
        have = Pool.__objects.get(tag, None)

        if have is None:
            Pool.__objects[tag] = (constructor(), 1)
        else:
            (obj, count) = have
            Pool.__objects[tag] = (obj, count + 1)

        return Pool.__objects[tag]

    def remove(self, tag):
        have = Pool.__objects.get(tag, None)

        if have is None:
            return

        (obj, count) = have

        if count > 1:
            Pool.__objects[tag] = (obj, count - 1)
        elif count == 1:
            del Pool.__objects[tag]

        return count - 1


class ProjectPool:
    """
    Pool Composte projects in memory
    uuid -> (project, count)
    """

    __objects = {}

    def __init__(self):
        pass

    def put(self, uuid, constructor=None):
        """
        Fetch a project and bump its refcount. When the requested project is
        not cached, invoke constructor if possible and cache the result.
        """
        (proj, count) = ProjectPool.__objects.get(uuid, (None, 0))

        if proj is None:
            if constructor is None:
                # We don't have it and the client is going to go get it
                return None
            else:
                # We don't have it but the client told us how to get it
                proj = constructor()

        ProjectPool.__objects[uuid] = (proj, count + 1)
        return proj

    def remove(self, uuid, on_removal=lambda x: x):
        """
        Un-use a project, running on_removal with the project as the only
        argumargument when the reference is removed
        """
        (proj, count) = ProjectPool.__objects.get(uuid, (None, 0))

        if count is None:
            return

        if count > 1:
            ProjectPool.__objects[uuid] = (proj, count - 1)
        elif count == 1:
            on_removal(proj)
            del ProjectPool.__objects[uuid]

        return count - 1

    def map(self, mapfun):
        """
        Apply a function to all cached projects. Adding or removing projects
        during this process results in undefined behavior.
        """
        for pid, (proj, count) in ProjectPool.__objects.items():
            mapfun(proj, count)
