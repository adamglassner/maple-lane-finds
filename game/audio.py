"""Audio manager. If the PC has no sound device, the game simply runs silently (never crashes)."""
import pygame

from . import synth


class Audio:
    def __init__(self, settings):
        self.settings = settings
        self.ok = False
        self.sounds = {}
        self.music = None
        self.music_channel = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(synth.SR, -16, 2, 1024)
            freq, _fmt, channels = pygame.mixer.get_init()
            if freq != synth.SR:
                raise RuntimeError("unexpected mixer rate")
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)
            self.channels = channels
            self.ok = True
        except Exception:
            self.ok = False
            return
        try:
            for name, (fn, gain) in synth.SFX.items():
                self.sounds[name] = pygame.sndarray.make_sound(synth.to_stereo_int16(fn(), gain, channels))
            left, right = synth.make_music()
            self.music = pygame.sndarray.make_sound(synth.to_stereo_int16(left, 0.8, channels, pan_wide=(left, right)))
            self.music_channel = pygame.mixer.Channel(0)
        except Exception:
            self.ok = False
        self.apply_volumes()

    def _music_vol(self):
        return 0.0 if self.settings["muted"] else self.settings["music_volume"] * 0.75

    def _sfx_vol(self):
        return 0.0 if self.settings["muted"] else self.settings["sfx_volume"]

    def apply_volumes(self):
        if not self.ok:
            return
        if self.music_channel:
            self.music_channel.set_volume(self._music_vol())

    def start_music(self):
        if self.ok and self.music and self.music_channel and not self.music_channel.get_busy():
            self.music_channel.play(self.music, loops=-1, fade_ms=1500)
            self.apply_volumes()

    def play(self, name, volume=1.0):
        if not self.ok:
            return
        snd = self.sounds.get(name)
        v = self._sfx_vol() * volume
        if snd and v > 0:
            ch = pygame.mixer.find_channel(True)
            if ch:
                ch.set_volume(v)
                ch.play(snd)
