from setuptools import setup

setup(
    name='ps_trainer',
    version='0.1',
    description='personal problem solving trainer',
    url='#',
    author='Rick Jinhwan Choi',
    author_email='jinhwanlazy@gmail.com',
    license='MIT',
    packages=['ps_trainer'],
    entry_points={
        'console_scripts': ['ps_trainer=ps_trainer.main:main']
    },
)
