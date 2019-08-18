# -*- coding: utf-8 -*-
#
#       ctypes_pulseaudio.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
#
#       This library is free software; you can redistribute it and/or
#       modify it under the terms of the GNU Lesser General Public
#       License as published by the Free Software Foundation; either
#       version 3 of the License, or (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

from ctypes import *
PA = CDLL('libpulse.so.0')

#
# Pulse Audio constants and defines
#
PA_CONTEXT_UNCONNECTED = 0
PA_CONTEXT_CONNECTING = 1
PA_CONTEXT_AUTHORIZING = 2
PA_CONTEXT_SETTING_NAME = 3
PA_CONTEXT_READY = 4
PA_CONTEXT_FAILED = 5
PA_CONTEXT_TERMINATED = 6

PA_OPERATION_RUNNING = 0
PA_OPERATION_DONE = 1
PA_OPERATION_CANCELLED = 2

# Convenience ...
STRING = c_char_p
size_t = c_ulong
uint32_t = c_uint32
uint8_t = c_uint8

class pa_mainloop_api(Structure):
    pass
class pa_threaded_mainloop(Structure):
    pass
pa_threaded_mainloop._fields_ = []
pa_threaded_mainloop_new = PA.pa_threaded_mainloop_new
pa_threaded_mainloop_new.restype = POINTER(pa_threaded_mainloop)
pa_threaded_mainloop_new.argtypes = []
pa_threaded_mainloop_free = PA.pa_threaded_mainloop_free
pa_threaded_mainloop_free.restype = None
pa_threaded_mainloop_free.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_start = PA.pa_threaded_mainloop_start
pa_threaded_mainloop_start.restype = c_int
pa_threaded_mainloop_start.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_stop = PA.pa_threaded_mainloop_stop
pa_threaded_mainloop_stop.restype = None
pa_threaded_mainloop_stop.argtypes = [POINTER(pa_threaded_mainloop)]
pa_threaded_mainloop_get_api = PA.pa_threaded_mainloop_get_api
pa_threaded_mainloop_get_api.restype = POINTER(pa_mainloop_api)
pa_threaded_mainloop_get_api.argtypes = [POINTER(pa_threaded_mainloop)]

class pa_context(Structure):
    pass
pa_context._fields_ = []
class pa_spawn_api(Structure):
    pass
class pa_stream(Structure):
    pass
pa_stream._fields_ = []

class pa_operation(Structure):
        pass

class pa_cvolume(Structure):
        pass
pa_volume_t = uint32_t
pa_cvolume._fields_ = [
    ('channels', uint8_t),
    ('values', pa_volume_t * 32),
]

pa_sample_format = c_int
pa_sample_format_t = pa_sample_format

class pa_sample_spec(Structure):
    pass
pa_sample_spec._fields_ = [
        ('format', pa_sample_format_t),
        ('rate', uint32_t),
        ('channels', uint8_t),
]

pa_channel_position = c_int
pa_channel_position_t = pa_channel_position

class pa_channel_map(Structure):
    pass
uint8_t = c_uint8
pa_channel_map._fields_ = [
    ('channels', uint8_t),
    ('map', pa_channel_position_t * 32),
]

class pa_source_info(Structure):
    pass
pa_source_info._fields_ = [
    ('name', STRING),
    ('index', uint32_t),
    ('description', STRING),
    ('sample_spec', pa_sample_spec),
    ('channel_map', pa_channel_map),
    ('owner_module', uint32_t),
    ('volume', pa_cvolume),
#    ('mute', c_int),
#    ('monitor_of_sink', uint32_t),
#    ('monitor_of_sink_name', STRING),
#    ('latency', pa_usec_t),
#    ('driver', STRING),
#    ('flags', pa_source_flags_t),
#    ('proplist', POINTER(pa_proplist)),
#    ('configured_latency', pa_usec_t),
#    ('base_volume', pa_volume_t),
#    ('state', pa_source_state_t),
#    ('n_volume_steps', uint32_t),
#    ('card', uint32_t),
#    ('n_ports', uint32_t),
#    ('ports', POINTER(POINTER(pa_source_port_info))),
#    ('active_port', POINTER(pa_source_port_info)),
#    ('n_formats', uint8_t),
#    ('formats', POINTER(POINTER(pa_format_info))),
]

