# Maciej Szeptuch (Neverous) <neverous@neverous.info> (C) 2012

import time
import socket
import select
import log
from protocol1_4 import *
from event import *

class ServerDisconnected(Exception): pass

class SynergyClient(object):
	def __init__(self, name, host, port, timeout = 2):
		self._times = 0
		self._host = host
		self._name = name
		self._port = port
		self._timeout = timeout
		self._ev = []
		self._sock = None
		self._data = ''
		self._supported = (
			(Hello,				self._serverHello),
			(EIncompatible,		self._serverIncompatible),
			(EBusy,				self._nameUsed),
			(EUnknown,			self._nameInvalid),
			(EBad,				self._protocolError),
			(QInfo,				self._screenInfo),
			(CInfoAck,			self._infoAcknowledgment),
			(DSetOptions,		self._optionsSet),
			(CResetOptions,		self._optionsReset),
			(CKeepAlive,		self._keepAlive),
			(CClose,			self._serverClose),
			(CNoop,				lambda: None),
			(CEnter,			self._focusIn),
			(CLeave,			self._focusOut),
			(CClipboard,		self._clipboardGet),
			(DClipboard,		self._clipboardSet),
			(CScreenSaver,		self._screenSaver),
			(EBad,				self._protocolError),
			(DMouseMove,		self._mouseMotion),
			(DMouseRelMove,		self._mouseRelativeMotion),
			(DMouseWheel,		self._mouseWheel),
			(DMouseDown,		self._mouseDown),
			(DMouseUp,			self._mouseUp),
			(DKeyDown,			self._keyDown),
			(DKeyUp,			self._keyUp),
			(DKeyRepeat,		self._keyRepeat),
			(DGameButtons,		self._gamepadButtons),
			(DGameSticks,		self._gamepadSticks),
			(DGameTriggers,		self._gamepadTriggers),
			(CGameTimingReq,	self._gamepadTiming),
		)

	def getEvents(self):
		while self._ev:
			yield self._ev.pop(0)

	# Socket handling

	def connect(self):
		self.disconnect()
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self._sock.setsockopt(socket.SOL_SOCKET, socket.TCP_NODELAY, 1)

		except socket.error, msg:
			log.warning('Cannot set TCP_NODELAY: %s', msg)

		try:
			log.debug('Connecting to %s:%d...', self._host, self._port)
			self._sock.connect((self._host, self._port))
			self._ev.append(Event(CONNECTED, host = self._host, port = self._port))

		except socket.error, msg:
			log.warning('Failed to connect to server: %s', msg)
			del self._sock
			self._sock = None
			return False

		return True
	
	def disconnect(self, reason = ''):
		if not self._sock:
			return

		self._sock.shutdown(socket.SHUT_RDWR)
		del self._sock
		self._sock = None
		self._ev.append(Event(DISCONNECTED, host = self._host, port = self._port, reason = reason))

	def read(self):
		if not self._sock:
			return

		data = ''
		if select.select([self._sock, ], [], [])[0]:
			try:
				data = self._sock.recv(4)
				(length, ), _ = unpack('%4i', data)
				data += self._sock.recv(length)

			except Exception, msg:
				log.warning('Read error: %s', msg)
				return ''

		log.debug('Got: %s', data)
		return data

	def write(self, data):
		if not self._sock:
			return False

		data = pack('%s', data)
		try:
			if select.select([], [self._sock, ], [])[1]:
				self._sock.send(data)
				log.debug('Sent: %s', data)
				return True

		except Exception, msg:
			log.warning('Write error: %s', msg)
			return False

	# Processing
	def process(self):
		while not self._sock:
			log.debug('Retry in %ds!', self._timeout ** self._times)
			time.sleep(self._timeout ** self._times)
			self._times = (self._times + 1) % 5
			self.connect()

		self._data += self.read()
		while self._data:
			(length, ), self._data = unpack('%4i', self._data)
			log.debug('Processing: %d %s', length, self._data[:4])
			if len(self._data) < length:
				log.error('Incomplete message from server: %s(%d)!', self._data, length)
				self.disconnect()
				return

			try:
				self._data = self._parse(self._data[:4], self._data)

			except ServerDisconnected:
				self._data = ''
				self.disconnect()
				return

	def _parse(self, code, data):
		for (fmt, handle) in self._supported:
			if fmt.startswith(code):
				args, data = unpack(fmt, data)
				handle(*args)
				return data

		else:
			self._invalidMessage(code)
			#raise ServerDisconnected

	def _invalidMessage(self, code):
		log.warning('Invalid message from server: %s', code)

	# Commands
	def _protocolError(self):
		log.error('Protocol error!')
		raise ServerDisconnected

	def _nameInvalid(self):
		log.error('Invalid client name!')
		raise ServerDisconnected

	def _nameUsed(self):
		log.warning('Client name already in use. Waiting for 10s before reconnect!.')
		time.sleep(10)
		raise ServerDisconnected

	def _serverIncompatible(self, major, minor):
		log.error('Incompatible server protocol: %d.%d vs. %d.%d', major, minor, PROTOCOL_MAJOR, PROTOCOL_MINOR)
		raise ServerDisconnected

	def _serverClose(self):
		log.info('Server disconnected!')
		raise ServerDisconnected

	def _serverHello(self, major, minor):
		log.info('Connected to server protocol version %d.%d.', major, minor)
		if not self.write(pack(HelloBack, PROTOCOL_MAJOR, PROTOCOL_MINOR, self._name)): raise ServerDisconnected

	def _screenInfo(self):
		log.debug('Server requested screen information.')
		self._ev.append(Event(SCREENREQUEST))

	def screenInfo(self, x, y, width, height, wrap = 0, mx = 0, my = 0):
		log.debug('Sending screen information.')
		if not self.write(pack(DInfo, x, y, width, height, wrap, mx, my)):
			self.disconnect()
			return False

		return True

	def _infoAcknowledgment(self):
		log.debug('Server connected properly!')
		self._mouse = (0, 0)

	def _optionsReset(self):
		log.debug('Server requested options reset!')
		self._ev.append(Event(OPTIONSRESET))

	def _optionsSet(self, opts):
		log.debug('Server set options: %s', opts)
		self._ev.append(Event(OPTIONSSET, data = opts))

	def _keepAlive(self):
		self._keepalive = time.time()
		if not self.write(pack(CKeepAlive)): raise ServerDisconnected

	def _focusIn(self, x, y, seq, mask):
		log.info('Mouse entered screen (%d, %d) [%d] M%x.', x, y, seq, mask)
		self._ev.append(Event(FOCUSIN, x = x, y = y, mask = mask, seq = seq))

	def _focusOut(self):
		log.info('Mouse left screen')
		self._ev.append(Event(FOCUSOUT))

	def _clipboardSet(self, id, seq, clipboard):
		log.debug('Got clipboard(%d): %s.', id, clipboard)
		self._ev.append(Event(CLIPBOARDSET, id = id, data = clipboard, seq = seq))

	def _clipboardGet(self, id, seq):
		log.debug('Got clipboard request %d.', id)
		self._ev.append(Event(CLIPBOARDGET, id = id, seq = seq))

	def _mouseMotion(self, x, y):
		log.debug('Mouse motion -> (%d, %d)', x, y)
		self._mouse = (x, y)
		self._ev.append(Event(MOUSEMOTION, x = x, y = y))

	def _mouseRelativeMotion(self, dx, dy):
		log.debug('Mouse motion [%d, %d]', dx, dy)
		self._mouse = (self._mouse[0] + dx, self._mouse[1] + dy)
		self._ev.append(Event(MOUSERELATIVEMOTION, dx = dx, dy = dy))

	def _mouseWheel(self, dx, dy):
		log.debug('Mouse wheel [%d, %d]', dx, dy)
		self._ev.append(Event(MOUSEWHEEL, dx = dx, dy = dy))

	def _mouseDown(self, id):
		log.debug('Mouse button down [%d]', id)
		self._ev.append(Event(MOUSEBUTTONDOWN, button = id))

	def _mouseUp(self, id):
		log.debug('Mouse button up [%d]', id)
		self._ev.append(Event(MOUSEBUTTONUP, button = id))

	def _keyUp(self, id, mask, button):
		log.debug('Key up [%d#%d %d]', id, mask, button)
		self._ev.append(Event(KEYUP, key = id, mask = mask, button = button))

	def _keyDown(self, id, mask, button):
		log.debug('Key down [%d#%d %d]', id, mask, button)
		self._ev.append(Event(KEYDOWN, key = id, mask = mask, button = button))

	def _keyRepeat(self, id, mask, count, button):
		log.debug('Key down [%d#%d %d] * %d', id, mask, button, count)
		self._ev.append(Event(KEYREPEAT, key = id, mask = mask, button = button, count = count))

	def _screenSaver(self, enable):
		log.debug('Screen saver %d', enable)
		self._ev.append(Event(SCREENSAVER, enable = enable))

	def _gamepadButtons(self, id, mask):
		log.debug('Gamepad buttons %d #%d', id, mask)
		self._ev.append(Event(GAMEPADBUTTONS, id = id, buttons = mask))

	def _gamepadSticks(self, id, x1, y1, x2, y2):
		log.debug('Gamepad sticks %d (%d, %d) (%d, %d)', id, x1, y1, x2, y2)
		self._ev.append(Event(GAMEPADSTICKS, id = id, x1 = x1, y1 = y1, x2 = x2, y2 = y2))

	def _gamepadTriggers(self, id, trig1, trig2):
		log.debug('Gamepad triggers %d %d %d', id, trig1, trig2)
		self._ev.append(Event(GAMEPADTRIGGERS, id = id, trigger1 = trig1, trigger2 = trig2))

	def _gamepadTiming(self):
		log.debug('Gamepad timing request.')
		self._ev.append(Event(GAMEPADTIMING))

	def gamepadTiming(self, freq):
		log.debug('Sending gamepad timing.')
		if not self.write(pack(CGameTimingResp, freq)):
			self.disconnect()
			return False

		return True

	def _gamepadFeedback(self, id, m1, m2):
		log.debug('Gamepad feedback %d %d %d', id, m1, m2)
		self._ev.append(Event(GAMEPADFEEDBACK, id = id, m1 = m1, m2 = m2))
