from lib.flash_spi import FLASH
from system.hexpansion.config import HexpansionConfig
from machine import SPI
import os
import app
from app_components import Notification

# default location to mount the main flash device
_MOUNTPATH = "/flopagon"

_STATE_INIT = 0
_STATE_MOUNTED = 1
_STATE_ERROR = 2

class FlopagonApp(app.App):
    def __init__(self, config=None):
        # run the app class init
        super().__init__()
        if config is None:
            return

        # if this is run from the EEPROM then config will be a HexpansionConfig for whatever slot it's plugged into
        self._config = config

        # create a handle for the notification
        self._notification = None

        # set up the chip select pin, it's the first high-speed IO pin on the hexpansion
        cspin = self._config.pin[0]
        cspin.init(cspin.OUT, value=1)
        self._cspins = (cspin,)

        # set up the SPI device, we specify all the pins and max out at 10MHz
        # SPI 2 is used for the CTX graphics driver, SPI1 can be used by python code
        self._hspi = SPI(1, 10000000, sck=self._config.pin[1], mosi=self._config.pin[2], miso=self._config.pin[3])

        self._flash = None
        self._state = _STATE_INIT


    def flash(self) -> FLASH:
        return self._flash


    def state(self, state=None):
        if state is not None:
            self._state = state
        return self._state


    # ctx GUI stuff just taken from the examples
    def draw(self, ctx):
        #clear_background(ctx)
        if self._notification:
            self._notification.draw(ctx)


    def update(self, delta):
        if self._state == _STATE_INIT:
            if self._flash is None:
                # wait to setup the flash device until the app is running
                #
                # Create a handle on the flash object, if you watch the serial console you'll see
                #  1 chips detected. Total flash size 16MiB.
                # at this point if all is working
                try:
                    self._flash = FLASH(self._hspi, self._cspins, cmd5=False)
                    os.mount(self._flash, _MOUNTPATH)
                    self._state = _STATE_MOUNTED
                    self._notification = Notification(f"Mounted")
                    print("Flopagon Mounted")                                     
                except Exception as e:
                    self._notification = Notification(f"Error: {e}")
                    print(f"Error: {e}")
                    self._state = _STATE_ERROR
            
        if self._notification:
            self._notification.update(delta)


__app_export__ = FlopagonApp
