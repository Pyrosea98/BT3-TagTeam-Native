"""Let ordinary native rematches run visibly while rebuild support is pending."""

import os


def install_stable(autopilot, pine=None):
    if os.environ.get('PS2X_NATIVE_REMATCH') == '1':
        from codex_native_rematch_rebuild import install
        install(autopilot, pine)
        return
    def unavailable(self, source, ack_token):
        raise ValueError('Native simultaneous-team rematches are not supported yet. '
                         'Close the game and reopen the Vulkan trial to play another match')
    autopilot.Autopilot.load_file = unavailable
    original_observe = autopilot.Autopilot.observe
    def observe(self):
        obs = original_observe(self)
        if (obs is not None and self.state == 'ACTIVE' and obs.loop == 1
                and obs.team_mode == 0
                and autopilot.menu_return.return_destination(obs.result_flags,obs.return_flags) is None):
            # Native reset already withdrew expanded routing. This is a new
            # ordinary match, not a request to load a PCSX2 checkpoint. Keep
            # the retained patches/allocations out of fresh preparation.
            self.reset_reload_worker()
            self.state = 'NATIVE_REMATCH'
            self.heartbeat = None
            if pine is not None and self.playable:
                try:
                    from native_rematch_cleanup import audit
                    folder, ownership = audit(self,pine)
                    autopilot.log(f'Native rematch cleanup audit: {ownership["after"]["used_blocks"]} retained heap blocks; {folder}')
                    if os.environ.get('PS2X_REMATCH_RESTORE')=='1':
                        from native_rematch_cleanup import restore_patches
                        restored,skipped=restore_patches(ownership,pine)
                        autopilot.log(f'Native rematch hook restore: {restored} ranges restored, {skipped} skipped')
                except (OSError,ValueError,RuntimeError,TimeoutError,pine.PineError) as error:
                    autopilot.log(f'Native rematch cleanup audit stopped: {error}')
            self.uncover()
            self.report('Native rematch is running in ordinary tag-team mode. '
                        'Simultaneous extra fighters have not been rebuilt.',obs,'warning')
        return obs
    autopilot.Autopilot.observe = observe
    original_report = autopilot.Autopilot.report
    def report(self, message, *args, **kwargs):
        if message.startswith('Simultaneous match ready. Rematch checkpoint:'):
            message='Simultaneous match ready. Fight Again currently returns to ordinary tag-team mode; simultaneous rebuilding is pending.'
        return original_report(self, message, *args, **kwargs)
    autopilot.Autopilot.report = report

