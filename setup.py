import setuptools

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="UGFlib",
	version="0.0.1",
	author="shedarshian",
	author_email="shedarshian@gmail.com",
	description="A library developed by shedarshian.",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/shedarshian/UGFlib",
	packages=setuptools.find_packages(),
	classifiers=[
		"Development Status :: 1 - Planning",
		"Environment :: Console",
		"Intended Audience :: Developers",
		"Intended Audience :: Science/Research",
		"License :: OSI Approved :: MIT License",
		"Programming Language :: Python",
		"Operating System :: OS Independent",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Topic :: Scientific/Engineering :: Physics"
	],
	python_requires='>=2.7',
)
