"""Own one Windows subprocess tree without changing machine policy.

Start suspended, assign to a private kill-on-close Job Object, then resume the
initial thread. Descendants cannot race ahead of assignment or outlive cleanup.
Only imported on Windows; no third-party package or process-name matching.
"""
import ctypes
from ctypes import wintypes as w
import time


class BasicLimits(ctypes.Structure):
    _fields_ = [('ProcessTime', ctypes.c_longlong), ('JobTime', ctypes.c_longlong),
                ('LimitFlags', w.DWORD), ('MinWorkingSet', ctypes.c_size_t),
                ('MaxWorkingSet', ctypes.c_size_t), ('ActiveProcessLimit', w.DWORD),
                ('Affinity', ctypes.c_size_t), ('PriorityClass', w.DWORD), ('SchedulingClass', w.DWORD)]


class IOCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_ulonglong) for name in
                ('ReadOps', 'WriteOps', 'OtherOps', 'ReadBytes', 'WriteBytes', 'OtherBytes')]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [('Basic', BasicLimits), ('IO', IOCounters),
                ('ProcessMemory', ctypes.c_size_t), ('JobMemory', ctypes.c_size_t),
                ('PeakProcessMemory', ctypes.c_size_t), ('PeakJobMemory', ctypes.c_size_t)]


class Accounting(ctypes.Structure):
    _fields_ = [(name, ctypes.c_longlong) for name in ('UserTime', 'KernelTime', 'PeriodUserTime', 'PeriodKernelTime')] + [
        ('PageFaults', w.DWORD), ('TotalProcesses', w.DWORD), ('ActiveProcesses', w.DWORD), ('TerminatedProcesses', w.DWORD)]


class ThreadEntry(ctypes.Structure):
    _fields_ = [('dwSize', w.DWORD), ('cntUsage', w.DWORD), ('thread_id', w.DWORD),
                ('owner_pid', w.DWORD), ('base_priority', w.LONG), ('delta_priority', w.LONG), ('flags', w.DWORD)]


class WindowsJob:
    creationflags = 0x00000004  # CREATE_SUSPENDED

    def __init__(self):
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'CreateJobObjectW': ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            'SetInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            'AssignProcessToJobObject': ([w.HANDLE, w.HANDLE], w.BOOL),
            'TerminateJobObject': ([w.HANDLE, w.UINT], w.BOOL),
            'QueryInformationJobObject': ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            'CloseHandle': ([w.HANDLE], w.BOOL),
            'CreateToolhelp32Snapshot': ([w.DWORD, w.DWORD], w.HANDLE),
            'Thread32First': ([w.HANDLE, ctypes.POINTER(ThreadEntry)], w.BOOL),
            'Thread32Next': ([w.HANDLE, ctypes.POINTER(ThreadEntry)], w.BOOL),
            'OpenThread': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            'ResumeThread': ([w.HANDLE], w.DWORD),
            'OpenProcess': ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            'WaitForSingleObject': ([w.HANDLE, w.DWORD], w.DWORD),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.api, name); fn.argtypes = args; fn.restype = result
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits(); limits.Basic.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error()); self.close(); raise error

    def attach_and_resume(self, process):
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise ctypes.WinError(ctypes.get_last_error())
        snapshot = self.api.CreateToolhelp32Snapshot(4, 0)  # TH32CS_SNAPTHREAD
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            entry = ThreadEntry(); entry.dwSize = ctypes.sizeof(entry)
            found = self.api.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.owner_pid == process.pid:
                    thread = self.api.OpenThread(2, False, entry.thread_id)
                    if not thread:
                        raise ctypes.WinError(ctypes.get_last_error())
                    try:
                        previous = self.api.ResumeThread(thread)
                        if previous != 1:
                            raise OSError('Initial subprocess thread was not suspended exactly once')
                        return
                    finally:
                        self.api.CloseHandle(thread)
                found = self.api.Thread32Next(snapshot, ctypes.byref(entry))
            raise OSError('Initial subprocess thread not found')
        finally:
            self.api.CloseHandle(snapshot)

    def terminate_and_wait(self, timeout=5):
        if not self.handle:
            return
        deadline = time.monotonic() + timeout
        # ActiveProcesses can reach zero before Windows finishes closing the
        # inherited file handles. Wait on process objects as well as accounting.
        class Pids(ctypes.Structure):
            _fields_ = [('assigned', w.DWORD), ('count', w.DWORD), ('ids', ctypes.c_size_t * 4096)]
        pids = Pids()
        if not self.api.QueryInformationJobObject(self.handle, 3, ctypes.byref(pids), ctypes.sizeof(pids), None):
            raise ctypes.WinError(ctypes.get_last_error())
        handles = []
        try:
            for pid in list(pids.ids)[:pids.count]:
                handle = self.api.OpenProcess(0x100000, False, pid)  # SYNCHRONIZE
                if handle:
                    handles.append(handle)
            if not self.api.TerminateJobObject(self.handle, 1):
                raise ctypes.WinError(ctypes.get_last_error())
            for handle in handles:
                remaining = max(0, int((deadline - time.monotonic()) * 1000))
                if self.api.WaitForSingleObject(handle, remaining) != 0:
                    raise TimeoutError('Owned Windows subprocess did not finish closing handles')
        finally:
            for handle in handles:
                self.api.CloseHandle(handle)
        while True:
            info = Accounting()
            if not self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(info), ctypes.sizeof(info), None):
                raise ctypes.WinError(ctypes.get_last_error())
            if not info.ActiveProcesses:
                return
            if time.monotonic() >= deadline:
                raise TimeoutError('Owned Windows subprocess tree did not terminate')
            time.sleep(.02)

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle); self.handle = None
