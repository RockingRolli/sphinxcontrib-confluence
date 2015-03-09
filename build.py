from pybuilder.core import Author, use_plugin, init

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")


name = "sphinxcontrib-confluence"
default_task = "publish"


###
# Meta information
###
url = 'http://rvo.name'
description = "We don't need a description"
authors = [
    Author('Roland von Ohlen', 'webwork@rvo-host.net'),
]
license = 'Nope'
summary = 'Foobar'
version = '0.1.0'


@init
def set_properties(project):
    project.depends_on('Sphinx>=0.6')

    project.set_property('distutils_classifiers', [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ])
