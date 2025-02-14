from setuptools import setup, find_packages

setup(
    name='wiki',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
        'openai',
        'pydantic',
        'beautifulsoup4',
        'requests-toolbelt',
        'sqlalchemy',
        'unstructured[csv,doc,docx,epub,md,msg,odt,org,ppt,pptx,rtf,rst,tsv,xlsx]',
        'pymupdf',
        'tiktoken',
        'python-slugify'
    ],
    author='Gordon Kamer',
    author_email='gordon@goodreason.ai',
    description='Build a wiki for any research topic',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/goodreasonai/wiki',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
