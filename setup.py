# Always prefer setuptools over distutils
from setuptools import setup, find_packages
from os import path
from io import open
here = path.abspath(path.dirname(__file__))
setup(
    name='WSPDataVisualizer',
    version='1.0.0',
    description='Easy User-Configurable Data Visualization',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Zening Chen',
    author_email='chezenin@amazon.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: People who dont like excel',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='User-Configurable Data Visualization',
    packages=find_packages(),

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['pandas',
                      'matplotlib',
                      'numpy',
                      'functools',
                      'datetime',
                      'itertools',
                      'traceback',
                      'python-qt5'],  # Optional
    dependency_links = ['http://github.com/mtai/python-gearman/tarball/master#egg=gearman-2.0.0beta'],
    entry_points={  # Optional
        'console_scripts': [
            'py_visualizer=dataVisualizer:main',
        ],
    },
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/zeningchen/PythonDataVisualizer',
    },
)