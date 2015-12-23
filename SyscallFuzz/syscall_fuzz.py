
""" QNX syscall fuzzer
<alex.plaskett@mwrinfosecurity.com> - 2015
BB10 Libc exports
TODO: 
- Remote logging server
- Add support for COID's outside of the process
- Use timertimeout to do non-blocking?
- Implement ConnectClientInfoExt
- Add support for power parameters
while true; do python3.2 syscall_fuzz.py; done
"""

from ctypes import *
from util import *
import socket

# flags for _channel_connect_attr 
#define _NTO_CHANCON_ATTR_CONFLAGS		0x00000001
#define _NTO_CHANCON_ATTR_CHANFLAGS		0x00000002
#define _NTO_CHANCON_ATTR_MODE			0x00000004
#define _NTO_CHANCON_ATTR_BUFSIZE		0x00000008
#define _NTO_CHANCON_ATTR_MAXBUF		0x00000010
#define _NTO_CHANCON_ATTR_EVENT			0x00000020
#define _NTO_CHANCON_ATTR_CURMSGS		0x00000040
#define _NTO_CHANCON_ATTR_CRED			0x00000080

CHAN_CONNECT_FLAGS = [0x00000001,0x00000002,0x00000004,0x00000008,0x00000010,0x00000020,0x00000040,0x00000080]

class sigevent(Structure):
	_fields_ = [
	("sival_int",c_ulong),
	("sival_ptr",c_void_p)
	]

class ev(Structure):
	_fields_ = [
	("event",sigevent),
	("coid",c_ulong)
	]

class _cred_info(Structure):
	_fields_ = [
	("ruid",c_ulong),
	("euid",c_ulong),
	("suid",c_ulong),
	("rgid",c_ulong),
	("egid",c_ulong),
	("sgid",c_ulong),
	("ngroups",c_ulong),
	("grouplist",c_ulong * 8) # 8 seems to the what it is atm.
	]

class _channel_connect_attr(Union):
	_fields_ = [
	("flags",c_ulong),
	("mode_t",c_ulong),
	("bufsize",c_ulong),
	("maxbuf",c_ulong),
	("ev",ev),
	("num_curmsgs",c_ulong),
	("cred",_cred_info)
	]

# Channel flags
#define _NTO_CHF_FIXED_PRIORITY		0x0001
#define _NTO_CHF_UNBLOCK			0x0002
#define _NTO_CHF_THREAD_DEATH		0x0004
#define _NTO_CHF_DISCONNECT			0x0008
#define _NTO_CHF_NET_MSG			0x0010
#define _NTO_CHF_SENDER_LEN			0x0020
#define _NTO_CHF_COID_DISCONNECT	0x0040
#define _NTO_CHF_REPLY_LEN			0x0080
#define _NTO_CHF_STICKY				0x0100
#define _NTO_CHF_ASYNC_NONBLOCK		0x0200
#define _NTO_CHF_ASYNC				0x0400
#define _NTO_CHF_GLOBAL				0x0800
#define _NTO_CHF_PRIVATE			0x1000u
#define _NTO_CHF_MSG_PAUSING		0x2000u
#define _NTO_CHF_SIG_RESTART		0x4000u
#define _NTO_CHF_UNBLOCK_TIMER		0x8000u

CHAN_FLAGS = [0x0001,0x0002,0x0004,0x0008,0x0010,0x0020,0x0040,0x0080,0x0100,0x0200,0x0400,0x0800,0x1000,0x2000,0x4000,0x8000]


# Conn flags
#define _NTO_COF_CLOEXEC		0x0001
#define _NTO_COF_DEAD			0x0002
#define _NTO_COF_NOSHARE		0x0040
#define _NTO_COF_NETCON			0x0080
#define _NTO_COF_NONBLOCK		0x0100
#define _NTO_COF_ASYNC			0x0200
#define _NTO_COF_GLOBAL			0x0400
#define _NTO_COF_NOEVENT		0x0800
#define _NTO_COF_INSECURE		0x1000

CONN_FLAGS = [0x0001,0x0002,0x0040,0x0080,0x0100,0x0200,0x0400,0x0800,0x1000]




#typedef struct iovec
#{
#    void    *iov_base;
#    size_t   iov_len;
#} iov_t

class iovec(Structure):
	_fields_ = [
	("iov_base",c_void_p),
	("iov_len",c_ulong)
	]

class _client_info(Structure):
	_fields_ = [
	("nd",c_ulong),
	("pid",c_ulong),
	("sid",c_ulong),
	("flags",c_ulong),
	("cred",_cred_info)
	]

class _vtid_info(Structure):
	_fields = [
	("tid",c_ulong),
	("coid",c_ulong),
	("priority",c_ulong),
	("srcmsglen",c_ulong),
	("keydata",c_ulong),
	("srcnd",c_ulong),
	("dstmsglen",c_ulong),
	("zero",c_ulong)
	]


class _msg_info(Structure):
	_fields_ = [
	("nd",c_ulong),
	("srcnd",c_ulong),
	("pid",c_ulong),
	("tid",c_ulong),
	("chid",c_ulong),
	("scoid",c_ulong),
	("coid",c_ulong),
	("msglen",c_ulong),
	("srcmsglen",c_ulong),
	("dstmsglen",c_ulong),
	("priority",c_ushort),
	("flags",c_ushort),
	("reserved",c_ulong)
	]

#define _server_info	_msg_info

class _asyncmsg_connection_descriptor(Structure):
	_fields_ = [
	("flags",c_ulong),
	("sendq",c_void_p),
	("sendq_size",c_ulong),
	("sendq_head",c_ulong),
	("sendq_tail",c_ulong),
	("sendq_free",c_ulong),
	("err",c_long),
	("ev",sigevent),
	("num_curmsg",c_ulong),
	("ttimer",c_ulong),
	("block_con",c_ulong),
	("mu",c_ulong),
	("reserve",c_ulong),
	]

#struct _asyncmsg_connection_descriptor {
#	unsigned flags;							/* flags for the async connection */
#	struct _asyncmsg_put_header *sendq;		/* send queue */
#	unsigned sendq_size;				    /* send queue size */
#	unsigned sendq_head;		            /* head of the send queue */
#	unsigned sendq_tail;		            /* tail of the send queue */
#	unsigned sendq_free;		            /* start of the free list */
#	int err;								/* error status of this connection */
#	struct sigevent ev;						/* the event to be sent for notification */
#	unsigned num_curmsg;					/* number of messages pending on this connection */
#	timer_t ttimer;							/* triggering timer */
#	pthread_cond_t block_con;				/* condvar for blocking if send header queue is full */
#	pthread_mutex_t mu;						/* mutex to protect the data structure and for the condvar */
#	unsigned reserve;						/* reserve */
#	struct _asyncmsg_connection_attr attr;	/* attribute of this connection */
#	unsigned reserves[3];					/* reserve */
#};

#struct _sighandler_info {
#	siginfo_t			siginfo;
#	void				(*handler)(_SIG_ARGS);
#	void				*context;
#	/* void				data[] */
#};

# This is broken currently.
class _siginfo(Structure):
	_fields_ = [
	("si_signo",c_ulong),
	("si_code",c_ulong),
	("si_errno",c_ulong),
	]

class _sighandler_info(Structure):
	_fields_ = [
	("siginfo",_siginfo),
	("handler",c_ulong),
	("context",c_ulong),
	]

class sigaction(Structure):
	_fields_ = [
	("_sa_handler",c_void_p),
	("sa_flags",c_ulong),
	("sa_mask",c_ulong),
	]

class sched_param(Structure):
	_fields_ = [
	("_priority",c_ulong),
	("_curpriority",c_ulong),
	("__spare",c_ulong),
	]


#struct _sched_info {
#	int					priority_min;
#	int					priority_max;
#	_Uint64t			interval;
#	int					priority_priv;
#	int					reserved[11];
#};

class sched_info(Structure):
	_fields_ = [
	("priority_min",c_ulong),
	("priority_max",c_ulong),	
	("interval",c_uint64),
	("priority_priv",c_ulong),
	("reserved",c_ulong)
	]

class sync_union(Union):
	_fields_ = [
	("count", c_ulong),
	("fd",c_long),
	("clockid",c_long)
	]

class nto_job_t(Structure):
	_fields_ = [
	("__u", sync_union),
	("__owner",c_ulong)
	]

class itimer(Structure):
	_fields_ = [
	("nsec", c_uint64),
	("interval_nsec",c_uint64)
	]	

class timerinfo(Structure):
	_fields_ = [
	("itime", itimer),
	("otime",itimer),
	("flags", c_ulong),
	("tid", c_ulong),
	("notify", c_ulong),
	("clockid", c_ulong),
	("overruns", c_ulong),
	("sigevent",sigevent)
	]

class _sync_attr(Structure):
	_fields_ = [
	("protocol", c_ulong),
	("flags", c_ulong),
	("__prioceiling", c_ulong),
	("__clockid", c_ulong),
	("reserved", c_ulong),
	]

class clockadjust(Structure):
	_fields_ = [
	("tick_count", c_ulong),
	("tick_nsec_inc", c_ulong),
	]

class _client_able(Structure):
	_field_ = [
	("ability", c_ulong),
	("flags", c_ulong),	
	("range_lo", c_ulong),
	("range_hi", c_ulong),	
	]

class nto_power_range(Structure):
	_fields_ = [
	("load",c_ushort),
	("duration",c_ushort)
	]

class nto_power_freq(Structure):
	_fields_ = [
	("performance",c_ulong),
	("low",nto_power_range),
	("high",nto_power_range)
	]

class nto_power_parameter(Structure):
	_fields_ = [
	("parameter_type",c_ushort),
	("clusterid",c_ulong),
	("spare",c_ulong),
	("u",nto_power_freq)
	]

