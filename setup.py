from setuptools import setup, find_packages

setup(
    name='hafas',
    version='0.1.0',
    author='Christian Meilke',
    author_email='christian.meilke@googlemail.com',
    include_package_data=True,
    py_modules=[],
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'monitor = hafas.cli:monitor',
        ]
    },
)
