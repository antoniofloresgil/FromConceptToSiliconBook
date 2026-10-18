#!/usr/bin/env python3
"""Original package/integration boundary diagram using the architectural style."""
from pathlib import Path
from architecture import Drawing, outputs, BLUE, GREEN, ORANGE

d = Drawing('ip-release-boundaries', 'Reuse the release; adapt the platform',
            'One three-file RTL identity • platform collateral and evidence have separate owners', 560)
d.box(28,95,300,85,'AXI subsystem','AXI4-Lite stimulus + AXI RAM','profiles: 16 / 256')
d.box(632,95,300,85,'Real Wally RTL platform','RV32 firmware / AHB adapter','profile: 256; MMIO 0x10080000')
d.box(632,215,300,65,'Platform policy','decode / PMA / IRQ / buffers',color=ORANGE)
d.path('M782 180V215',ORANGE,dashed=True)
d.box(310,330,340,105,'dotproduct_ip 1.1.0','endpoint + engine + MAC','same three SHA-256 identities',color=GREEN)
d.path('M28 138H12V382H310')
d.path('M782 280V382H650')
d.box(28,215,300,65,'Register schema → views','RTL decode / C / assembly / docs')
d.path('M178 280V305H480V330',GREEN)
d.note(465,'A platform changes adapters, addresses and policies. An IP change creates a new release.',
       'Passing integration tests qualify these boundaries; technology-specific physical views need their own run.')
d.save()
target = Path(__file__).resolve().parents[2]/'figures/ip-release-boundaries.svg'
target.write_bytes(outputs['ip-release-boundaries.svg'])
print('GENERATED',target)
