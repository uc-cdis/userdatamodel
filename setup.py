from setuptools import setup, find_packages

setup(
    name='userdatamodel',
    packages=find_packages(),
    install_requires=[
        'sqlalchemy==1.1.9',
    ],
    scripts=[
        'bin/userdatamodel-init',
    ],
)
