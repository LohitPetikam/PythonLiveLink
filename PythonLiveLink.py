from multiprocessing.connection import Client, Listener
import sys
import traceback
import logging
import threading
import time
import pickle
import io


envdir = {}

def exec_user_code(source, envdir):
	ss = io.StringIO("Successfully executed")

	try:
		exec(source, envdir)
	except Exception:
		ss.seek(0)
		ss.write("Exception in user code:\n")
		ss.write("-"*60 + "\n")
		traceback.print_exc(file=ss)
		ss.write("-"*60 + "\n")

	ss.seek(0)
	out = ss.read()
	print(out)
	return out

def eval_expression(expr, envdir):
	ss = io.StringIO("")

	try:
		ret = eval(expr, envdir)
	except Exception:
		ss.seek(0)
		ss.write("Exception in user code:\n")
		ss.write("-"*60 + "\n")
		traceback.print_exc(file=ss)
		ss.write("-"*60 + "\n")

	ss.seek(0)
	return ss.read()

class LiveLink(object):
	"""Interface for clients to communicate with server"""
	def __init__(self, port):

		address = ('localhost', port)
		self.conn = Client(address, authkey=b'livelink password')

		if sys.version_info < (3,0):
			self.conn.send("protocol2")
			print(self.conn.recv())

	def execute(self, code):
		msg = {'cmd':'exec', 'code':code}
		self.conn.send(msg)
		print(self.conn.recv())

	def send_msg(self, msg):
		self.conn.send(msg)
		print(self.conn.recv())

	def close_server(self):
		self.conn.send('close')
		print(self.conn.recv())

def client_test():

	address = ('localhost', 6000)
	conn = Client(address, authkey=b'livelink password')

	conn.send("protocol2")
	print(conn.recv())

	conn.send(['a', 2.5, None, int, sum])
	print(conn.recv())

	conn.send('close')

	msg = conn.recv()
	print(msg)

	conn.close()

def send_protocol(conn, msg, protocol=None):
	if protocol is None:
		conn.send(msg)
	else:
		data = pickle.dumps(msg, protocol=protocol)
		conn.send_bytes(data)

def thread_function(name, exit_event, envdir):
	logging.info("Thread %s: starting", name)
	address = ('localhost', 6000)     # family is deduced to be 'AF_INET'
	listener = Listener(address, authkey=b'livelink password')
	logging.info('hosting on %s', address)
	logging.info('waiting for connection...')
	conn = listener.accept()
	logging.info('connection accepted from %s', listener.last_accepted)

	protocol = None
	while not exit_event.wait(1):
		msg = conn.recv()
		msg_type = type(msg)
		if msg_type == type(''):
			if msg == 'protocol2':
				logging.info('setting protocol = 2')
				protocol = 2
				send_protocol(conn, 'ok switching to protocol 2', protocol)
				continue
			elif msg == 'close':
				send_protocol(conn, 'goodbye', protocol)
				conn.close()
				break
		elif msg_type == type({}):
			if not 'cmd' in msg:
				send_protocol(conn, 'invalid cmd', protocol)
				continue

			cmd = msg['cmd']
			if cmd == 'exec':
				if not 'code' in msg:
					send_protocol(conn, 'no code given', protocol)
					continue

				ret = exec_user_code(msg['code'], envdir)
				send_protocol(conn, ret, protocol)
				continue
			elif cmd == 'eval':
				if not 'expr' in msg:
					send_protocol(conn, 'no expr given', protocol)
					continue

				ret = eval_expression(msg['expr'], envdir)
				send_protocol(conn, ret, protocol)
				continue

		logging.info('received: %s', repr(type(msg)))
		logging.info(msg)
		send_protocol(conn, 'thanks', protocol)

	listener.close()
	logging.info("Thread %s: finishing", name)




def main():
	format = "%(asctime)s: %(message)s"
	logging.basicConfig(format=format, level=logging.INFO,
						datefmt="%H:%M:%S")

	exit_event = threading.Event()
	test_thread = threading.Thread(target=thread_function, args=(1,exit_event, envdir))
	logging.info("Main \t: starting server thread...")
	test_thread.start()

	while True:
		source = input("> ")
		if source == '!q':
			exit_event.set()
			test_thread.join()
			break
		exec_user_code(source, envdir)
	
	print('user quit')

if __name__ == '__main__':
	main()