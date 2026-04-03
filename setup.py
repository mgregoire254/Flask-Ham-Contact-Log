from setuptools import setup


setup(
    name='Contacts',
    version='1.0.0',
    packages=['Contacts'],
    package_dir={'Contacts': '.'},
    include_package_data=True,
    install_requires=[
        'flask',
    ],
)
