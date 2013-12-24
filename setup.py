from distutils.core import setup

def get_version(version, _):
    return version

version = get_version("1.0.3", 1649)

setup(
    name = "TastyTopping",
    version = version,
    author = "Christian Boelsen",
    author_email="christian.boelsen@hds.com",
    packages = ['tastytopping'],
    license = "LICENSE.txt",
    description = "An ORM to wrap TastyPie APIs.",
    long_description = open('README.rst', 'r').read(),
    url = 'https://github.com/cryporchild/tastytopping',
    install_requires = [
        'requests >= 1.0.0',
    ],
)
