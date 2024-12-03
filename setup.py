from setuptools import setup, find_packages


setup(
    name='news_scraper',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'seleniumbase',
        'selenium-wire',
        'selenium',
        'blinker==1.7.0'
    ],
    author='Karim Dabbouz',
    author_email='hey@karim.ooo',
    description='A Python with utils to scrape articles from any news outlet.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/karimdabbouz/news_scraper',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)