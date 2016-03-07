# Maciej Szeptuch (Neverous) <neverous@neverous.info> (C) 2012

# Synergy protocol 1.4 implementation for python

# PySynergy protocol version
PROTOCOL_MAJOR	= 1
PROTOCOL_MINOR	= 4

# Synergy protocol available messages.
Hello			= "Synergy%2i%2i"				# kMsgHello (major version, minor version)								- handshake request
HelloBack		= "Synergy%2i%2i%s"				# kMsgHelloBack (major version, minor version, client name)				- handshake response
QInfo			= "QINF"						# kMsgQInfo																- info request
DInfo			= "DINF%2i%2i%2i%2i%2i%2i%2i"	# kMsgDInfo ([shape] x, y, width, height, wrap?, [mouse] pos x, pos y)	- screen info
CInfoAck		= "CIAK"						# kMsgCInfoAck															- info acknowledgment
DSetOptions		= "DSOP%4I"						# kMsgDSetOptions (options)												- setting options
CResetOptions	= "CROP"						# kMsgCResetOptions														- clearing options
CNoop		 	= "CNOP"						# kMsgCNoop																- noop(why? there is keepalive)
CClose			= "CBYE"						# kMsgCClose															- close connection
CEnter			= "CINN%2i%2i%4i%2i"			# kMsgCEnter (pos x, pos y, synergy sequence number, mask)				- screen in focus
CLeave	 		= "COUT"						# kMsgCLeave															- screen out of focus
CClipboard	 	= "CCLP%1i%4i"					# kMsgCClipboard (clipboard id, synergy sequence number)				- request for clipboard data
DClipboard		= "DCLP%1i%4i%s"				# kMsgDClipboard (clipboard id, synergy sequence number, data)			- setting clipboard
CScreenSaver	= "CSEC%1i"						# kMsgCScreenSaver (state 1/0)											- en/disabling screensaver
CKeepAlive		= "CALV"						# kMsgKeepAlive															- keep alive packet
CGameTimingReq	= "CGRQ"						# kMsgCGameTimingReq													- gamepad polling frequency request
CGameTimingResp	= "CGRS%2i"						# kMsgCGameTimingResp (frequency)										- gamepad polling frequency
DKeyDown		= "DKDN%2i%2i%2i"				# kMsgDKeyDown (key id, mask, button)									- key down
DKeyUp			= "DKUP%2i%2i%2i"				# kMsgDKeyUp (key id, mask, button)										- key up
DKeyRepeat		= "DKRP%2i%2i%2i%2i"			# kMsgDKeyRepeat (key id, mask, count, button)							- key repeat
DMouseDown		= "DMDN%1i"						# kMsgDMouseDown (button id)											- mouse button down
DMouseUp		= "DMUP%1i"						# kMsgDMouseUp (button id)												- mouse button up
DMouseMove		= "DMMV%2i%2i"					# kMsgDMouseMove (pos x, pos y)											- mouse movement
DMouseRelMove	= "DMRM%2i%2i"					# kMsgDMouseRelMove (dx, dy)											- mouse relative movement
DMouseWheel		= "DMWM%2i%2i"					# kMsgDMouseWheel (dx, dy)												- mouse wheel
DGameButtons	= "DGBT%1i%2i"					# kMsgDGameButtons (gamepad id, buttons mask)							- gamepad buttons
DGameSticks		= "DGST%1i%2i%2i%2i%2i"			# kMsgDGameSticks (gamepad id, [stick1] x, y, [stick2] x, y)			- gamepad analog sticks
DGameTriggers	= "DGTR%1i%1i%1i"				# kMsgDGameTriggers (gamepad id, trigger1, trigger2)					- gamepad triggers
DGameFeedback	= "DGFB%1i%2i%2i"				# kMsgDGameFeedback (gamepad id, m1?, m2?)								- gamepad feedback
EIncompatible	= "EICV%2i%2i"					# kMsgEIncompatible (major version, minor version)						- incompatible protocols
EBusy			= "EBSY"						# kMsgEBusy																- client name in use already
EUnknown		= "EUNK"						# kMsgEUnknown															- invalid client name
EBad			= "EBAD"						# kMsgEBad																- protocol error(invalid command etc)

# Format Types
AVAILABLE_TYPES = 'iIsS%'

