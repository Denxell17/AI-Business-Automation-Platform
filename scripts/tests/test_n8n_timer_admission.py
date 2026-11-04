"""Only new timer admission boundaries; no systemd or backup calls."""
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
m=runpy.run_path(str(ROOT/'deploy/hosthatch/activate-reviewed-n8n-timer-once.py'))
class TimerAdmissionTests(unittest.TestCase):
    def test_existing_calendar_contract_accepted(self):
        m['timer_contract']((ROOT/'deploy/hosthatch/systemd/n8n-backup.timer').read_text())
    def test_unexpected_trigger_rejected(self):
        text=(ROOT/'deploy/hosthatch/systemd/n8n-backup.timer').read_text()
        for old,new in [('05:30:00','06:30:00'),('Persistent=true','Persistent=false'),
                        ('Unit=n8n-backup.service','Unit=another.service'),
                        ('Persistent=true','Persistent=true\nOnBootSec=1')]:
            with self.subTest(new=new),self.assertRaises(m['Stop']):m['timer_contract'](text.replace(old,new))
    def test_missing_approval_stops_before_units_or_files(self):
        with patch.object(m['os'],'geteuid',return_value=0,create=True),patch.object(m['sys'],'argv',['controller']):
            with self.assertRaisesRegex(m['Stop'],'explicit_timer_activation_approval_required'):m['main']()
if __name__=='__main__':unittest.main()
