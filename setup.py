from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name="PgGraph",
    description="Утилита для работы с зависимостями таблиц в PostgreSQL",
    long_description=long_description,
    long_description_content_type='text/markdown',
    version="0.1",
    author='Sberbank Real Estate Centre LLC <mail@olegborzov.ru> mail@olegborzov.ru',
    url='https://github.com/domclick/pggraph',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Topic :: Database',
        'Topic :: Utilities'
    ],
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary>=2.8.4"
    ],
    entry_points={'console_scripts': ['pggraph=pg_graph.main:main']}
)
