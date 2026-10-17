"""Small explicit ownership/visibility/dependency models; not RTL or RVWMO validation."""
import itertools
import json
from pathlib import Path

class Domain:
    """Two coherent CPU views, non-snooping DMA, explicit whole-line actions.

    A dirty owner may forward a clean reader copy without updating backing RAM.
    This is an executable visibility abstraction, not a MESI implementation.
    """
    def __init__(self):self.ram={};self.caches=[{},{}];self.trace=[]
    def backing(self,line):return self.ram.setdefault(line,[0,0])
    def load(self,hart,address):
        line,word=divmod(address,2);cache=self.caches[hart]
        if line not in cache:
            peer=self.caches[1-hart].get(line)
            data=peer['data'] if peer and peer['dirty'] else self.backing(line)
            cache[line]={'data':list(data),'dirty':False}
        value=cache[line]['data'][word];self.trace.append(['cpu_load',hart,address,value]);return value
    def store(self,hart,address,value):
        line,word=divmod(address,2);self.load(hart,address)
        peer=self.caches[1-hart].get(line)
        if peer and peer['dirty']:self.clean(1-hart,line)
        self.caches[1-hart].pop(line,None)
        self.caches[hart][line]['data'][word]=value;self.caches[hart][line]['dirty']=True
        self.trace.append(['cpu_store',hart,address,value])
    def clean(self,hart,line):
        entry=self.caches[hart].get(line)
        if entry and entry['dirty']:
            self.ram[line]=list(entry['data']);entry['dirty']=False
        self.trace.append(['local_clean',hart,line])
    def clean_domain(self,line):
        for hart in range(2):self.clean(hart,line)
        self.trace.append(['domain_clean',line])
    def invalidate(self,hart,line):
        entry=self.caches[hart].get(line)
        if entry and entry['dirty']:raise ValueError('Refuse to discard dirty CPU data')
        self.caches[hart].pop(line,None);self.trace.append(['invalidate',hart,line])
    def evict(self,hart,line):
        self.clean(hart,line);self.invalidate(hart,line);self.trace.append(['evict',hart,line])
    def dma_read(self,address):
        line,word=divmod(address,2);value=self.backing(line)[word]
        self.trace.append(['dma_read',address,value]);return value
    def dma_write(self,address,value):
        line,word=divmod(address,2);self.backing(line)[word]=value;self.trace.append(['dma_write',address,value])
    def fence(self):self.trace.append(['fence_order_only'])

def ordering(release,acquire):
    constraints=[('publish','flag')]
    if release:constraints.append(('data','publish'))
    if acquire:constraints.append(('flag','read'))
    traces=[]
    for events in itertools.permutations(['data','publish','flag','read']):
        if any(events.index(a)>events.index(b) for a,b in constraints):continue
        value=int(events.index('data')<events.index('read'))
        traces.append({'events':list(events),'observed_data':value})
    return {'executions':len(traces),'stale':sum(t['observed_data']==0 for t in traces),
            'witness':next((t for t in traces if not t['observed_data']),None)}

def cycle(graph):
    def visit(node,path):
        if node in path:return path[path.index(node):]+[node]
        for nxt in graph.get(node,[]):
            found=visit(nxt,path+[node])
            if found:return found
        return None
    return next((c for n in graph if (c:=visit(n,[]))),None)

def experiment():
    checks={}
    # A coherent CPU pair forwards the dirty owner's newest value, while a
    # non-snooping DMA reads backing RAM. FENCE changes order, not these bytes.
    domain=Domain();domain.store(0,0,7);peer_value=domain.load(1,0);old=domain.dma_read(0)
    assert peer_value==7 and old==0
    checks['dirty-input']={'cpu1_sees':peer_value,'dma_sees':old,'expected_stale':True,'trace':list(domain.trace)}
    domain.fence();old=domain.dma_read(0);assert old==0
    checks['fence-without-clean']={'dma_sees':old,'expected_stale':True,'trace':list(domain.trace)}
    domain.clean(1,0);old=domain.dma_read(0);assert old==0
    checks['clean-only-local-non-owner']={'dma_sees':old,'expected_stale':True,'trace':list(domain.trace),
        'assumption':'This local-only operation cannot clean the remote dirty owner'}
    domain.clean_domain(0);new=domain.dma_read(0);assert new==7
    checks['domain-clean-before-launch']={'dma_sees':new,'pass':True,'trace':list(domain.trace)}
    domain=Domain();assert domain.load(1,0)==0;domain.dma_write(0,49);domain.fence()
    stale=domain.load(1,0);assert stale==0 and domain.dma_read(0)==49
    checks['completion-without-invalidate']={'cpu1_sees':stale,'ram':49,'expected_stale':True,'trace':list(domain.trace)}
    domain.invalidate(1,0);new=domain.load(1,0);assert new==49
    checks['invalidate-before-consume']={'cpu1_sees':new,'pass':True,'trace':list(domain.trace)}
    # Two words share one abstract line. A dirty CPU writeback overwrites DMA.
    domain=Domain();domain.store(0,1,1);domain.dma_write(0,49);domain.evict(0,0)
    lost=domain.dma_read(0);assert lost==0 and domain.dma_read(1)==1
    checks['false-sharing-writeback']={'result':lost,'flag':1,'expected_lost_result':True,'trace':list(domain.trace)}
    domain=Domain();domain.store(0,2,1);domain.dma_write(0,49);domain.evict(0,1)
    result=domain.dma_read(0);assert result==49
    checks['separate-owned-lines']={'result':result,'pass':True,'trace':list(domain.trace)}
    for release,acquire in [(False,False),(True,False),(False,True),(True,True)]:
        result=ordering(release,acquire)
        if (result['stale']==0)!=(release and acquire):raise AssertionError('Publication model invariant')
        checks[f'publication-release{int(release)}-acquire{int(acquire)}']=result
    blocked={'request':['probe'],'probe':['response'],'response':['request']}
    repaired={'request':['probe'],'probe':['response'],'response':[]}
    checks['dependency-cycle']={'cycle':cycle(blocked),'repair_cycle':cycle(repaired),
        'scope':'Finite resource-dependency abstraction; not a full protocol liveness proof'}
    if not cycle(blocked) or cycle(repaired):raise AssertionError('Dependency graph invariant')
    fixed=[0]*16;round_robin=[i%2 for i in range(16)]
    checks['arbitration']={'fixed_priority_hart1_grants':fixed.count(1),
        'round_robin_hart1_grants':round_robin.count(1),'assumption':'Both request continuously; every response is accepted'}
    old_epoch=3;current_epoch=4
    checks['late-completion']={'untagged_completion_accepted':True,'tagged_completion_accepted':old_epoch==current_epoch,
        'scope':'Hypothetical tagged interface; the supplied dot-product IP has no reset/epoch register'}
    return {'status':'pass','scope':'Explicit finite visibility/cache-line/dependency examples, not a complete ISA/cache/interconnect model',
            'checks':checks}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);a=p.parse_args()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(experiment(),indent=2)+'\n');print('PASS explicit multicore models')
