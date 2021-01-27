import setuptools
from sqlalchemy_tools import get_version

VERSION = get_version()

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

setuptools.setup(
    name="sqlalchemy_toolbox",
    version=VERSION,
    license="MIT",
    author="coding kitties",
    author_email="codingkitties@gmail.com",
    description="A collection of sqlalchemy utility classes and "
                "functionalities that help in using sqlalchemy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/coding-kitties/sqlalchemy-toolbox.git",
    packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
    keywords=['SQLALCHEMY', 'SQL', 'ORM', 'DATABASE', 'ALEMBIC'],
    classifiers=[
        "Intended Audience :: Developers",
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        "Topic :: Software Development",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=required,
    python_requires='>=3.6',
    include_package_data=True,
)
