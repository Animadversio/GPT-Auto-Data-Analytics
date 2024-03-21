from setuptools import setup, find_packages

setup(
    name='auto_analytics',
    version='0.1.0',
    author='Binxu Wang',
    author_email='binxu_wang@hms.harvard.edu',
    description='Automated local data analytics and report generation powered by GPT models.',
    long_description="",
    long_description_content_type='text/markdown',
    url='https://github.com/Animadversio/GPT-Auto-Data-Analytics',
    packages=find_packages(),
    install_requires=[
        'openai_multi_tool_use_parallel_patch',
        'nbformat',
        'openai',
        # Add your package dependencies here
        # Example:
        # 'numpy>=1.19.2',
        # 'pandas>=1.1.3',
        # 'transformers>=4.0.0',
    ],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    keywords='data analytics, GPT, automation',
)