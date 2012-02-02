from setuptools import setup, find_packages

version = '0.0.9'

setup(
    name = 'isotoma.recipe.cluster',
    version = version,
    description = "Buildout recipe for generating cluster start/stop scripts.",
    url = "http://pypi.python.org/pypi/isotoma.recipe.cluster",
    long_description = open("README.rst").read() + "\n" + \
                       open("CHANGES.txt").read(),
    classifiers = [
        "Framework :: Buildout",
        "Framework :: Buildout :: Recipe",
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX",
        "License :: OSI Approved :: Apache Software License",

    ],
    keywords = "buildout cluster",
    author = "John Carr",
    author_email = "john.carr@isotoma.com",
    license="Apache Software License",
    packages = find_packages(exclude=['ez_setup']),
    package_data = {
        '': ['README.rst', 'CHANGES.txt'],
    },
    namespace_packages = ['isotoma', 'isotoma.recipe'],
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'setuptools',
        'zc.buildout',
    ],
    extras_require=dict(
        test = ['zope.testing',],
    ),
    entry_points = {
        "zc.buildout": [
            "default = isotoma.recipe.cluster.recipe:Cluster",
        ],
    }
)
