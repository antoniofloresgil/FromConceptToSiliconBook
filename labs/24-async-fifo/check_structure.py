#!/usr/bin/env python3
"""Review the actual generic Yosys netlist's two-stage pointer chains.

This is a limited digital structural check, not a CDC/RDC or physical signoff tool.
"""
import json
from pathlib import Path
import sys


def check(path):
    module=json.loads(Path(path).read_text())['modules']['async_fifo']
    nets,cells=module['netnames'],module['cells']
    def flipflop(bit):
        drivers=[c for c in cells.values() if c['connections'].get('Q')==[bit]]
        assert len(drivers)==1,(bit,'not uniquely registered')
        c=drivers[0]
        assert c['type'].startswith('$_DFF'),c['type']
        return c['connections']
    checked=0
    for clock,source,first,second in [('wclk','r_gray','wq1_rgray','wq2_rgray'),
                                       ('rclk','w_gray','rq1_wgray','rq2_wgray')]:
        clk=module['ports'][clock]['bits']
        assert nets[first]['attributes']['ASYNC_REG']=='TRUE'
        assert nets[second]['attributes']['ASYNC_REG']=='TRUE'
        assert len(nets[first]['bits'])==len(nets[second]['bits'])==len(nets[source]['bits'])
        for src,q1,q2 in zip(nets[source]['bits'],nets[first]['bits'],nets[second]['bits']):
            a,b=flipflop(q1),flipflop(q2)
            assert a['D']==[src] and b['D']==[q1]
            assert a['C']==clk and b['C']==clk
            # The published Gray bit is itself a register output.
            source_clock='rclk' if clock=='wclk' else 'wclk'
            assert flipflop(src)['C']==module['ports'][source_clock]['bits']
            consumers=[(name,pin) for name,c in cells.items() for pin,bits in c['connections'].items()
                       if c['port_directions'][pin]=='input' and q1 in bits]
            assert len(consumers)==1 and consumers[0][1]=='D',consumers
            checked+=1
    return dict(pointer_bits_checked=checked,stages=2,first_stage_fanout='second-stage D only',
                scope='Generic netlist connectivity; no metastability, placement, skew or reset-tree qualification')


if __name__=='__main__': print(json.dumps(check(sys.argv[1]),indent=2))
