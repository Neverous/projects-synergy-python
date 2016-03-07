import event
import synergyclient

_cnt = synergyclient.SynergyClient('raspi.lan', '192.168.1.5', 24800)
_cnt.connect()
while True:
	_cnt.process()
	for ev in _cnt.getEvents():
		print ev
		if ev.type == event.SCREENREQUEST:
			_cnt.screenInfo(0, 0, 1280, 800)
