# This file has been copied from:
# <github-url-for-template-module>
import os
import re
from subprocess import check_output, CalledProcessError


def get_version_from_git():
    tag, plus, dirty = "0", "unknown", ""
    path = os.path.dirname(__file__)
    git_cmd = "git -C %s describe --tags --dirty --always --long" % path
    try:
        # describe is TAG-NUM-gHEX[-dirty] or HEX[-dirty]
        describe = check_output(git_cmd.split(), stderr=None).decode().strip()
        if describe.endswith("-dirty"):
            describe = describe[:-6]
            dirty = ".dirty"
        if "-" in describe:
            # There is a tag, extract it and the other pieces
            match = re.search(r'^(.+)-(\d+)-g([0-9a-f]+)$', describe)
            tag, plus, sha1 = match.groups()
        else:
            # No tag, just sha1
            plus, sha1 = "untagged", describe
    except CalledProcessError:
        # not a git repo, maybe an archive
        tags = [t[5:] for t in "$Format:%D$".split(", ")
                if t.startswith("tag: ")]
        if tags:
            tag = tags[0]
            plus = "0"
        sha1 = "$Format:%h$"
        if sha1.startswith("$"):
            sha1 = "error"
    if plus != "0" or dirty:
        # Not on a tag, add additional info
        return "%(tag)s+%(plus)s.%(sha1)s%(dirty)s" % locals()
    else:
        # On a tag, just return it
        return tag


__version__ = get_version_from_git()


def get_cmdclass(build_py=None, sdist=None):
    if build_py is None:
        from setuptools.command.build_py import build_py
    if sdist is None:
        from setuptools.command.sdist import sdist

    def make_version_static(base_dir, pkg):
        with open(os.path.join(base_dir, pkg, "_version_static.py"), "w") as f:
            f.write("__version__ = %r\n" % __version__)

    class BuildPy(build_py):
        def run(self):
            super(BuildPy, self).run()
            for pkg in self.packages:
                make_version_static(self.build_lib, pkg)

    class Sdist(sdist):
        def make_release_tree(self, base_dir, files):
            super(Sdist, self).make_release_tree(base_dir, files)
            for pkg in self.distribution.packages:
                make_version_static(base_dir, pkg)

    return dict(build_py=BuildPy, sdist=Sdist)
