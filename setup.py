from setuptools import setup

setup(
  name = 'WIOpy',
  packages = ['WIOpy'],
  version = '0.0.9',
  license='MIT',
  
  description = 'Walmart IO API python wrapper',

  author = 'CoderJosh',
  author_email = '74162303+CoderJoshDK@users.noreply.github.com',
  url = 'https://github.com/CoderJoshDK/WIOpy',
  download_url = 'https://github.com/CoderJoshDK/WIOpy/archive/refs/tags/v_009_alpha.tar.gz',
  keywords = ['API', 'Wrapper', 'Python', 'Walmart', 'Affiliate', 'WalmartIO', 'Async', 'AIOHTTP'],
  install_requires=[
          'requests',
          'pycryptodome',
          'aiohttp'
      ],
  
  classifiers=[
      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
      'Development Status :: 3 - Alpha',      

      'Intended Audience :: Developers',      # Define that your audience are developers
      'Topic :: Software Development :: Build Tools',
      
      'License :: OSI Approved :: MIT License',
  
      'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6',
      'Programming Language :: Python :: 3.7',
      'Programming Language :: Python :: 3.8',
      'Programming Language :: Python :: 3.9',
  ],
)
