__appname__ = 'ps_trainer'
__author__ = 'rick.choi'
__version__ = '0.1'

import os
from appdirs import AppDirs
__appdirs__ = AppDirs(__appname__, __author__, __version__)
__logdir__ = __appdirs__.user_log_dir
__logfile__ = os.path.join(__appdirs__.user_log_dir, 'ps_trainer.log')
__datadir__ = __appdirs__.user_data_dir
os.makedirs(__logdir__, exist_ok=True)
os.makedirs(__datadir__, exist_ok=True)