class Syscall:

	def __init__(self,syscalls):
		self.libc = CDLL("libc.so")
		self.channel_ids = [0,1,1073741824]
		self.pids = [0,1]
		self.util = Util()
		self.scoids = [0]
		self.timer_ids = [0]
		self.connection_ids = [0]
		self.sync = nto_job_t() # global sync type
		self.syscalls = syscalls # so we can mutate in thread callback
		self.clock_ids = [0]

		self.remote_log = True
		if self.remote_log:
			self.server = "192.168.65.1"
			self.port = 50007
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			print('connecting to logging server...')
			self.sock.connect((self.server, self.port))

	# Not in neutrino.h
	def cache_flush(self):
		self.libc.CacheFlush()

	# Not sure args of this.
	def cache_flush_r(self):
		self.libc.CacheFlush_r()


	########################## Channel Creation Methods ##########################
	#extern int ChannelCreate(unsigned __flags);
	#extern int ChannelCreate_r(unsigned __flags);
	#extern int ChannelCreateExt(unsigned __flags, mode_t __mode, size_t __bufsize, unsigned __maxnumbuf, const struct sigevent *__ev, struct _cred_info *__cred);
	#extern int ChannelDestroy(int __chid);
	#extern int ChannelDestroy_r(int __chid);
	#extern int ConnectAttach(_Uint32t __nd, pid_t __pid, int __chid, unsigned __index, int __flags);
	#extern int ConnectAttach_r(_Uint32t __nd, pid_t __pid, int __chid, unsigned __index, int __flags);
	#extern int ConnectAttachExt(_Uint32t __nd, pid_t __pid, int __chid, unsigned __index, int __flags, struct _asyncmsg_connection_descriptor *__cd);
	#extern int ConnectDetach(int __coid);
	#extern int ConnectDetach_r(int __coid);
	#extern int ConnectServerInfo(pid_t __pid, int __coid, struct _server_info *__info);
	#extern int ConnectServerInfo_r(pid_t __pid, int __coid, struct _server_info *__info);
	#extern int ConnectClientInfo(int __scoid, struct _client_info *__info, int __ngroups);
	#extern int ConnectClientInfo_r(int __scoid, struct _client_info *__info, int __ngroups);
	#extern int ConnectFlags(pid_t __pid, int __coid, unsigned __mask, unsigned __bits);
	#extern int ConnectFlags_r(pid_t __pid, int __coid, unsigned __mask, unsigned __bits);
	#extern int ChannelConnectAttr(unsigned __id, union _channel_connect_attr *__old_attr, union _channel_connect_attr *__new_attr, unsigned __flags);
	
	# New calls
	# extern int ConnectClientInfoExt(int __scoid, struct _client_info **__info_pp, int flags);
	# extern int ClientInfoExtFree(struct _client_info **__info_pp);
	# extern int ConnectClientInfoAble(int __scoid, struct _client_info **__info_pp, int flags, struct _client_able * const abilities, const int nable);

    # https://developer.blackberry.com/native/reference/core/com.qnx.doc.neutrino.lib_ref/topic/c/channelcreate.html
	def channel_create(self):
		flags = self.util.choice(CHAN_FLAGS) 

		if (self.util.chance(2)):
			flags = self.util.choice(CHAN_FLAGS) | self.util.choice(CHAN_FLAGS) | self.util.choice(CHAN_FLAGS)

			self.log_remote("ChannelCreate")
		ret = self.libc.ChannelCreate(flags)
		if (ret != -1):
			print("ChannelCreate coid = ", ret)
			self.channel_ids.append(ret)
		else:
			print("ChannelCreate failed")
		

	def channel_create_r(self):
		flags = self.util.choice(CHAN_FLAGS)

		if (self.util.chance(2)):
			flags = self.util.choice(CHAN_FLAGS) | self.util.choice(CHAN_FLAGS) | self.util.choice(CHAN_FLAGS)
		self.log_remote("ChannelCreate_r")
		ret = self.libc.ChannelCreate_r(flags)
		if (ret != -1):
			print("channel_create_r coid = ", ret)
			self.channel_ids.append(ret)
		else:
			print("ChannelCreate_r failed")
		

	# http://www.qnx.com/developers/docs/660/index.jsp?topic=%2Fcom.qnx.doc.neutrino.lib_ref%2Ftopic%2Fc%2Fchannelcreateext.html
	def channel_create_ext(self):
		# extern int ChannelCreateExt(unsigned __flags, mode_t __mode, size_t __bufsize, unsigned __maxnumbuf, const struct sigevent *__ev, struct _cred_info *__cred);
		flags = self.util.choice(CHAN_FLAGS)

		flags |= 0x0200 # _NTO_CHF_ASYNC_NONBLOCK
		flags |= 0x0800 # _NTO_CHF_GLOBAL

		if (self.util.chance(4)):
			flags = self.util.choice(CHAN_FLAGS) | self.util.choice(CHAN_FLAGS) | self.util.choice(CHAN_FLAGS)

		mode = self.util.R(0xffffffff)
		bufsize = self.util.R(0xffffffff)				
		maxnumbuf = self.util.R(0xffffffff)
		ev = sigevent()
		ev.sival_int = self.util.R(0xffffffff)
		ev.sival_ptr = self.util.R(0xffffffff)

		cred = _cred_info()
		self.log_remote("ChannelCreateExt")
		print("Bufsize = ",bufsize)
		print("Maxnumbuf = ",maxnumbuf)
		ret = self.libc.ChannelCreateExt(flags,mode,bufsize,maxnumbuf,byref(ev),byref(cred))
		if (ret != -1):
			print("ChannelCreateExt coid = ", ret)
			self.channel_ids.append(ret)
		else:
			print("ChannelCreateExt failed")
		

    # http://www.qnx.com/developers/docs/6.3.2/neutrino/lib_ref/c/channeldestroy.html
	def channel_destory(self):
		chid = self.util.choice(self.channel_ids)
		if (self.util.chance(4)):
			chid = self.util.R(0xffffffff)
		self.log_remote("ChannelDestroy")
		ret = self.libc.ChannelDestroy(chid)
		if (ret != 1):
			print("ChannelDestroy worked")
		

	def channel_destroy_r(self):
		chid = self.util.choice(self.channel_ids)
		if (self.util.chance(4)):
			chid = self.util.R(0xffffffff)
		self.log_remote("ChannelDestroy_r")
		ret = self.libc.ChannelDestroy_r(chid)
		if (ret != 1):
			print("ChannelDestroy_r worked")
		

	# http://www.qnx.com/developers/docs/6.3.0SP3/neutrino/lib_ref/c/connectattach.html
	def connect_attach(self):
		nd = 0
		pid = self.util.choice(self.pids)
		chid = self.util.choice(self.channel_ids)
		index = self.util.R(0xffffffff)
		if (self.util.chance(2)):
			index = 1073741824 # _NTO_SIDE_CHANNEL

		flags = self.util.choice(CONN_FLAGS)

		if (self.util.chance(4)):
			flags = self.util.choice(CONN_FLAGS) | self.util.choice(CONN_FLAGS)

		self.log_remote("ConnectAttach")
		ret = self.libc.ConnectAttach(nd,pid,chid,index,flags)
		if (ret != -1):
			print("ConnectAttach = ", ret)
			self.connection_ids.append(ret)
		else:
			print("ConnectAttach failed")
		

	def connect_attach_r(self):
		nd = 0
		pid = self.util.choice(self.pids)
		chid = self.util.choice(self.channel_ids)
		index = self.util.R(0xffffffff)
		if (self.util.chance(2)):
			index = 1073741824 # _NTO_SIDE_CHANNEL

		flags = self.util.choice(CONN_FLAGS)

		if (self.util.chance(4)):
			flags = self.util.choice(CONN_FLAGS) | self.util.choice(CONN_FLAGS)

		self.log_remote("ConnectAttach")
		ret = self.libc.ConnectAttach_r(nd,pid,chid,index,flags)
		if (ret != -1):
			print("ConnectAttach = ", ret)
			self.connection_ids.append(ret)
		else:
			print("ConnectAttach failed")
			

	# This is undocumented
	# extern int ConnectAttachExt(_Uint32t __nd, pid_t __pid, int __chid, unsigned __index, int __flags, struct _asyncmsg_connection_descriptor *__cd);
	def connect_attach_ext(self):
		nd = 0
		pid = self.util.choice(self.pids)
		chid = self.util.choice(self.channel_ids)
		index = self.util.R(0xffffffff)
		if (self.util.chance(2)):
			index = 1073741824 # _NTO_SIDE_CHANNEL

		flags = self.util.choice(CONN_FLAGS)

		if (self.util.chance(4)):
			flags = self.util.choice(CONN_FLAGS) | self.util.choice(CONN_FLAGS)
		
		cd = _asyncmsg_connection_descriptor()
		cd.flags = self.util.R(0xffffffff)
		cd.senq = self.util.R(0xffffffff)
		cd.sendq_size = self.util.R(0xffffffff)
		cd.sendq_head = self.util.R(0xffffffff)
		cd.sendq_tail = self.util.R(0xffffffff)
		cd.sendq_free = self.util.R(0xffffffff)
		cd.err = self.util.R(0xffffffff)
		ev = sigevent()
		cd.ev = ev
		cd.num_curmsg = self.util.R(0xffffffff)
		cd.ttimer = self.util.R(0xffffffff)
		cd.block_con = self.util.R(0xffffffff)
		cd.mu = self.util.R(0xffffffff)
		cd.reserve = 0
		self.log_remote("ConnectAttachExt")
		ret = self.libc.ConnectAttachExt(nd,pid,chid,index,flags,byref(cd))
		if (ret != -1):
			print("ConnectAttachExt = ", ret)
			self.connection_ids.append(ret)
		else:
			print("ConnectAttachExt failed")
		self.log_remote("ConnectAttachExt")	

	# http://www.qnx.com/developers/docs/6.3.0SP3/neutrino/lib_ref/c/connectdetach.html
	def connect_detach(self):
		coid = self.util.choice(self.connection_ids)
		self.log_remote("ConnectDetach")
		ret = self.libc.ConnectDetach(coid)
		if (ret != -1):
			print("ConnectDetach ok = ", ret)
		else:
			print("ConnectDetach failed")	
		self.log_remote("ConnectDetach")

	def connect_detach_r(self):
		coid = self.util.choice(self.connection_ids)
		self.log_remote("ConnectDetach_r")
		ret = self.libc.ConnectDetach_r(coid)
		if (ret != -1):
			print("ConnectDetach_r ok = ", ret)
		else:
			print("ConnectDetach_r failed")	
		self.log_remote("ConnectDetach_r")

    # http://www.qnx.com/developers/docs/6.4.0/neutrino/lib_ref/c/connectserverinfo.html
	def connect_server_info(self):
		##extern int ConnectServerInfo(pid_t __pid, int __coid, struct _server_info *__info);
		pid = self.util.choice(self.pids)
		coid = self.util.choice(self.connection_ids)
		info = _msg_info()
		self.log_remote("ConnectServerInfo")
		ret = self.libc.ConnectServerInfo(pid,coid,byref(info))
		if (ret != -1):
			print("ConnectServerInfo ok = ", ret)
			print("scoid = ", info.scoid)
			self.scoids.append(info.scoid)
		else:
			print("ConnectServerInfo failed")	
		self.log_remote("ConnectServerInfo")

	def connect_server_info_r(self):
		##extern int ConnectServerInfo(pid_t __pid, int __coid, struct _server_info *__info);
		pid = self.util.choice(self.pids)
		coid = self.util.choice(self.connection_ids)
		info = _msg_info()
		self.log_remote("ConnectServerInfo_r")
		ret = self.libc.ConnectServerInfo_r(pid,coid,byref(info))
		if (ret != -1):
			print("ConnectServerInfo_r ok = ", ret)
			print("scoid = ", info.scoid)
			self.scoids.append(info.scoid)
		else:
			print("ConnectServerInfo_r failed")
		self.log_remote("ConnectServerInfo_r")		

	# http://www.qnx.com/developers/docs/6.3.0SP3/neutrino/lib_ref/c/connectclientinfo.html
	def connect_client_info(self):
		#extern int ConnectClientInfo(int __scoid, struct _client_info *__info, int __ngroups);
		scoid = self.util.choice(self.connection_ids)
		info = _client_info()
		ngroups = self.util.R(0xffffffff)
		self.log_remote("ConnectClientInfo")
		ret = self.libc.ConnectClientInfo(scoid,byref(info),ngroups)
		if (ret != -1):
			print("ConnectClientInfo ok = ", ret)
		else:
			print("ConnectClientInfo failed")
		self.log_remote("ConnectClientInfo")		

	# http://www.qnx.com/developers/docs/6.3.0SP3/neutrino/lib_ref/c/connectclientinfo.html
	def connect_client_info_r(self):
		#extern int ConnectClientInfo(int __scoid, struct _client_info *__info, int __ngroups);
		scoid = self.util.choice(self.connection_ids)
		info = _client_info()
		ngroups = self.util.R(0xffffffff)
		self.log_remote("ConnectClientInfo_r")
		ret = self.libc.ConnectClientInfo_r(scoid,byref(info),ngroups)
		if (ret != -1):
			print("ConnectClientInfo_r ok = ", ret)
		else:
			print("ConnectClientInfo_r failed")
		self.log_remote("ConnectClientInfo_r")		

	def connect_flags(self):
		#extern int ConnectFlags(pid_t __pid, int __coid, unsigned __mask, unsigned __bits);
		pid = self.util.choice(self.pids)
		coid = self.util.choice(self.connection_ids)
		# TODO: Fix mask / bits here
		mask = self.util.R(0xffffffff)
		bits = self.util.R(0xffffffff)
		self.log_remote("ConnectFlags")
		ret = self.libc.ConnectFlags(pid,coid,mask,bits)
		if (ret != -1):
			print("ConnectFlags ok = ", ret)
		else:
			print("ConnectFlags failed")
			


	def connect_flags_r(self):
		#extern int ConnectFlags(pid_t __pid, int __coid, unsigned __mask, unsigned __bits);
		pid = self.util.choice(self.pids)
		coid = self.util.choice(self.connection_ids)
		mask = self.util.R(0xffffffff)
		bits = self.util.R(0xffffffff)
		self.log_remote("ConnectFlags_r")
		ret = self.libc.ConnectFlags_r(pid,coid,mask,bits)
		if (ret != -1):
			print("ConnectFlags_r ok = ", ret)
		else:
			print("ConnectFlags_r failed")	
		

	# This is interesting, conn_attr is complicated struct.
	# Undocumented function
	def channel_conn_attr(self):
		# #extern int ChannelConnectAttr(unsigned __id, union _channel_connect_attr *__old_attr, union _channel_connect_attr *__new_attr, unsigned __flags);
		__id = self.util.choice(self.connection_ids)

		__old_attr = _channel_connect_attr()
		__old_attr.flags = self.util.R(0xffffffff)
		__old_attr.mode_t = self.util.R(0xffffffff)
		__old_attr.bufsize = self.util.R(0xffffffff)
		__old_attr.maxbuf = self.util.R(0xffffffff)
		ev = sigevent()
		__old_attr.num_curmsgs = self.util.R(0xffffffff)
		cred = _cred_info()
		__old_attr.cred = cred

		__new_attr = _channel_connect_attr()

		__new_attr = _channel_connect_attr()
		__new_attr.flags = self.util.R(0xffffffff)
		__new_attr.mode_t = self.util.R(0xffffffff)
		__new_attr.bufsize = self.util.R(0xffffffff)
		__new_attr.maxbuf = self.util.R(0xffffffff)
		ev = sigevent()
		__new_attr.num_curmsgs = self.util.R(0xffffffff)
		cred = _cred_info()
		__new_attr.cred = cred

		flags = self.util.choice(CHAN_CONNECT_FLAGS)
		self.log_remote("ChannelConnectAttr")
		ret = self.libc.ChannelConnectAttr(__id,__old_attr,__new_attr,flags)
		if (ret != -1):
			print("ChannelConnectAttr ok = ", ret)
		else:
			print("ChannelConnectAttr failed")	
			

	# extern int ConnectClientInfoAble(int __scoid, struct _client_info **__info_pp, int flags, struct _client_able * const abilities, const int nable);
	def connect_client_info_able(self):
		__scoid = self.util.choice(self.connection_ids)
		__info_pp = c_ulong(0)
		flags = 0
		abilities = _client_able()
		nable = self.util.R(0xffffffff)
		self.log_remote("ConnectClientInfoAble")
		ret = self.libc.ConnectClientInfoAble(__scoid,byref(__info_pp),flags,byref(abilities),nable)
		if (ret != -1):
			print("ConnectClientInfoAble ok = ", ret)
		else:
			print("ConnectClientInfoAble failed")	
					


	# extern int ConnectClientInfoExt(int __scoid, struct _client_info **__info_pp, int flags);
	def connect_client_info_ext(self):
		scoid = self.util.choice(self.connection_ids)
		ci = _client_info()
		flags = 1
		self.log_remote("ConnectClientInfoExt")
		ret = self.libc.ConnectClientInfoExt(scoid,byref(ci),flags)
		if (ret != -1):
			print("ConnectClientInfoExt ok = ", ret)
		else:
			print("ConnectClientInfoExt failed")
			

	#extern int ClientInfoExtFree(struct _client_info **__info_pp);
	def client_info_ext_free(self):
		value = c_ulong
		ptr = POINTER(value)()
		self.log_remote("ClientInfoExtFree")
		ret = self.libc.ClientInfoExtFree(byref(ptr))
		if (ret != -1):
			print("ClientInfoExtFree ok = ", ret)
		else:
			print("ClientInfoExtFree failed")	
				


	################################ Messaging Methods ###############################

	def msg_send(self):
		# extern int MsgSend(int __coid, const void *__smsg, int __sbytes, void *__rmsg, int __rbytes);
		send_buf = create_string_buffer(self.util.R(0xffff))
		recv_buf = create_string_buffer(self.util.R(0xffff))
		coid = self.util.choice(self.connection_ids)
		__smsg = send_buf
		sbytes = len(__smsg)
		__rmsg = recv_buf
		rbytes = len(__rmsg)
		ret = self.libc.MsgSend(coid,__smsg,len(__smsg),__rmsg,len(__rmsg))
		if (ret != -1):
			print("MsgSend ok = ", ret)
		else:
			print("MsgSend failed")			

	def msg_send_r(self):
		# extern int MsgSend(int __coid, const void *__smsg, int __sbytes, void *__rmsg, int __rbytes);
		send_buf = create_string_buffer(self.util.R(0xffff))
		recv_buf = create_string_buffer(self.util.R(0xffff))
		coid = self.util.choice(self.connection_ids)
		__smsg = send_buf
		sbytes = len(__smsg)
		__rmsg = recv_buf
		rbytes = len(__rmsg)
		ret = self.libc.MsgSend(coid,__smsg,len(__smsg),__rmsg,len(__rmsg))
		if (ret != -1):
			print("MsgSend_r ok = ", ret)
		else:
			print("MsgSend_r failed")		

	# extern int MsgSendnc(int __coid, const void *__smsg, int __sbytes, void *__rmsg, int __rbytes);
	# nc is non-cancelation point
	def msg_send_nc(self):
		send_buf = create_string_buffer(self.util.R(0xfffff))
		recv_buf = create_string_buffer(self.util.R(0xfffff))
		coid = self.util.choice(self.connection_ids)
		__smsg = send_buf
		sbytes = len(__smsg)
		__rmsg = recv_buf
		rbytes = len(__rmsg)
		ret = self.libc.MsgSendnc(coid,__smsg,len(__smsg),__rmsg,len(__rmsg))
		if (ret != -1):
			print("MsgSendNc ok = ", ret)
		else:
			print("MsgSendNc failed")		

	def msg_send_nc_r(self):
		send_buf = create_string_buffer(self.util.R(0xffff))
		recv_buf = create_string_buffer(self.util.R(0xffff))
		coid = self.util.choice(self.connection_ids)
		__smsg = send_buf
		sbytes = len(__smsg)
		__rmsg = recv_buf
		rbytes = len(__rmsg)
		ret = self.libc.MsgSendnc(coid,__smsg,len(__smsg),__rmsg,len(__rmsg))
		if (ret != -1):
			print("MsgSendNc_r ok = ", ret)
		else:
			print("MsgSendNc_r failed")	

	#extern int MsgSendsv(int __coid, const void *__smsg, int __sbytes, const struct iovec *__riov, int __rparts);
	def msg_send_sv(self):
		coid = self.util.choice(self.connection_ids)
		send_buf = create_string_buffer(self.util.R(0xfffff))
		sbytes = len(send_buf)
		iov = iovec()
		iov.iov_base = self.util.R(0xffffffff)
		iov.iov_len = self.util.R(0xffffffff)
		rparts = 0
		ret = self.libc.MsgSendsv(coid,send_buf,sbytes,byref(iov),rparts)
		if (ret != -1):
			print("MsgSendsv ok = ", ret)
		else:
			print("MsgSendsv failed")	


	def msg_send_sv_r(self):
		coid = self.util.choice(self.connection_ids)
		send_buf = create_string_buffer(self.util.R(0xfffff))
		sbytes = len(send_buf)
		iov = iovec()
		iov.iov_base = self.util.R(0xffffffff)
		iov.iov_len = self.util.R(0xffffffff)
		rparts = 0
		ret = self.libc.MsgSendsv(coid,send_buf,sbytes,byref(iov),rparts)
		if (ret != -1):
			print("MsgSendsv_r ok = ", ret)
		else:
			print("MsgSendsv_r failed")	

	# extern int MsgSendsvnc(int __coid, const void *__smsg, int __sbytes, const struct iovec *__riov, int __rparts);
	def msg_send_svnc(self):
		coid = self.util.choice(self.connection_ids)
		send_buf = create_string_buffer(self.util.R(0xfffff))
		sbytes = len(send_buf)
		iov = iovec()
		iov.iov_base = self.util.R(0xffffffff)
		iov.iov_len = self.util.R(0xffffffff)
		rparts = 0
		ret = self.libc.MsgSendsvnc(coid,send_buf,sbytes,byref(iov),rparts)
		if (ret != -1):
			print("MsgSendsvnc ok = ", ret)
		else:
			print("MsgSendsvnc failed")	

	def msg_send_svnc_r(self):
		coid = self.util.choice(self.connection_ids)
		send_buf = create_string_buffer(10)
		sbytes = len(send_buf)
		iov = iovec()
		iov.iov_base = self.util.R(0xffffffff)
		iov.iov_len = self.util.R(0xffffffff)
		rparts = 0
		ret = self.libc.MsgSendsvnc_r(coid,send_buf,sbytes,byref(iov),rparts)
		if (ret != -1):
			print("MsgSendsvnc_r ok = ", ret)
		else:
			print("MsgSendsvnc_r failed")	

	# extern int MsgSendv(int __coid, const struct iovec *__siov, int __sparts, const struct iovec *__riov, int __rparts);
	# extern int MsgSendv_r(int __coid, const struct iovec *__siov, int __sparts, const struct iovec *__riov, int __rparts);
	def msg_send_v(self):
		coid = self.util.choice(self.connection_ids)
		siov = iovec()
		siov.iov_base = self.util.R(0xffffffff)
		siov.iov_len = self.util.R(0xffffffff)
		sparts = 0
		riov = iovec()
		riov.iov_base = self.util.R(0xffffffff)
		riov.iov_len = self.util.R(0xffffffff)
		rparts = 0
		ret = self.libc.MsgSendv(coid,byref(siov),sparts,byref(riov),rparts)
		if (ret != -1):
			print("MsgSendv ok = ", ret)
		else:
			print("MsgSendv failed")	

	def msg_send_v_r(self):
		coid = self.util.choice(self.connection_ids)
		siov = iovec()
		siov.iov_base = self.util.R(0xffffffff)
		siov.iov_len = self.util.R(0xffffffff)
		sparts = 0
		riov = iovec()
		riov.iov_base = self.util.R(0xffffffff)
		riov.iov_len = self.util.R(0xffffffff)
		rparts = 0
		ret = self.libc.MsgSendv(coid,byref(siov),sparts,byref(riov),rparts)
		if (ret != -1):
			print("MsgSendv_r ok = ", ret)
		else:
			print("MsgSendv_r failed")	

	# These syscalls block
	#extern int MsgReceive(int __chid, void *__msg, int __bytes, struct _msg_info *__info);
	#extern int MsgReceive_r(int __chid, void *__msg, int __bytes, struct _msg_info *__info);
	def msg_receive(self):
		chid = self.util.choice(self.channel_ids)
		__msg = create_string_buffer(10)
		bytes = 0
		__info = _msg_info()
		ret = self.libc.MsgReceive(chid,__msg,bytes,byref(__info))
		if (ret != -1):
			print("MsgReceive ok = ", ret)
		else:
			print("MsgReceive failed")	

	def msg_receive_r(self):
		chid = self.util.choice(self.channel_ids)
		__msg = create_string_buffer(10)
		l = len(__msg)
		__info = _msg_info()
		ret = self.libc.MsgReceive(chid,__msg,l,byref(__info))
		if (ret != -1):
			print("MsgReceive_r ok = ", ret)
		else:
			print("MsgReceive_r failed")		

	#extern int MsgReceivev(int __chid, const struct iovec *__iov, int __parts, struct _msg_info *__info);
	#extern int MsgReceivev_r(int __chid, const struct iovec *__iov, int __parts, struct _msg_info *__info);
	def msg_receive_v(self):
		chid = self.util.choice(self.channel_ids)
		iov = iovec()
		__parts = 0
		__info = _msg_info()
		ret = self.libc.MsgReceivev(chid,iov,__parts,__info)
		if (ret != -1):
			print("MsgReceivev ok = ", ret)
		else:
			print("MsgReceivev failed")		

	def msg_receive_v_r(self):
		chid = self.util.choice(self.channel_ids)
		iov = iovec()
		__parts = 0
		__info = _msg_info()
		ret = self.libc.MsgReceivev_r(chid,iov,__parts,__info)
		if (ret != -1):
			print("MsgReceivev_r ok = ", ret)
		else:
			print("MsgReceivev_r failed")		

	#extern int MsgReceivePulse(int __chid, void *__pulse, int __bytes, struct _msg_info *__info);
	#extern int MsgReceivePulse_r(int __chid, void *__pulse, int __bytes, struct _msg_info *__info);
	def msg_receive_pulse(self):
		chid = self.util.choice(self.channel_ids)
		buf = create_string_buffer(256)
		__bytes = 0
		__info = None
		ret = self.libc.MsgReceivePulse(chid,buf,__bytes,__info)
		if (ret != -1):
			print("MsgReceivePulse ok = ", ret)
		else:
			print("MsgReceivePulse failed")		

	def msg_receive_pulse_r(self):
		chid = self.util.choice(self.channel_ids)
		buf = create_string_buffer(256)
		__bytes = 0
		__info = None
		ret = self.libc.MsgReceivePulse(chid,buf,__bytes,__info)
		if (ret != -1):
			print("MsgReceivePulse_r ok = ", ret)
		else:
			print("MsgReceivePulse_r failed")	

	#extern int MsgReceivePulsev(int __chid, const struct iovec *__iov, int __parts, struct _msg_info *__info);
	#extern int MsgReceivePulsev_r(int __chid, const struct iovec *__iov, int __parts, struct _msg_info *__info);
	# todo

	#extern int MsgReply(int __rcvid, int __status, const void *__msg, int __bytes);
	#extern int MsgReply_r(int __rcvid, int __status, const void *__msg, int __bytes);

	def msg_reply(self):
		rcvid = 0
		__status = 0
		__msg = create_string_buffer(256)
		bytes = 0
		ret = self.libc.MsgReply(rcvid,__status,__msg,bytes)
		if (ret != -1):
			print("MsgReply ok = ", ret)
		else:
			print("MsgReply failed")	

	def msg_reply_r(self):
		rcvid = 0
		__status = 0
		__msg = create_string_buffer(256)
		bytes = 0
		ret = self.libc.MsgReply_r(rcvid,__status,__msg,bytes)
		if (ret != -1):
			print("MsgReply_r ok = ", ret)
		else:
			print("MsgReply_r failed")	

	#extern int MsgReplyv(int __rcvid, int __status, const struct iovec *__iov, int __parts);
	#extern int MsgReplyv_r(int __rcvid, int __status, const struct iovec *__iov, int __parts);
	def msg_reply_v(self):
		rcvid = 0
		__status = 0
		iov = iovec()
		__parts = 0
		self.libc.MsgReplyv(rcvid,__status,byref(iov),__parts)

	def msg_reply_v_r(self):
		rcvid = 0
		__status = 0
		iov = iovec()
		__parts = 0
		self.libc.MsgReplyv_r(rcvid,__status,byref(iov),__parts)

	#extern int MsgReadiov(int __rcvid, const struct iovec *__iov, int __parts, int __offset, int __flags);
	#extern int MsgReadiov_r(int __rcvid, const struct iovec *__iov, int __parts, int __offset, int __flags);
	def msg_read_iov(self):
		rcvid = 0
		iov = iovec()
		__parts = 0
		__offset = 0
		__flags = 0
		self.libc.MsgReadiov(rcvid,byref(iov),__parts,__offset,__flags)


	def msg_read_iov_r(self):
		rcvid = 0
		iov = iovec()
		__parts = 0
		__offset = 0
		__flags = 0
		self.libc.MsgReadiov_r(rcvid,byref(iov),__parts,__offset,__flags)

	#extern int MsgRead(int __rcvid, void *__msg, int __bytes, int __offset);
	#extern int MsgRead_r(int __rcvid, void *__msg, int __bytes, int __offset);
	def msg_read(self):
		rcvid = 0
		__msg = create_string_buffer(256)
		__bytes = 0
		__offset = 0
		self.libc.MsgRead(rcvid,__msg,__bytes,__offset)

	def msg_read_r(self):
		rcvid = 0
		__msg = create_string_buffer(256)
		__bytes = 0
		__offset = 0
		self.libc.MsgRead_r(rcvid,__msg,__bytes,__offset)

	#extern int MsgReadv(int __rcvid, const struct iovec *__iov, int __parts, int __offset);
	#extern int MsgReadv_r(int __rcvid, const struct iovec *__iov, int __parts, int __offset);
	def msg_readv(self):
		__rcvid = 0
		iov = iovec()
		__parts = 0
		__offset = 0
		self.libc.MsgReadv(__rcvid,byref(iov),__parts,__offset)

	def msg_readv_r(self):
		__rcvid = 0
		iov = iovec()
		__parts = 0
		__offset = 0
		self.libc.MsgReadv_r(__rcvid,byref(iov),__parts,__offset)

	#extern int MsgWrite(int __rcvid, const void *__msg, int __bytes, int __offset);
	#extern int MsgWrite_r(int __rcvid, const void *__msg, int __bytes, int __offset);
	def msg_write(self):
		__rcvid = 0
		__msg = create_string_buffer(256)
		__bytes = len(__msg)
		__offset = 0
		self.libc.MsgWrite(__rcvid,__msg,__bytes,__offset)

	def msg_write_r(self):
		__rcvid = 0
		__msg = create_string_buffer(256)
		__bytes = len(__msg)
		__offset = 0
		self.libc.MsgWrite_r(__rcvid,__msg,__bytes,__offset)

	#extern int MsgWritev(int __rcvid, const struct iovec *__iov, int __parts, int __offset);
	#extern int MsgWritev_r(int __rcvid, const struct iovec *__iov, int __parts, int __offset);
	def msg_write_v(self):
		__rcvid = 0
		iov = iovec()
		__parts = 0
		__offset = 0
		self.libc.MsgWritev(__rcvid,byref(iov),__parts,__offset)

	def msg_write_v_r(self):
		__rcvid = 0
		iov = iovec()
		__parts = 0
		__offset = 0
		self.libc.MsgWritev_r(__rcvid,byref(iov),__parts,__offset)

	#extern int MsgSendPulse(int __coid, int __priority, int __code, int __value);
	#extern int MsgSendPulse_r(int __coid, int __priority, int __code, int __value);
	def msg_send_pulse(self):
		__coid = self.util.choice(self.connection_ids)
		__priority = self.util.R(0xffffffff)
		__code = self.util.R(0xffffffff) # TODO: find out pulse codes
		__value = self.util.R(0xffffffff)
		ret = self.libc.MsgSendPulse(__coid,__priority,__code,__value)
		if (ret != -1):
			print("MsgSendPulse ok", ret)
		else:
			print("MsgSendPulse failed")

	def msg_send_pulse_r(self):
		__coid = 0
		__priority = 0
		__code = 0 # TODO: find out pulse codes
		__value = 0
		self.libc.MsgSendPulse(__coid,__priority,__code,__value)

	# extern int MsgDeliverEvent(int __rcvid, const struct sigevent *__event);
	# extern int MsgDeliverEvent_r(int __rcvid, const struct sigevent *__event);	
	def msg_deliver_event(self):
		__rcvid = 0
		__event = sigevent()
		ret = self.libc.MsgDeliverEvent(__rcvid,byref(__event))
		if (ret != -1):
			print("MsgDeliverEvent ok")
		else:
			print("MsgDeliverEvent failed")

	def msg_deliver_event_r(self):
		__rcvid = 0 # TODO: Store these in a list
		__event = sigevent()
		ret = self.libc.MsgDeliverEvent_r(__rcvid,byref(__event))
		if (ret != -1):
			print("MsgDeliverEvent ok")
		else:
			print("MsgDeliverEvent failed")

	# extern int MsgVerifyEvent(int __rcvid, const struct sigevent *__event);
	# extern int MsgVerifyEvent_r(int __rcvid, const struct sigevent *__event);
	def msg_verify_event(self):
		__rcvid = 0
		__event = sigevent()
		self.libc.MsgVerifyEvent(__rcvid,byref(__event))

	def msg_verify_event_r(self):
		__rcvid = 0
		__event = sigevent()
		self.libc.MsgVerifyEvent_r(__rcvid,byref(__event))

	#extern int MsgInfo(int __rcvid, struct _msg_info *__info);
	#extern int MsgInfo_r(int __rcvid, struct _msg_info *__info);
	def msg_info(self):
		__rcvid = 0
		__info = _msg_info()
		self.libc.MsgInfo(__rcvid,byref(__info))

	def msg_info_r(self):
		__rcvid = 0
		__info = _msg_info()
		self.libc.MsgInfo_r(__rcvid,byref(__info))

	#extern int MsgKeyData(int __rcvid, int __oper, _Uint32t __key, _Uint32t *__newkey, const struct iovec *__iov, int __parts);
	#extern int MsgKeyData_r(int __rcvid, int __oper, _Uint32t __key, _Uint32t *__newkey, const struct iovec *__iov, int __parts);
	def msg_key_data(self):
		__rcvid = 0
		__oper = self.util.choice([0,1,2])
		__key = self.util.R(0xffffffff)
		__newkey = c_ulong(self.util.R(0xffffffff))
		__iov = iovec()
		__iov.iov_base = self.util.R(0xffffffff)
		__iov.iov_len = self.util.R(0xffffffff)
		__parts = self.util.R(0xffffffff)
		ret = self.libc.MsgKeyData(__rcvid,__oper,__key,byref(__newkey),__iov,__parts)
		if (ret != -1):
			print("MsgKeyData ok", ret)
		else:
			print("MsgKeyData failed")

	def msg_key_data_r(self):
		__rcvid = 0
		__oper = self.util.choice([0,1,2])
		__key = self.util.R(0xffffffff)
		__newkey = c_ulong(self.util.R(0xffffffff))
		__iov = iovec()
		__iov.iov_base = self.util.R(0xffffffff)
		__iov.iov_len = self.util.R(0xffffffff)
		__parts = self.util.R(0xffffffff)
		ret = self.libc.MsgKeyData_r(__rcvid,__oper,__key,byref(__newkey),__iov,__parts)
		if (ret != -1):
			print("MsgKeyData_r ok", ret)
		else:
			print("MsgKeyData_r failed")

	#extern int MsgError(int __rcvid, int __err);
	#extern int MsgError_r(int __rcvid, int __err);
	def msg_error(self):
		__rcvid = 0
		__err = 0
		self.libc.MsgError(__rcvid,__err)

	def msg_error_r(self):
		__rcvid = 0
		__err = 0
		self.libc.MsgError_r(__rcvid,__err)	

	#extern int MsgCurrent(int __rcvid);
	#extern int MsgCurrent_r(int __rcvid);
	def msg_current(self):
		__rcvid = 0
		self.libc.MsgCurrent(__rcvid)

	def msg_current_r(self):
		__rcvid = 0
		self.libc.MsgCurrent_r(__rcvid)

	# extern int MsgSendAsyncGbl(int __coid, const void *__smsg, size_t __sbytes, unsigned __msg_prio);
	def msg_send_async_gbl(self):
		__coid = self.util.choice(self.connection_ids)
		__smsg = create_string_buffer(256)
		if self.util.chance(2):
			sbytes = len(__smsg)
		else:
			sbytes = self.util.R(0xffffffff)

		__msg_prio = 0
		ret = self.libc.MsgSendAsyncGbl(__coid,__smsg,sbytes,__msg_prio)
		if (ret != -1):
			print("MsgSendAsyncGbl ok", ret)
		else:
			print("MsgSendAsyncGbl failed")


	# extern int MsgSendAsync(int __coid);
	def msg_send_async(self):
		__coid = self.util.choice(self.connection_ids)
		ret = self.libc.MsgSendAsync(__coid)
		if (ret != -1):
			print("MsgSendAsync ok", ret)
		else:
			print("MsgSendAsync failed")

	# extern int MsgReceiveAsyncGbl(int __chid, void *__rmsg, size_t __rbytes, struct _msg_info *__info, int __coid);
	def msg_receive_async_gbl(self):
		__chid = self.util.choice(self.channel_ids)
		__rmsg = create_string_buffer(256)
		__rbytes = len(__rmsg)
		__info = _msg_info()
		__coid = self.util.choice(self.channel_ids)
		ret = self.libc.MsgReceiveAsyncGbl(__chid,__rmsg,__rbytes,__info,__coid)
		if (ret != -1):
			print("MsgReceiveAsyncGbl ok", ret)
		else:
			print("MsgReceiveAsyncGbl failed")

	# extern int MsgReceiveAsync(int __chid, const struct iovec *__iov, unsigned __parts);
	def msg_receive_async(self):
		__chid = 0
		iov = iovec()
		__parts = 0
		self.libc.MsgReceiveAsync(__chid,byref(iov),__parts)

    #extern int MsgPause(int __rcvid, unsigned __cookie);
	def msg_pause(self):
		__rcvid = 0
		__cookie = 0
		ret = self.libc.MsgPause(__rcvid,__cookie)
		if (ret != -1):
			print("MsgPause ok", ret)
		else:
			print("MsgPause failed")

	def msg_pause_r(self):
		__rcvid = 0
		__cookie = 0
		ret = self.libc.MsgPause_r(__rcvid,__cookie)
		if (ret != -1):
			print("MsgPause_r ok", ret)
		else:
			print("MsgPause_r failed")

	###################################### Signal Methods #####################################
	
	#extern int SignalKill(_Uint32t __nd, pid_t __pid, int __tid, int __signo, int __code, int __value);
	def signal_kill(self):
		nd = 0
		pid = self.util.choice(self.pids)
		tid = 0
		signo = self.util.R(64)
		code = self.util.R(0xffffffff)
		value = self.util.R(0xffffffff)
		ret = self.libc.SignalKill(nd,pid,tid,signo,code,value)
		if (ret != -1):
			print("SignalKill ok", ret)
		else:
			print("SignalKill failed")		


	#extern int SignalKill(_Uint32t __nd, pid_t __pid, int __tid, int __signo, int __code, int __value);
	def signal_kill_r(self):
		nd = 0
		pid = self.util.choice(self.pids)
		tid = 0
		signo = self.util.R(64)
		code = self.util.R(0xffffffff)
		value = self.util.R(0xffffffff)
		ret = self.libc.SignalKill_r(nd,pid,tid,signo,code,value)
		if (ret != -1):
			print("SignalKill_r ok", ret)
		else:
			print("SignalKill_r failed")		

	# extern int SignalReturn(struct _sighandler_info *__info);
	# This allows control of PC after a return has occured. 
	def signal_return(self):
		__info = _sighandler_info()
		ret = self.libc.SignalReturn(__info)
		if (ret != -1):
			print("SignalReturn ok", ret)
		else:
			print("SignalReturn failed")		

    #extern int SignalFault(unsigned __sigcode, void *__regs, _Uintptrt __refaddr);
    # This is undocumented and allows control of return addr
	def signal_fault(self):
		signo = self.util.R(64)
		regs = c_ulong() 
		refaddr = c_ulong()
		ret = self.libc.SignalFault(signo,byref(regs),byref(refaddr))
		if (ret != -1):
			print("SignalFault ok", ret)
		else:
			print("SignalFault failed")		

    # extern int SignalAction(pid_t __pid, void (*__sigstub)(void), int __signo, const struct sigaction *__act, struct sigaction *__oact);
	# implement this 
	def signal_action(self):
		pid = self.util.chTimoice(self.pids)
		sigstub = c_ulong()
		signo = self.util.R(64)
		__act = sigaction()
		_oact = sigaction()
		ret = self.libc.SignalAction(pid,sigstub,signo,byref(__act),byref(_oact))
		if (ret != -1):
			print("SignalAction ok", ret)
		else:
			print("SignalAction failed")				

    # extern int SignalProcmask(pid_t __pid, int __tid, int __how, const sigset_t *__set, sigset_t *__oldset);
	def signal_procmask(self):
		pid = self.util.choice(self.pids)
		tid = 0
		how = self.util.R(5)
		__set = c_ulong()
		__oldset = c_ulong()
		ret = self.libc.SignalProcmask(pid,tid,how,byref(__set),byref(__oldset))
		if (ret != -1):
			print("SignalProcmask ok", ret)
		else:
			print("SignalProcmask failed")			

	# extern int SignalSuspend(const sigset_t *__set);
	def signal_suspend(self):
		__set = c_ulong()
		ret = self.libc.SignalSuspend(byref(__set))
		if (ret != -1):
			print("SignalSuspend ok", ret)
		else:
			print("SignalSuspend failed")		

	# extern int SignalWaitinfo(const sigset_t *__set, siginfo_t *__info);
	def signal_waitinfo(self):
		__set = c_ulong()
		__info = _siginfo()
		ret = self.libc.SignalWaitinfo(byref(__set),byref(__info))
		if (ret != -1):
			print("SignalWaitinfo ok", ret)
		else:
			print("SignalWaitinfo failed")			

	############################ Thread Methods ##################################

	# Add mutation within callback function
	def callback(a, b):
		print("ThreadCreate callback called!")
		return 0

	# extern int ThreadCreate(pid_t __pid, void *(*__func)(void *__arg), void *__arg, const struct _thread_attr *__attr);
	def thread_create(self):
		pid = self.util.choice(self.pids)
		CMPFUNC = CFUNCTYPE(c_void_p, POINTER(c_int))
		cmp_func = CMPFUNC(self.callback)
		self.log_remote("ThreadCreate")
		ret = self.libc.ThreadCreate(pid,cmp_func,0,0)
		if (ret != -1):
			print("ThreadCreate ok", ret)
		else:
			print("ThreadCreate failed")	
				

	# extern int ThreadCtl(int __cmd, void *__data);
	def thread_ctl(self):
		cmd = self.util.R(15)
		data = create_string_buffer(self.util.R(256))
		self.log_remote("ThreadCtl")	
		ret = self.libc.ThreadCtl(cmd,data)
		if (ret != -1):
			print("ThreadCtl ok", ret)
		else:
			print("ThreadCtl failed")	
			

	# extern int ThreadCtlExt(pid_t __pid, int __tid, int __cmd, void *__data);
	# undocumented
	def thread_ctl_ext(self):
		pid = self.util.choice(self.pids)
		tid = 0
		cmd = self.util.R(15)
		data = create_string_buffer(self.util.R(256))
		self.log_remote("ThreadCtlExt")
		ret = self.libc.ThreadCtlExt(cmd,data)
		if (ret != -1):
			print("ThreadCtlExt ok", ret)
		else:
			print("ThreadCtlExt failed")
		

	############################ Interupt Methods ##################################

	# extern int InterruptHookTrace(const struct sigevent *(*__handler)(int), unsigned __flags);
	def interupt_hook_trace(self):
		handler = c_ulong()
		flags = 0
		self.log_remote("InterruptHookTrace")
		ret = self.libc.InterruptHookTrace(byref(handler),flags)
		if (ret != -1):
			print("InterruptHookTrace ok", ret)
		else:
			print("InterruptHookTrace failed")	
		
	# extern int InterruptHookIdle(void (*__handler)(_Uint64t *, struct qtime_entry *), unsigned __flags);
	def interupt_hook_idle(self):
		handler = c_ulong()
		flags = 0
		self.log_remote("InterruptHookIdle")
		ret = self.libc.InterruptHookIdle(byref(handler),flags)
		if (ret != -1):
			print("InterruptHookIdle ok", ret)
		else:
			print("InterruptHookIdle failed")	
		

	# extern int InterruptHookIdle2(void (*__handler)(unsigned, struct syspage_entry *, struct _idle_hook *), unsigned __flags);
	def interupt_hook_idle2(self):
		handler = c_ulong()
		flags = 0
		self.log_remote("InterruptHookIdle2")
		ret = self.libc.InterruptHookIdle2(byref(handler),flags)
		if (ret != -1):
			print("InterruptHookIdle2 ok", ret)
		else:
			print("InterruptHookIdle2 failed")
		

	# extern int InterruptHookOverdriveEvent(const struct sigevent *__event, unsigned __flags);
	def interupt_hook_overdrive_event(self):
		__event = sigevent()
		flags = 0
		self.log_remote("InterruptHookOverdriveEvent")
		ret = self.libc.InterruptHookOverdriveEvent(byref(__event),flags)
		if (ret != -1):
			print("InterruptHookOverdriveEvent ok", ret)
		else:
			print("InterruptHookOverdriveEvent failed")	
		

	# extern int InterruptAttachEvent(int __intr, const struct sigevent *__event, unsigned __flags);
	def interupt_attach_event(self):
		intr = self.util.R(0xffffffff)
		__event = sigevent()
		flags = 0
		self.log_remote("InterruptAttachEvent")
		ret = self.libc.InterruptAttachEvent(intr,byref(__event),flags)
		if (ret != -1):
			print("InterruptAttachEvent ok", ret)
		else:
			print("InterruptAttachEvent failed")	
		

    # extern int InterruptAttach(int __intr, const struct sigevent *(*__handler)(void *__area, int __id), const void *__area, int __size, unsigned __flags);
	def interupt_attach_event(self):
		intr = self.util.R(0xffffffff)
		__event = sigevent()
		area = create_string_buffer(256)
		size = len(area)
		flags = 0
		self.log_remote("InterruptAttach")
		ret = self.libc.InterruptAttach(intr,byref(__event),area,size,flags)
		if (ret != -1):
			print("InterruptAttach ok", ret)
		else:
			print("InterruptAttach failed")
		

	# extern int InterruptDetach(int __id);
	def interupt_detach(self):
		_id = self.util.R(0xffffffff)
		self.log_remote("InterruptDetach")
		ret = self.libc.InterruptAttach(_id)
		if (ret != -1):
			print("InterruptDetach ok", ret)
		else:
			print("InterruptDetach failed")		
		

	# extern int InterruptWait(int __flags, const _Uint64t *__timeout);
	def interupt_wait(self):
		__flags = 0
		timeout = c_ulong()
		self.log_remote("InterruptWait")
		ret = self.libc.InterruptWait(__flags,byref(timeout))
		if (ret != -1):
			print("InterruptWait ok", ret)
		else:
			print("InterruptWait failed")
						

	# extern int InterruptCharacteristic(int __type, int __id, unsigned *__new, unsigned *__old);
	def interupt_characteristic(self):
		__type = 0
		_id = self.util.R(0xffffffff)
		_new = c_ulong()
		_old = c_ulong()
		self.log_remote("InterruptCharacteristic")
		ret = self.libc.InterruptCharacteristic(__type,_id,byref(_new),byref(_old))
		if (ret != -1):
			print("InterruptCharacteristic ok", ret)
		else:
			print("InterruptCharacteristic failed")	
			

	############################ Scheduler Methods #################################
	# extern int SchedGet(pid_t __pid, int __tid, struct sched_param *__param);
	def scheduler_get(self):
		pid = self.util.choice(self.pids)
		tid = 0
		_param = sched_param()
		self.log_remote("SchedGet")
		ret = self.libc.SchedGet(pid,tid,_param)
		if (ret != -1):
			print("SchedGet ok", ret)
		else:
			print("SchedGet failed")
		 	   	

	def scheduler_set(self):
		pid = self.util.choice(self.pids)
		tid = 0
		__algorithm = 0
		_param = sched_param()
		self.log_remote("SchedSet") 
		ret = self.libc.SchedSet(pid,tid,__algorithm,_param)
		if (ret != -1):
			print("SchedSet ok", ret)
		else:
			print("SchedSet failed")
		

	# extern int SchedInfo(pid_t __pid, int __algorithm, struct _sched_info *__info);
	def scheduler_info(self):
		pid = self.util.choice(self.pids)
		__algorithm = 0
		_info = sched_info()
		self.log_remote("SchedInfo") 
		ret = self.libc.SchedInfo(pid,__algorithm,byref(_info))
		if (ret != -1):
			print("SchedInfo ok", ret)
		else:
			print("SchedInfo failed") 
		  	

	# extern int SchedYield(void);
	def scheduler_yield(self):
		self.log_remote("SchedYield")
		ret = self.libc.SchedYield()
		if (ret != -1):
			print("SchedYield ok", ret)
		else:
			print("SchedYield failed")  
					

	# extern int SchedCtl(int __cmd, void *__data, size_t __length);
	def scheduler_ctl(self):
		cmd = 200+self.util.R(16)
		if (self.util.chance(5)):
			cmd = self.util.R(3)
		data = create_string_buffer(self.util.R(256))
		l = len(data)
		self.log_remote("SchedCtl")
		ret = self.libc.SchedCtl(cmd,data,l)
		if (ret != -1):
			print("SchedCtl ok", ret)
		else:
			print("SchedCtl failed")  
				

	# extern int SchedJobCreate(nto_job_t	*__job);
	# undocumented
	def scheduler_job_create(self):
		job = nto_job_t()
		self.log_remote("SchedJobCreate")
		ret = self.libc.SchedJobCreate(byref(job))
		if (ret != -1):
			print("SchedJobCreate ok", ret)
		else:
			print("SchedJobCreate failed")  	
				

	# extern int SchedJobDestroy(nto_job_t	*__job);
	def scheduler_job_destroy(self):
		job = nto_job_t()
		self.log_remote("SchedJobDestroy")
		ret = self.libc.SchedJobDestroy(byref(job))
		if (ret != -1):
			print("SchedJobDestroy ok", ret)
		else:
			print("SchedJobDestroy failed")  
				
	# extern int SchedWaypoint(nto_job_t *__job, const _Int64t *__new, _Int64t *__old);
	# undocumented
	def scheduler_waypoint(self):
		job = nto_job_t()
		new = c_ulong(self.util.R(0xffffffff))
		old = c_ulong(self.util.R(0xffffffff))
		self.log_remote("SchedWaypoint")
		ret = self.libc.SchedWaypoint(byref(job),byref(new),byref(old))
		if (ret != -1):
			print("SchedWaypoint ok", ret)
		else:
			print("SchedWaypoint failed") 
			

    # extern int SchedWaypoint2(nto_job_t *__job, const _Int64t *__new, const _Int64t *__max, _Int64t *__old);
    # undocumented
	def scheduler_waypoint2(self):
		job = nto_job_t()
		new = c_ulong(self.util.R(0xffffffff))
		m = c_ulong(self.util.R(0xffffffff))
		old = c_ulong(self.util.R(0xffffffff))
		self.log_remote("SchedWaypoint2") 
		ret = self.libc.SchedWaypoint2(byref(job),byref(new),byref(m),byref(old))
		if (ret != -1):
			print("SchedWaypoint2 ok", ret)
		else:
			print("SchedWaypoint2 failed") 	
		

	############################ Timer Methods ##################################

	# extern int TimerCreate(clockid_t __id, const struct sigevent *__notify);
	def timer_create(self):
		i = self.util.R(5)
		event = sigevent()
		ret = self.libc.TimerCreate(i,byref(event))
		if (ret != -1):
			print("TimerCreate ok", ret)
			self.timer_ids.append(ret)
		else:
			print("TimerCreate failed") 			

	# extern int TimerDestroy(timer_t __id);
	def timer_destroy(self):
		i = self.util.choice(self.timer_ids)
		event = sigevent()
		ret = self.libc.TimerDestroy(i)
		if (ret != -1):
			print("TimerDestroy ok", ret)
		else:
			print("TimerDestroy failed") 	

	# extern int TimerSettime(timer_t __id, int __flags, const struct _itimer *__itime, struct _itimer *__oitime);
	def timer_settime(self):
		i = self.util.choice(self.timer_ids)
		flags = 0
		itime = itimer()
		oitimer = itimer()
		ret = self.libc.TimerSettime(i,byref(itime),byref(oitimer))
		if (ret != -1):
			print("TimerSettime ok", ret)
		else:
			print("TimerSettime failed") 			

	# extern int TimerInfo(pid_t __pid, timer_t __id, int __flags, struct _timer_info *__info);
	def timer_info(self):
		pid = self.util.choice(self.pids)
		i = self.util.choice(self.timer_ids)
		flags = 0
		info = timerinfo()
		ret = self.libc.TimerInfo(pid,i,flags,byref(info))
		if (ret != -1):
			print("TimerInfo ok", ret)
		else:
			print("TimerInfo failed") 		

    # extern int TimerAlarm(clockid_t __id, const struct _itimer *__itime, struct _itimer *__otime);
	def timer_alarm(self):
		i = self.util.choice(self.timer_ids)
		flags = 0
		itime = itimer()
		oitimer = itimer()
		ret = self.libc.TimerAlarm(i,byref(itime),byref(oitimer))
		if (ret != -1):
			print("TimerAlarm ok", ret)
		else:
			print("TimerAlarm failed") 

	# extern int TimerTimeout(clockid_t __id, int __flags, const struct sigevent *__notify, const _Uint64t *__ntime,_Uint64t *__otime);
	def timer_timeout(self):
		i = self.util.choice(self.timer_ids)
		flags = 0
		notify = sigevent()
		__ntime = c_ulong()
		__otime = c_ulong()
		ret = self.libc.TimerTimeout(i,flags,byref(notify),byref(__ntime),byref(__otime))
		if (ret != -1):
			print("TimerTimeout ok", ret)
		else:
			print("TimerTimeout failed") 		


	############################ Sync Methods ##################################

	# extern int SyncTypeCreate(unsigned __type, sync_t *__sync, const struct _sync_attr *__attr);
	def sync_type_create(self):
		t = self.util.R(4)
		sync = nto_job_t()
		sync.count = self.util.R(0xffffffff)
		sync.__owner = 0

		if self.util.chance(2):
			sync = self.sync

		attr = _sync_attr()
		if self.util.chance(2):
			attr.protocol = self.util.R(0xffffffff)
			attr.flags = self.util.R(0xffffffff)
			attr.protocol = self.util.R(0xffffffff)
			attr.__prioceiling = self.util.R(0xffffffff)
			attr.__clockid = self.util.choice(self.clock_ids)

		self.log_remote("SyncTypeCreate")
		ret = self.libc.SyncTypeCreate(t,byref(sync),byref(attr))
		if (ret != -1):
			print("SyncTypeCreate ok", ret)
		else:
			print("SyncTypeCreate failed") 	
		 		

	# extern int SyncDestroy(sync_t *__sync);
	def sync_destroy(self):
		self.log_remote("SyncDestroy")
		ret = self.libc.SyncDestroy(byref(self.sync))
		if (ret != -1):
			print("SyncDestroy ok", ret)
		else:
			print("SyncDestroy failed") 
		 			

	# extern int SyncCtl(int __cmd, sync_t *__sync, void *__data);
	def sync_ctl(self):
		cmd = self.util.R(0xffffffff)
		sync = nto_job_t()

		if self.util.chance(2):
			sync = self.sync

		data = create_string_buffer(256)
		self.log_remote("SyncCtl") 
		ret = self.libc.SyncCtl(cmd,byref(sync),data)
		if (ret != -1):
			print("SyncCtl ok", ret)
		else:
			print("SyncCtl failed") 	
			

	# extern int SyncMutexEvent(sync_t *__sync, struct sigevent *event);
	def sync_mutex_event(self):
		sync = nto_job_t()

		if self.util.chance(2):
			sync = self.sync

		event = sigevent()
		self.log_remote("SyncMutexEvent")
		ret = self.libc.SyncMutexEvent(byref(sync),byref(event))
		if (ret != -1):
			print("SyncMutexEvent ok", ret)
		else:
			print("SyncMutexEvent failed") 	
		 	

	# extern int SyncMutexLock(sync_t *__sync);
	def sync_mutex_lock(self):
		sync = nto_job_t()

		if self.util.chance(2):
			sync = self.sync

		self.log_remote("SyncMutexLock") 
		ret = self.libc.SyncMutexLock(byref(sync))
		if (ret != -1):
			print("SyncMutexLock ok", ret)
		else:
			print("SyncMutexLock failed")
				

	# extern int SyncMutexUnlock(sync_t *__sync);			
	def sync_mutex_unlock(self):
		sync = nto_job_t()

		if self.util.chance(2):
			sync = self.sync

		self.log_remote("SyncMutexUnlock")
		ret = self.libc.SyncMutexUnlock(byref(sync))
		if (ret != -1):
			print("SyncMutexUnlock ok", ret)
		else:
			print("SyncMutexUnlock failed")
		

	# extern int SyncMutexRevive(sync_t *__sync);
	def sync_mutex_revive(self):
		sync = nto_job_t()

		if self.util.chance(2):
			sync = self.sync

		self.log_remote("SyncMutexRevive")
		ret = self.libc.SyncMutexRevive(byref(sync))
		if (ret != -1):
			print("SyncMutexRevive ok", ret)
		else:
			print("SyncMutexRevive failed")	
				

	# extern int SyncCondvarWait(sync_t *__sync, sync_t *__mutex);

	def sync_condvar_wait(self):
		sync = nto_job_t()

		if self.util.chance(2):
			sync = self.sync

		__mutex = nto_job_t()
		self.log_remote("SyncCondvarWait")
		ret = self.libc.SyncCondvarWait(byref(sync),byref(__mutex))
		if (ret != -1):
			print("SyncCondvarWait ok", ret)
		else:
			print("SyncCondvarWait failed")	
				

	# extern int SyncCondvarSignal(sync_t *__sync, int __all);
	def sync_condvar_signal(self):
		sync = nto_job_t()

		if self.util.chance(2):
			sync = self.sync

		self.log_remote("SyncCondvarSignal")
		__all = 0
		ret = self.libc.SyncCondvarSignal(byref(sync),__all)
		if (ret != -1):
			print("SyncCondvarSignal ok", ret)
		else:
			print("SyncCondvarSignal failed")	
			

	# extern int SyncSemPost(sync_t *__sync);
	def sync_sem_post(self):
		sync = nto_job_t()

		if self.util.chance(2):
			sync = self.sync

		self.log_remote("SyncSemPost")
		ret = self.libc.SyncSemPost(byref(sync))
		if (ret != -1):
			print("SyncSemPost ok", ret)
		else:
			print("SyncSemPost failed")
				

	# extern int SyncSemWait(sync_t *__sync, int __tryto);
	def sync_sem_wait(self):
		sync = nto_job_t()

		if self.util.chance(2):
			sync = self.sync

		__tryto = 0
		self.log_remote("SyncSemWait")
		ret = self.libc.SyncSemWait(byref(sync),__tryto)
		if (ret != -1):
			print("SyncSemWait ok", ret)
		else:
			print("SyncSemWait failed")	
			


	############################ Clock Methods ##################################

	# extern int ClockTime(clockid_t __id, const _Uint64t *_new, _Uint64t *__old);
	def clock_time(self):
		i = 0
		_new = c_uint64()
		_old = c_uint64()
		self.log_remote("ClockTime")
		ret = self.libc.ClockTime(i,byref(_new),byref(_old))
		if (ret != -1):
			print("ClockTime ok", ret)
		else:
			print("ClockTime failed")	
				

	def clock_adjust(self):
		# ClockAdjust(clockid_t __id, const struct _clockadjust *_new, struct _clockadjust *__old);
		__id = 0
		_new = clockadjust()
		_old = clockadjust()
		self.log_remote("ClockAdjust")
		ret = self.libc.ClockAdjust(__id,byref(_new),byref(_old))
		if (ret != -1):
			print("ClockAdjust ok", ret)
		else:
			print("ClockAdjust failed")	
				

	# extern int ClockPeriod(clockid_t __id, const struct _clockperiod *_new, struct _clockperiod *__old, int __reserved);
	def clock_period(self):
		__id = 0
		_new = clockadjust()
		_old = clockadjust()
		self.log_remote("ClockPeriod")
		ret = self.libc.ClockPeriod(__id,byref(_new),byref(_old))
		if (ret != -1):
			print("ClockPeriod ok", ret)
		else:
			print("ClockPeriod failed")
								

	# extern int ClockId(pid_t __pid, int __tid);
	def clock_id(self):
		self.log_remote("ClockId")
		pid = self.util.choice(self.pids)
		tid = 0
		ret = self.libc.ClockId(pid,tid)
		if (ret != -1):
			print("ClockId ok", ret)
		else:
			print("ClockId failed")
						

	# QNET kernel stuff #########################################################

	#extern int NetCred(int __coid, const struct _client_info *__info);
	def net_cred(self):
		self.log_remote("NetCred")	
		coid = self.util.choice(self.channel_ids)
		ci = _client_info()
		ret = self.libc.NetCred(coid,byref(ci))
		if (ret != -1):
			print("NetCred ok", ret)
		else:
			print("NetCred failed") 
			

	#extern int NetVtid(int __vtid, const struct _vtid_info *__info);
	def net_vtid(self):
		self.log_remote("NetVtid")
		__vtid = self.util.choice(self.channel_ids)
		__info = _vtid_info()
		ret = self.libc.NetVtid(__vtid,byref(__info))
		if (ret != -1):
			print("NetVtid ok", ret)
		else:
			print("NetVtid failed") 
					

	# extern int NetUnblock(int __vtid);
	def net_unblock(self):
		self.log_remote("NetUnblock")
		vtid = 0
		ret = self.libc.NetUnblock(vtid)
		if (ret != -1):
			print("NetUnblock ok", ret)
		else:
			print("NetUnblock failed") 	
			

	# extern int NetInfoscoid(int __local_scoid, int __remote_scoid);
	def net_info_scoid(self):
		self.log_remote("NetInfoscoid")
		scoid = self.util.choice(self.channel_ids)
		__remote_scoid = self.util.choice(self.channel_ids)
		ret = self.libc.NetInfoscoid(scoid,__remote_scoid)
		if (ret != -1):
			print("NetInfoscoid ok", ret)
		else:
			print("NetInfoscoid failed")
				

	# extern int NetSignalKill(void *sigdata, struct _cred_info *cred);
	def net_signal_skill(self):
		self.log_remote("NetSignalKill")	
		sigdata = create_string_buffer(256)
		cred = _cred_info()
		ret = self.libc.NetSignalKill(sigdata,byref(cred))
		if (ret != -1):
			print("NetSignalKill ok", ret)
		else:
			print("NetSignalKill failed") 			
		
	def trace_event(self):
		self.log_remote("TraceEvent")
		code = self.util.R(0xffffffff)
		c1 = self.util.R(0xffffffff)
		c2 = self.util.R(0xffffffff)
		c3 = self.util.R(0xffffffff)
		c4 = self.util.R(0xffffffff)
		c5 = self.util.R(0xffffffff)
		c6 = self.util.R(0xffffffff)
		ret = self.libc.TraceEvent(code,c1,c2,c3,c4,c5,c6)
		if (ret != -1):
			print("TraceEvent ok", ret)
		else:
			print("TraceEvent failed") 	
				

	def cpu_page_get(self):
		self.log_remote("__SysCpupageGet")
		ret = self.libc.__SysCpupageGet(self.util.R(0xffffffff))
		if (ret != -1):
			print("__SysCpupageGet ok", ret)
		else:
			print("__SysCpupageGet failed") 	
			

	def cpu_page_set(self):
		self.log_remote("__SysCpupageSet")
		ret = self.libc.__SysCpupageSet(self.util.R(0xffffffff),self.util.R(0xffffffff))
		if (ret != -1):
			print("__SysCpupageSet ok", ret)
		else:
			print("__SysCpupageSet failed")
		

 	#extern int PowerParameter(unsigned __id, unsigned __struct_len, const struct nto_power_parameter *__new,
	#struct nto_power_parameter *__old);	
	def power_param(self):
		i = self.util.R(6)
		__new = nto_power_parameter()
		__old = nto_power_parameter()
		if self.util.chance(2):
			l = self.util.R(0xffffffff)
		elif self.util.chance(2):
			l = 0x28
		else:
			l = 0x24

		log_str = "PowerParameter"
		self.log_remote(log_str)
		ret = self.libc.PowerParameter(i,l,byref(__new),byref(__old))
		if (ret != -1):
			print("PowerParameter ok", ret)
		else:
			print("PowerParameter failed")

	def power_active(self):
		i = self.util.R(0xffffffff)
		self.log_remote("PowerSetActive(" + str(i) + ");")

		ret = self.libc.PowerSetActive(i)
		if (ret != -1):
			print("PowerSetActive ok", ret)
		else:
			print("PowerSetActive failed")
		

	def log_remote(self,data):
		buf = create_string_buffer(bytes(data, encoding='utf-8'),50)
		self.sock.sendall(buf)
		ack = self.sock.recv(3)
		print(ack)
		

