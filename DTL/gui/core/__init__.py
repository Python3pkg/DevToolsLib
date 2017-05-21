"""
Selects the appropreate core for the environment you are running in
"""
Core = None

# initialize the ui system for the environment we are running in
try:
	from .maya.core import MayaCore as Core
except:
	pass

try:
	from .studiomax.core import StudioMaxCore as Core
except:
	pass

try:
	from .motionbuilder.core import MotionBuilderCore as Core
except:
	pass

if Core is None:
	from .external import Core

Core = Core.instance()
