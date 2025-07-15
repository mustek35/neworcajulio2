import threading
import queue
import numpy as np

try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
except Exception as e:  # if gstreamer not installed
    raise


class GStreamerRTSPReader:
    """Lector RTSP utilizando GStreamer"""

    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.pipeline = None
        self.appsink = None
        self.bus = None
        self.running = False
        self.thread = None
        self.frame_queue = queue.Queue(maxsize=10)

    def start(self):
        if self.running:
            return True

        Gst.init(None)
        pipeline_desc = (
            f"rtspsrc location={self.rtsp_url} latency=200 ! "
            "decodebin ! videoconvert ! video/x-raw,format=BGR ! "
            "appsink name=sink max-buffers=1 drop=true"
        )
        try:
            self.pipeline = Gst.parse_launch(pipeline_desc)
            self.appsink = self.pipeline.get_by_name('sink')
            self.appsink.set_property('emit-signals', False)
            self.appsink.set_property('sync', False)
            self.bus = self.pipeline.get_bus()

            self.pipeline.set_state(Gst.State.PLAYING)
            self.running = True

            self.thread = threading.Thread(target=self._read_frames, daemon=True)
            self.thread.start()
            return True
        except Exception as e:
            print(f"❌ Error iniciando GStreamer pipeline: {e}")
            return False

    def _read_frames(self):
        while self.running:
            sample = self.appsink.emit('try-pull-sample', Gst.SECOND // 5)
            if sample:
                buf = sample.get_buffer()
                caps = sample.get_caps()
                struct = caps.get_structure(0)
                width = struct.get_value('width')
                height = struct.get_value('height')

                success, map_info = buf.map(Gst.MapFlags.READ)
                if not success:
                    continue
                try:
                    frame = np.frombuffer(map_info.data, np.uint8)
                    frame = frame.reshape((height, width, 3))
                    try:
                        self.frame_queue.put_nowait(frame)
                    except queue.Full:
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(frame)
                        except queue.Empty:
                            pass
                finally:
                    buf.unmap(map_info)
            else:
                msg = self.bus.timed_pop_filtered(10000, Gst.MessageType.ERROR | Gst.MessageType.EOS)
                if msg:
                    self.running = False

    def read(self):
        if not self.running:
            return False, None
        try:
            frame = self.frame_queue.get(timeout=1.0)
            return True, frame
        except queue.Empty:
            return False, None

    def isOpened(self):
        return self.running

    def release(self):
        self.running = False
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
        if self.thread:
            self.thread.join(timeout=2)
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
