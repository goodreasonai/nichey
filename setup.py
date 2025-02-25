from setuptools import setup, find_packages

setup(
    name='nichey',
    version='0.0.3',
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    package_data={
        'nichey': ['static/*', 'static/**/*'],  # Include static folder and all subdirectories
    },
    install_requires=[
        'requests',
        'openai',
        'pydantic',
        'beautifulsoup4',
        'requests-toolbelt',
        'unstructured[csv,doc,docx,epub,md,msg,odt,org,ppt,pptx,rtf,rst,tsv,xlsx]',
        'pymupdf',
        'tiktoken',
        'python-slugify',
        'flask',
        'flask_cors',
        'tqdm'
    ],
    author='Gordon Kamer',
    author_email='gordon@goodreason.ai',
    description='Build a wiki for your research topic',
    long_description="# Nichey: Generate a wiki for your niche.\n\nFor more information, check out Nichey on [GitHub](https://github.com/goodreasonai/nichey).",
    long_description_content_type='text/markdown',
    url='https://github.com/goodreasonai/nichey',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
