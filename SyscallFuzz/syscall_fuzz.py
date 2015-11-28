
""" QNX syscall fuzzer
<alex.plaskett@mwrinfosecurity.com> - 2013
BB10 Libc exports
TODO: Remove the libc wrapper and just fuzz directly? 
Add support for COID's outside of the process
"""

from ctypes import *
from util import *

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

CHAN_FLAGS = [0x0001,0x0002,0x0004,0x0008,0x0010,0x0020,0x0040,0x0080,0x0100,0x0200,0x0400,0x0800]


# Conn flags
#define _NTO_COF_CLOEXEC		0x0001
#define _NTO_COF_DEAD			0x0002
#define _NTO_COF_NOSHARE		0x0040
#define _NTO_COF_NETCON			0x0080
#define _NTO_COF_NONBLOCK		0x0100
#define _NTO_COF_ASYNC			0x0200
#define _NTO_COF_GLOBAL			0x0400

CONN_FLAGS = [0x0001,0x0002,0x0040,0x0080,0x0100,0x0200,0x0400]




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

class Syscall:

	def __init__(self):
		self.libc = CDLL("libc.so")
		self.channel_ids = []
		self.pids = [0]
		self.util = Util()
		self.scoids = []

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
	

	def channel_create(self):
		flags = self.util.choice(CHAN_FLAGS) # Should OR flags together
		ret = self.libc.ChannelCreate(flags)
		if (ret != -1):
			print("ChannelCreate coid = ", ret)
			self.channel_ids.append(ret)
		else:
			print("ChannelCreate failed")

	# Whats the _r methods for?
	def channel_create_r(self):
		flags = self.util.choice(CHAN_FLAGS)
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
		mode = 0 				# access permissions
		bufsize = self.util.R(0xffffffff)				
		maxnumbuf = self.util.R(0xffffffff)
		# TODO: Sort out structs
		# sigevent *
		# cred_info *
		print("Bufsize = ",bufsize)
		print("Maxnumbuf = ",maxnumbuf)
		ret = self.libc.ChannelCreateExt(flags,mode,bufsize,maxnumbuf,0,0)
		if (ret != -1):
			print("ChannelCreateExt coid = ", ret)
			self.channel_ids.append(ret)
		else:
			print("ChannelCreateExt failed")

	def channel_destory(self):
		chid = self.util.choice(self.channel_ids)
		ret = self.libc.ChannelDestroy(chid)
		if (ret != 1):
			print("ChannelDestroy worked")

	def channel_destroy_r(self):
		chid = self.util.choice(self.channel_ids)
		ret = self.libc.ChannelDestroy_r(chid)
		if (ret != 1):
			print("ChannelDestroy_r worked")

	def connect_attach(self):
		nd = 0
		pid = self.util.choice(self.pids)
		chid = self.util.choice(self.channel_ids)
		index = 0
		flags = self.util.choice(CONN_FLAGS)
		ret = self.libc.ConnectAttach(nd,pid,chid,index,flags)
		if (ret != -1):
			print("ConnectAttach = ", ret)
		else:
			print("ConnectAttach failed")

	def connect_attach_r(self):
		nd = 0
		pid = self.util.choice(self.pids)
		chid = self.util.choice(self.channel_ids)
		index = 0
		flags = self.util.choice(CONN_FLAGS)
		ret = self.libc.ConnectAttach_r(nd,pid,chid,index,flags)
		if (ret != -1):
			print("ConnectAttach = ", ret)
		else:
			print("ConnectAttach failed")

	# The struct passed to this method is really complicated and new code
	# async method handling.
	# This is undocumented
	# extern int ConnectAttachExt(_Uint32t __nd, pid_t __pid, int __chid, unsigned __index, int __flags, struct _asyncmsg_connection_descriptor *__cd);
	def connect_attach_ext(self):
		nd = 0
		pid = self.util.choice(self.pids)
		chid = self.util.choice(self.channel_ids)
		index = 0
		flags = self.util.choice(CONN_FLAGS)	
		
		# TODO: Fix the variables in this struct
		cd = _asyncmsg_connection_descriptor()

		ret = self.libc.ConnectAttach_r(nd,pid,chid,index,flags,cd)
		if (ret != -1):
			print("ConnectAttachExt = ", ret)
		else:
			print("ConnectAttachExt failed")	

	def connect_detach(self):
		coid = self.util.choice(self.channel_ids)
		ret = self.libc.ConnectDetach(coid)
		if (ret != -1):
			print("ConnectDetach ok = ", ret)
		else:
			print("ConnectDetach failed")	

	def connect_detach_r(self):
		coid = self.util.choice(self.channel_ids)
		ret = self.libc.ConnectDetach_r(coid)
		if (ret != -1):
			print("ConnectDetach_r ok = ", ret)
		else:
			print("ConnectDetach_r failed")	


	def connect_server_info(self):
		##extern int ConnectServerInfo(pid_t __pid, int __coid, struct _server_info *__info);
		pid = self.util.choice(self.pids)
		coid = self.util.choice(self.channel_ids)
		info = _msg_info()
		ret = self.libc.ConnectServerInfo(pid,coid,byref(info))
		if (ret != -1):
			print("ConnectServerInfo ok = ", ret)
			print("scoid = ", info.scoid)
			self.scoids.append(info.scoid)
		else:
			print("ConnectServerInfo failed")	

	def connect_server_info_r(self):
		##extern int ConnectServerInfo(pid_t __pid, int __coid, struct _server_info *__info);
		pid = self.util.choice(self.pids)
		coid = self.util.choice(self.channel_ids)
		info = _msg_info()
		ret = self.libc.ConnectServerInfo_r(pid,coid,byref(info))
		if (ret != -1):
			print("ConnectServerInfo_r ok = ", ret)
			print("scoid = ", info.scoid)
			self.scoids.append(info.scoid)
		else:
			print("ConnectServerInfo_r failed")	

	# ngroups could potentially overflow here.. fixed size in the struct passed.
	# These functions are currently broken
	def connect_client_info(self):
		#extern int ConnectClientInfo(int __scoid, struct _client_info *__info, int __ngroups);
		scoid = self.util.choice(self.scoids)
		info = _client_info()
		ngroups = self.util.R(0xffffffff)
		ret = self.libc.ConnectClientInfo(scoid,byref(info),ngroups)
		if (ret != -1):
			print("ConnectClientInfo ok = ", ret)
		else:
			print("ConnectClientInfo failed")	

	# ngroups could potentially overflow here.. fixed size in the struct passed.
	def connect_client_info_r(self):
		#extern int ConnectClientInfo(int __scoid, struct _client_info *__info, int __ngroups);
		scoid = self.util.choice(self.scoids)
		info = _client_info()
		ngroups = self.util.R(0xffffffff)
		ret = self.libc.ConnectClientInfo_r(scoid,byref(info),ngroups)
		if (ret != -1):
			print("ConnectClientInfo_r ok = ", ret)
		else:
			print("ConnectClientInfo_r failed")	

	def connect_flags(self):
		#extern int ConnectFlags(pid_t __pid, int __coid, unsigned __mask, unsigned __bits);
		pid = self.util.choice(self.pids)
		coid = self.util.choice(self.channel_ids)
		# TODO: Fix mask / bits here
		mask = 0
		bits = 0
		ret = self.libc.ConnectFlags(pid,coid,mask,bits)
		if (ret != -1):
			print("ConnectFlags ok = ", ret)
		else:
			print("ConnectFlags failed")	


	def connect_flags_r(self):
		#extern int ConnectFlags(pid_t __pid, int __coid, unsigned __mask, unsigned __bits);
		pid = self.util.choice(self.pids)
		coid = self.util.choice(self.channel_ids)
		# TODO: Fix mask / bits here
		mask = 0
		bits = 0
		ret = self.libc.ConnectFlags_r(pid,coid,mask,bits)
		if (ret != -1):
			print("ConnectFlags_r ok = ", ret)
		else:
			print("ConnectFlags_r failed")	

	# This is interesting, conn_attr is complicated struct.
	# Undocumented function
	def channel_conn_attr(self):
		# #extern int ChannelConnectAttr(unsigned __id, union _channel_connect_attr *__old_attr, union _channel_connect_attr *__new_attr, unsigned __flags);
		__id = self.util.choice(self.channel_ids)

		# TODO: Fill in structs here
		__old_attr = _channel_connect_attr()
		__new_attr = _channel_connect_attr()
		flags = self.util.choice(CHAN_CONNECT_FLAGS)
		ret = self.libc.ChannelConnectAttr(__id,__old_attr,__new_attr,flags)
		if (ret != -1):
			print("ChannelConnectAttr ok = ", ret)
		else:
			print("ChannelConnectAttr failed")	

	################################ Messaging Methods ###############################

	def msg_send(self):
		# extern int MsgSend(int __coid, const void *__smsg, int __sbytes, void *__rmsg, int __rbytes);
		send_buf = create_string_buffer(10)
		recv_buf = create_string_buffer(10)
		coid = self.util.choice(self.channel_ids)
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
		send_buf = create_string_buffer(10)
		recv_buf = create_string_buffer(10)
		coid = self.util.choice(self.channel_ids)
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
		send_buf = create_string_buffer(10)
		recv_buf = create_string_buffer(10)
		coid = self.util.choice(self.channel_ids)
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
		send_buf = create_string_buffer(10)
		recv_buf = create_string_buffer(10)
		coid = self.util.choice(self.channel_ids)
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
		coid = self.util.choice(self.channel_ids)
		send_buf = create_string_buffer(10)
		sbytes = len(send_buf)
		iov = iovec()
		rparts = 0
		ret = self.libc.MsgSendsv(coid,send_buf,sbytes,byref(iov),rparts)
		if (ret != -1):
			print("MsgSendsv ok = ", ret)
		else:
			print("MsgSendsv failed")	


	def msg_send_sv_r(self):
		coid = self.util.choice(self.channel_ids)
		send_buf = create_string_buffer(10)
		sbytes = len(send_buf)
		iov = iovec()
		rparts = 0
		ret = self.libc.MsgSendsv(coid,send_buf,sbytes,byref(iov),rparts)
		if (ret != -1):
			print("MsgSendsv_r ok = ", ret)
		else:
			print("MsgSendsv_r failed")	

	# extern int MsgSendsvnc(int __coid, const void *__smsg, int __sbytes, const struct iovec *__riov, int __rparts);
	def msg_send_svnc(self):
		coid = self.util.choice(self.channel_ids)
		send_buf = create_string_buffer(10)
		sbytes = len(send_buf)
		iov = iovec()
		rparts = 0
		ret = self.libc.MsgSendsvnc(coid,send_buf,sbytes,byref(iov),rparts)
		if (ret != -1):
			print("MsgSendsvnc ok = ", ret)
		else:
			print("MsgSendsvnc failed")	

	def msg_send_svnc_r(self):
		coid = self.util.choice(self.channel_ids)
		send_buf = create_string_buffer(10)
		sbytes = len(send_buf)
		iov = iovec()
		rparts = 0
		ret = self.libc.MsgSendsvnc_r(coid,send_buf,sbytes,byref(iov),rparts)
		if (ret != -1):
			print("MsgSendsvnc_r ok = ", ret)
		else:
			print("MsgSendsvnc_r failed")	

	# extern int MsgSendv(int __coid, const struct iovec *__siov, int __sparts, const struct iovec *__riov, int __rparts);
	# extern int MsgSendv_r(int __coid, const struct iovec *__siov, int __sparts, const struct iovec *__riov, int __rparts);
	def msg_send_v(self):
		coid = self.util.choice(self.channel_ids)
		siov = iovec()
		sparts = 0
		riov = iovec()
		rparts = 0
		ret = self.libc.MsgSendv(coid,byref(siov),sparts,byref(riov),rparts)
		if (ret != -1):
			print("MsgSendv ok = ", ret)
		else:
			print("MsgSendv failed")	

	def msg_send_v_r(self):
		coid = self.util.choice(self.channel_ids)
		siov = iovec()
		sparts = 0
		riov = iovec()
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
		bytes = 0
		__info = _msg_info()
		ret = self.libc.MsgReceive(chid,__msg,bytes,byref(__info))
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
		__coid = self.util.choice(self.channel_ids)
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
		__newkey = c_ulong()
		__iov = iovec()
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
		__newkey = c_ulong()
		__iov = iovec()
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
		__coid = self.util.choice(self.channel_ids)
		__smsg = create_string_buffer(256)
		sbytes = len(__smsg)
		__msg_prio = 0
		ret = self.libc.MsgSendAsyncGbl(__coid,__smsg,sbytes,__msg_prio)
		if (ret != -1):
			print("MsgSendAsyncGbl ok", ret)
		else:
			print("MsgSendAsyncGbl failed")


	# extern int MsgSendAsync(int __coid);
	def msg_send_async(self):
		__coid = self.util.choice(self.channel_ids)
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
	def signal_return(self):
		__info = _sighandler_info()
		ret = self.libc.SignalReturn(__info)
		if (ret != -1):
			print("SignalReturn ok", ret)
		else:
			print("SignalReturn failed")		

    #extern int SignalFault(unsigned __sigcode, void *__regs, _Uintptrt __refaddr);
    # This is undocumented
	def signal_fault(self):
		signo = self.util.R(64)
		regs = c_ulong() # RD_VERIFY_PTR(act, kap->regs, sizeof(CPU_REGISTERS));
		refaddr = c_ulong()
		ret = self.libc.SignalFault(signo,byref(regs),byref(refaddr))
		if (ret != -1):
			print("SignalFault ok", ret)
		else:
			print("SignalFault failed")		

    # extern int SignalAction(pid_t __pid, void (*__sigstub)(void), int __signo, const struct sigaction *__act, struct sigaction *__oact);
	def signal_action(self):
		pid = self.util.choice(self.pids)
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

	############################ Clock Methods ##################################
	# TODO
	def clock_adjust(self):
		# ClockAdjust(clockid_t __id, const struct _clockadjust *_new, struct _clockadjust *__old);
		__id = c_ulong()

	# QNET kernel stuff #########################################################
	def net_cred(self):
		#extern int NetCred(int __coid, const struct _client_info *__info);
		coid = 0
		ci = _client_info()

	def net_vtid(self):
		__vtid = 0
		__info = _vtid_info()
		#extern int NetVtid(int __vtid, const struct _vtid_info *__info);

	def net_unblock(self):
		# extern int NetUnblock(int __vtid);
		vtid = 0

	def net_info_scoid(self):
		# __remote_scoid - Can't find this defined anywhere.
		# extern int NetInfoscoid(int __local_scoid, int __remote_scoid);
		pass

	

if __name__ == "__main__":
	syscall = Syscall()
	syscall.channel_create()
	syscall.channel_create_r()
	syscall.channel_create_ext()
	syscall.channel_destory()
	syscall.connect_attach()
	syscall.connect_attach_ext()
	syscall.connect_server_info()
	syscall.connect_client_info()
	syscall.connect_flags()
	syscall.channel_conn_attr()
	syscall.msg_send()
	syscall.msg_send_pulse()
	#syscall.msg_receive()
	#syscall.msg_receive_pulse()
	syscall.msg_key_data()
	syscall.msg_send_async_gbl()
	syscall.msg_send_async()
	#syscall.msg_receive_async_gbl()
	syscall.msg_pause()
	#syscall.signal_kill()
	syscall.signal_return()
	syscall.signal_fault()
	syscall.signal_action()