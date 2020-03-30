import os
import re
import sys
from subprocess import STDOUT, CalledProcessError, check_output

# These will be filled in if git archive is run or by setup.py cmdclasses
GIT_REFS = "$Format:%D$"
GIT_SHA1 = "$Format:%h$"


def get_version_from_git(path=None):
    """Try to parse version from git describe, fallback to git archive tags"""
    tag, plus, suffix = "0", "untagged", ""
    if not GIT_SHA1.startswith("$"):
        # git archive or the cmdclasses below have filled in these strings
        sha1 = GIT_SHA1
        for ref_name in GIT_REFS.split(", "):
            if ref_name.startswith("tag: "):
                # git from 1.8.3 onwards labels archive tags "tag: TAGNAME"
                tag, plus = ref_name[5:], "0"
    else:
        if path is None:
            # If no path to git repo, choose the directory this file is in
            path = os.path.dirname(os.path.abspath(__file__))
        git_cmd = "git describe --tags --dirty --always --long".split()
        # output is TAG-NUM-gHEX[-dirty] or HEX[-dirty]
        try:
            out = check_output(git_cmd, stderr=STDOUT, cwd=path).decode().strip()
        except Exception as e:
            sys.stderr.write("%s: %s\n" % (type(e).__name__, str(e)))
            if isinstance(e, CalledProcessError):
                sys.stderr.write("-> %s" % e.output.decode())
            return "0+unknown", None, e
        else:
            if out.endswith("-dirty"):
                out = out[:-6]
                suffix = ".dirty"
            if "-" in out:
                # There is a tag, extract it and the other pieces
                match = re.search(r"^(.+)-(\d+)-g([0-9a-f]+)$", out)
                tag, plus, sha1 = match.groups()
            else:
                # No tag, just sha1
                sha1 = out
    if plus != "0" or suffix:
        # Not on a tag, add additional info
        tag = "%(tag)s+%(plus)s.g%(sha1)s%(suffix)s" % locals()
    return tag, sha1, None


__version__, git_sha1, git_error = get_version_from_git()


def get_cmdclass(build_py=None, sdist=None):
    """Create cmdclass dict to pass to setuptools.setup that will write a
    _version_static.py file in our resultant sdist, wheel or egg"""
    if build_py is None:
        from setuptools.command.build_py import build_py
    if sdist is None:
        from setuptools.command.sdist import sdist

    def make_version_static(base_dir, pkg):
        vg = os.path.join(base_dir, pkg.split(".")[0], "_version_git.py")
        if os.path.isfile(vg):
            lines = open(vg).readlines()
            with open(vg, "w") as f:
                for line in lines:
                    # Replace GIT_* with static versions
                    if line.startswith("GIT_SHA1 = "):
                        f.write("GIT_SHA1 = '%s'\n" % git_sha1)
                    elif line.startswith("GIT_REFS = "):
                        f.write("GIT_REFS = 'tag: %s'\n" % __version__)
                    else:
                        f.write(line)

    class BuildPy(build_py):
        def run(self):
            build_py.run(self)
            for pkg in self.packages:
                make_version_static(self.build_lib, pkg)

    class Sdist(sdist):
        def make_release_tree(self, base_dir, files):
            sdist.make_release_tree(self, base_dir, files)
            for pkg in self.distribution.packages:
                make_version_static(base_dir, pkg)

    return dict(build_py=BuildPy, sdist=Sdist)