# Synergy protocol 1.x formatting implementation
# NOTE: when sending/reciving packets there is also 32bit size before each one(socket/stream should handle it)
def pack(fmt, *argv):
	res = ''
	size = len(fmt)
	a = p = 0
	while p < size:
		if fmt[p] != '%':
			res += fmt[p]
			p += 1
			continue
		
		p += 1
		if fmt[p] == '%':
			res += '%'
			p += 1
			continue

		_size, p = parseInt(fmt, p)
		if not fmt[p] in AVAILABLE_TYPES: raise TypeError('Unavailable type "%s" in %s!' % (fmt[p], fmt))

		_tmp = packType[fmt[p]](_size, argv[a])
		res += _tmp
		a += 1
		p += 1

	return res

def unpack(fmt, data):
	res = []
	fsize = len(fmt)
	dsize = len(data)
	p = d = 0
	while p < fsize and d < dsize:
		if fmt[p] != '%':
			if fmt[p] != data[d]: raise AttributeError('Invalid data: "%s" vs "%s"!' % (data, fmt))
			
			p += 1
			d += 1
			continue

		p += 1
		if fmt[p] == '%':
			if fmt[p] != data[d]: raise AttributeError('Invalid data: "%s" vs "%s"!' % (data, fmt))

			p += 1
			d += 1
			continue

		_size, p = parseInt(fmt, p)
		if not fmt[p] in AVAILABLE_TYPES: raise TypeError('Unavailable type "%s" in %s!' % (fmt[p], fmt))

		_arg, d = unpackType[fmt[p]](_size, data, d)
		p += 1
		res.append(_arg)

	return tuple(res), data[d:]

def _packInteger(_size, _int):
	if not _size in (1, 2, 4): raise AttributeError('Invalid integer size "%d"!' % _size)
	
	res = ''
	for _s in xrange(_size):
		res += chr((_int >> (8 * (_size - _s - 1))) & 0xff)

	return res


def _unpackInteger(_size, data, d):
	if not _size in (1, 2, 4): raise AttributeError('Invalid integer size "%d"!' % _size)

	res = 0
	for _s in xrange(_size):
		res += ord(data[d]) << (8 * (_size - _s - 1))
		d += 1

	return res, d

def _packVector(_size, _vec):
	if not _size in (1, 2, 4): raise AttributeError('Invalid integer size "%d"!' % _size)

	_len = len(_vec)
	res = ''.join([chr((_len >> (8 * (3 - _s))) & 0xff) for _s in xrange(4)])

	for _int in _vec:
		for _s in xrange(_size):
			res += chr((_int >> (8 * (_size - _s - 1))) & 0xff)

	return res

def _unpackVector(_size, data, d):
	if not _size in (1, 2, 4): raise AttributeError('Invalid integer size "%d"!' % _size)

	_len = 0
	res = []
	for _s in xrange(4):
		_len += ord(data[d]) << (8 * (3 - _s))
		d += 1

	for _ in xrange(_len):
		_tmp = 0
		for _s in xrange(_size):
			_tmp += ord(data[d]) << (8 * (_size - _s - 1))
			d += 1

		res.append(_tmp)

	return tuple(res), d

def _packString(_size, _string):
	if _size != 0: raise AttributeError('String must not have size argument(given %d)!' % _size)

	_len = len(_string)
	return ''.join([chr((_len >> (8 * (3 - _s))) & 0xff) for _s in xrange(4)]) + _string

def _unpackString(_size, data, d):
	if _size != 0: raise AttributeError('String must not have size argument(given %d)!' % _size)

	_len = 0
	for _s in xrange(4):
		_len += ord(data[d]) << (8 * (3 - _s))
		d += 1

	_res = data[d:d+_len]
	if len(_res) != _len: raise AttributeError('Invalid string "%s"!' % data[d:])

	return data[d:d+_len], d + _len

def _packBytes(_size, _string):
	return _packString(_size, ''.join([chr(c) for c in _string]))

def _unpackBytes(_size, data, d):
	_bytes, d = _unpackString(_size, data, d)
	return tuple(map(ord, _bytes)), d

def parseInt(data, pos):
	res = 0
	while '0' <= data[pos] <= '9':
		res = 10 * res + ord(data[pos]) - ord('0')
		pos += 1

	return res, pos

packType = {
	'i': _packInteger,
	'I': _packVector,
	's': _packString,
	'S': _packBytes,
}

unpackType = {
	'i': _unpackInteger,
	'I': _unpackVector,
	's': _unpackString,
	'S': _unpackBytes,
}

