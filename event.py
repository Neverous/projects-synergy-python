# Maciej Szeptuch (Neverous) <neverous@neverous.info> (C) 2012

CONNECTED			= 1
DISCONNECTED		= 2
OPTIONSSET			= 3
OPTIONSRESET		= 4
SCREENREQUEST		= 5
CLIPBOARDGET		= 6
CLIPBOARDSET		= 7
FOCUSIN				= 8
FOCUSOUT			= 9
MOUSEMOTION			= 10
MOUSERELATIVEMOTION	= 11
MOUSEWHEEL			= 12
MOUSEBUTTONUP		= 13
MOUSEBUTTONDOWN		= 14
KEYUP				= 15
KEYDOWN				= 16
KEYREPEAT			= 17
SCREENSAVER			= 18
GAMEPADBUTTONS		= 19
GAMEPADSTICKS		= 20
GAMEPADTRIGGERS		= 21
GAMEPADFEEDBACK		= 22
GAMEPADTIMING		= 23

_name = (
	'INVALID', 'CONNECTED', 'DISCONNECTED',
	'OPTIONS SET', 'OPTIONS RESET', 'SCREEN REQUEST',
	'CLIPBOARD GET', 'CLIPBOARD SET',
	'FOCUS IN', 'FOCUS OUT',
	'MOUSE MOTION', 'MOUSE RELATIVE MOTION', 'MOUSE WHEEL', 'MOUSE BUTTON UP', 'MOUSE BUTTON DOWN',
	'KEY UP', 'KEY DOWN', 'KEY REPEAT',
	'SCREEN SAVER',
	'GAMEPAD BUTTONS', 'GAMEPAD TRIGGERS', 'GAMEPAD FEEDBACK', 'GAMEPAD TIMING REQUEST',
)

class Event(object):
	def __init__(self, type, **kwargs):
		self.type = type
		self.__dict__.update(kwargs)

	def __str__(self):
		return 'Event %s %s' % (_name[self.type], ' '.join(['%s=%s' % (key, value) for key, value in self.__dict__.items() if key != 'type']))
