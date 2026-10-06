from app.services.naya_listener import (
    NayaListener,
    naya_listener,
)


class MayaListener(NayaListener):
    """Compatibility wrapper for older imports."""

    def listen_for_maya(self):

        return self.listen_for_wake_phrase()


maya_listener = naya_listener
