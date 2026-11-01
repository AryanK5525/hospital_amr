from setuptools import setup
import os
from glob import glob

package_name = 'hospital_amr'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.world') + glob('worlds/*.sdf')),
        (os.path.join('share', package_name, 'maps'),
            glob('maps/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='aryan',
    maintainer_email='aryan@todo.todo',
    description='Hospital Medicine Delivery AMR Simulation',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'test_mover = hospital_amr.test_mover:main',
            'delivery_manager = hospital_amr.delivery_manager:main',
        ],
    },
)
