from setuptools import setup, find_packages

setup(
    name='userdatamodel',
    packages=find_packages(),
    install_requires=[
        'sqlalchemy==0.9.9',
        'sqlalchemy-migrate==0.11.0',
    ],
    scripts=[
        'bin/userdatamodel-init',
    ],
)