if __name__ == "__main__":
	
	util = Util()

	do_channels = True
	do_msging = False

	do_threads = True
	do_signals = False 

	do_interupts = True

	do_scheduling = True # causes malloc fails

	do_qnet = True

	do_timer = False
	do_clock = True
	do_sync = True

	do_cpupage = False
	do_tracelogging = True

	do_power = True

	syscalls = []

	if do_channels:
		syscalls.append("channel_create")
		syscalls.append("channel_create_r")
		syscalls.append("channel_create_ext")
		syscalls.append("channel_destory")
		syscalls.append("connect_attach")
		syscalls.append("connect_attach_ext")
		syscalls.append("connect_server_info")
		syscalls.append("connect_client_info")
		syscalls.append("connect_flags")
		syscalls.append("channel_conn_attr")
		syscalls.append("connect_client_info_able")
		syscalls.append("connect_client_info_ext")
		syscalls.append("client_info_ext_free")
	
	if do_msging:
		syscalls.append("msg_send")
		syscalls.append("msg_send_pulse")
		syscalls.append("msg_receive")
		syscalls.append("msg_receive_pulse")
		syscalls.append("msg_key_data")
		syscalls.append("msg_send_async_gbl")
		syscalls.append("msg_send_async")
		syscalls.append("msg_receive_async_gbl")
		syscalls.append("msg_pause")

	if do_threads:
		syscalls.append("thread_create")
		syscalls.append("thread_ctl")
		syscalls.append("thread_ctl_ext")

	if do_signals:
		syscalls.append("signal_kill")
		syscalls.append("signal_return")
		syscalls.append("signal_fault")
		syscalls.append("signal_action")
		syscalls.append("signal_return")
   
    # All require root permissions
	if do_interupts:
		syscalls.append("interupt_hook_trace")
		syscalls.append("interupt_hook_idle")
		syscalls.append("interupt_hook_idle2")
		syscalls.append("interupt_hook_overdrive_event")
		syscalls.append("interupt_attach_event")

	if do_scheduling:
		#syscalls.append("scheduler_info")
		syscalls.append("scheduler_get")
		syscalls.append("scheduler_set")
		syscalls.append("scheduler_yield")
		syscalls.append("scheduler_yield")
		syscalls.append("scheduler_job_create")
		syscalls.append("scheduler_job_destroy")
		syscalls.append("scheduler_waypoint")
		syscalls.append("scheduler_waypoint2")

	if do_qnet:
		syscalls.append("net_cred")
		syscalls.append("net_vtid")
		syscalls.append("net_unblock")
		syscalls.append("net_info_scoid")
		syscalls.append("net_signal_skill")

	if do_timer:
		syscalls.append("timer_create")
		syscalls.append("timer_settime")
		syscalls.append("timer_alarm")
		syscalls.append("timer_timeout")
		syscalls.append("timer_info")
		syscalls.append("timer_destroy")

	if do_sync:
		syscalls.append("sync_type_create")
		syscalls.append("sync_destroy")
		syscalls.append("sync_ctl")
		syscalls.append("sync_mutex_event")
		#syscalls.append("sync_mutex_lock")
		syscalls.append("sync_mutex_unlock")
		syscalls.append("sync_mutex_revive")
		#syscalls.append("sync_condvar_wait")
		syscalls.append("sync_condvar_signal")
		syscalls.append("sync_sem_post")
		#syscalls.append("sync_sem_wait")

	if do_clock:
		syscalls.append("clock_id")
		syscalls.append("clock_adjust")
		syscalls.append("clock_period")

	if do_tracelogging:
		syscalls.append("trace_event")

	if do_cpupage:
		syscalls.append("cpu_page_get")
		syscalls.append("cpu_page_set")

	if do_power:
		syscalls.append("power_param")
		syscalls.append("power_active")

	print(syscalls)

	syscall = Syscall(syscalls)

	# Fuzz loop
	while True:
		call = util.choice(syscalls)
		print(call) 
		# Make the call
		method = getattr(syscall,call)
		method()
