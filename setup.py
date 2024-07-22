"""
Copyright Ⓒ 2020 "Sberbank Real Estate Center" Limited Liability Company. Licensed under the MIT license.
Please, see the LICENSE.md file in project's root for full licensing information.
"""
from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name="pggraph",
    description="Утилита для работы с зависимостями таблиц в PostgreSQL",
    long_description=long_description,
    long_description_content_type='text/markdown',
    version="0.1.7",
    author='"Sberbank Real Estate Center" Limited Liability Company <omborzov@domclick.ru> omborzov@domclick.ru',
    author_email='omborzov@domclick.ru',
    url='https://github.com/domclick/pggraph',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Database',
        'Topic :: Utilities'
    ],
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary>=2.8",
        "dataclasses>=0.5",
    ],
    entry_points={'console_scripts': ['pggraph=pggraph.main:main']}
)
