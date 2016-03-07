# Maciej Szeptuch (Neverous) <neverous@neverous.info> (C) 2012

# Simple logging
import time

def message(level, msg, *values):
	print '[%s|%s] %s' % (time.strftime('%H:%M:%S %d-%m-%Y'), level, msg % values)

def debug(msg, *values): pass#message('DEBUG', msg, *values)
def info(msg, *values): message('INFO', msg, *values)
def error(msg, *values): message('ERROR', msg, *values)
def warning(msg, *values): message('WARNING', msg, *values)