pa_context_flags = c_int
pa_context_flags_t = pa_context_flags
pa_context_state = c_int
pa_context_state_t = pa_context_state
pa_context_notify_cb_t = CFUNCTYPE(None, POINTER(pa_context), c_void_p)
pa_context_success_cb_t = CFUNCTYPE(None, POINTER(pa_context), c_int, c_void_p)
pa_stream_success_cb_t = CFUNCTYPE(None, POINTER(pa_stream), c_int, c_void_p)
pa_stream_request_cb_t = CFUNCTYPE(None, POINTER(pa_stream), size_t, c_void_p)
pa_stream_notify_cb_t = CFUNCTYPE(None, POINTER(pa_stream), c_void_p)
pa_source_info_cb_t = CFUNCTYPE(None, POINTER(pa_context), POINTER(pa_source_info), c_int, c_void_p)

pa_context_new = PA.pa_context_new
pa_context_new.restype = POINTER(pa_context)
pa_context_new.argtypes = [POINTER(pa_mainloop_api), STRING]
pa_context_connect = PA.pa_context_connect
pa_context_connect.restype = c_int
pa_context_connect.argtypes = [POINTER(pa_context), STRING, pa_context_flags_t, POINTER(pa_spawn_api)]
pa_context_disconnect = PA.pa_context_disconnect
pa_context_disconnect.restype = None
pa_context_disconnect.argtypes = [POINTER(pa_context)]

pa_context_set_state_callback = PA.pa_context_set_state_callback
pa_context_set_state_callback.restype = None
pa_context_set_state_callback.argtypes = [POINTER(pa_context), pa_context_notify_cb_t, c_void_p]
pa_context_get_state = PA.pa_context_get_state
pa_context_get_state.restype = pa_context_state_t
pa_context_get_state.argtypes = [POINTER(pa_context)]
pa_stream_set_state_callback = PA.pa_stream_set_state_callback
pa_stream_set_state_callback.restype = None
pa_stream_set_state_callback.argtypes = [POINTER(pa_stream), pa_stream_notify_cb_t, c_void_p]

pa_context_get_source_info_list = PA.pa_context_get_source_info_list
pa_context_get_source_info_list.restype = POINTER(pa_operation)
pa_context_get_source_info_list.argtypes = [POINTER(pa_context), pa_source_info_cb_t, c_void_p]

pa_context_get_source_info_by_index = PA.pa_context_get_source_info_by_index
pa_context_get_source_info_by_index.restype = POINTER(pa_operation)
pa_context_get_source_info_by_index.argtypes = [POINTER(pa_context), uint32_t, pa_source_info_cb_t, c_void_p]

pa_context_set_source_volume_by_index = PA.pa_context_set_source_volume_by_index
pa_context_set_source_volume_by_index.restype = POINTER(pa_operation)
pa_context_set_source_volume_by_index.argtypes = [POINTER(pa_context), uint32_t, POINTER(pa_cvolume), pa_context_success_cb_t, c_void_p]

pa_context_set_source_mute_by_index = PA.pa_context_set_source_mute_by_index
pa_context_set_source_mute_by_index.restype = POINTER(pa_operation)
pa_context_set_source_mute_by_index.argtypes = [POINTER(pa_context), uint32_t, c_int, pa_context_success_cb_t, c_void_p]

pa_sw_volume_from_linear = PA.pa_sw_volume_from_linear
pa_sw_volume_from_linear.restype = pa_volume_t
pa_sw_volume_from_linear.argtypes = [c_double]
pa_sw_volume_to_linear = PA.pa_sw_volume_to_linear
pa_sw_volume_to_linear.restype = c_double
pa_sw_volume_to_linear.argtypes = [pa_volume_t]

pa_sw_volume_from_dB = PA.pa_sw_volume_from_dB
pa_sw_volume_from_dB.restype = pa_volume_t
pa_sw_volume_from_dB.argtypes = [c_double]
pa_sw_volume_to_dB = PA.pa_sw_volume_to_dB
pa_sw_volume_to_dB.restype = c_double
pa_sw_volume_to_dB.argtypes = [pa_volume_t]
