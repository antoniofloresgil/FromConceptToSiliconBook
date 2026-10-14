"""Static recipe audit: Docker ownership, namespaces, links and shared interfaces."""
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'labs'))
from tools.catalog import LABS, WALLY_REPOSITORY, WALLY_REVISION

def exact_path(root,relative):
    path=root
    for part in Path(relative).parts:
        if part in {'','.'}:continue
        if part=='..':
            path=path.parent;continue
        if not path.is_dir() or part not in {p.name for p in path.iterdir()}:
            raise ValueError(f'Missing or incorrectly cased local path: {relative}')
        path=path/part
    return path

def fences(text):
    return [(m.group(1),m.group(2),text[:m.start()].count('\n')+1)
            for m in re.finditer(r'^```(bash|sh|powershell)\s*\n(.*?)^```\s*$',text,re.M|re.S)]

def docker_errors(language,command,contracts):
    errors=[]
    writable_work=('/work' in command and ('--mount' in command or ' -v ' in command)
                   and not re.search(r'target=/work,readonly',command))
    if writable_work:
        if language in {'bash','sh'} and '--user "$(id -u):$(id -g)"' not in command:
            errors.append('Writable Linux project mount lacks host UID/GID')
        if language=='powershell' and '$(id ' in command:
            errors.append('PowerShell recipe contains POSIX id expressions')
        if '--env HOME=/tmp' not in command:
            errors.append('Writable project recipe lacks writable container HOME')
    if 'from-concept-labs:' in command:
        if not any(tag in command for tag in [contracts['image_tag'],contracts['ci_image_tag']]):
            errors.append('Teaching image tag disagrees with recipe contracts')
        if '--network none' not in command:errors.append('Reference run lost its offline execution policy')
        if 'python labs/run.py run dotproduct-wally' in command:
            setting='--env LAB_BUILD_DIR='+contracts['outputs']['wally_build_dir']
            if setting not in command:errors.append('Wally run would overwrite the unit report')
            if '--env WALLY_ROOT=/cvw' not in command or 'target=/cvw,readonly' not in command:
                errors.append('Wally dependency must use the documented read-only mount')
    return errors

def module_ports(text,top):
    match=re.search(r'\bmodule\s+'+re.escape(top)+r'\s*\((.*?)\);',text,re.S)
    if not match:raise ValueError('Cannot find expected module interface: '+top)
    ports=[]
    for field in re.findall(r'\b(?:input|output|inout)\s+(?:logic\s+)?(?:\[[^\]]+\]\s*)?([^\n]+)',match.group(1)):
        ports.extend(name.strip() for name in field.split(',') if name.strip())
    return ports

def validate_wally_checkout(text,repository,revision):
    checkouts=re.findall(r'repository:\s*(\S+)\s+ref:\s*(\S+)',text)
    if (repository,revision) not in checkouts:
        raise ValueError('CI Wally repository/revision differs from the validated source contract')

def validate_interfaces(root,contracts):
    for interface in contracts['interfaces']:
        source=exact_path(root,interface['rtl']).read_text(encoding='utf-8')
        if set(module_ports(source,interface['top']))!=set(interface['ports']):
            raise ValueError('RTL ports disagree with contract: '+interface['rtl'])
        for test in interface['tests']:exact_path(root,test)
        if 'config' in interface:
            config=exact_path(root,interface['config']).read_text(encoding='utf-8')
            if re.search(r'^CLOCK_PORT:\s*(\S+)',config,re.M).group(1)!=interface['clock']:
                raise ValueError('Physical CLOCK_PORT does not match RTL')
            if 'dir::rtl/accumulator.sv' not in config:
                raise ValueError('Physical source selection changed; review the recipe contract')
            sdc=exact_path(root,interface['constraints']).read_text(encoding='utf-8')
            if '[get_ports '+interface['clock']+']' not in sdc:
                raise ValueError('SDC clock does not match RTL')
    makefile=exact_path(root,'examples/cocotb/Makefile').read_text(encoding='utf-8')
    if '../verilator/accumulator.sv' not in makefile or 'COCOTB_TOPLEVEL = accumulator' not in makefile:
        raise ValueError('cocotb no longer selects the shared simulation interface')

def main():
    contracts=json.loads((ROOT/'labs/recipe-contracts.json').read_text())
    if WALLY_REVISION!=contracts['wally_revision']:raise ValueError('Pinned Wally revision drift')
    if WALLY_REPOSITORY!=contracts['wally_repository']:raise ValueError('Pinned Wally repository drift')
    labs_workflow=ROOT/'.github/workflows/labs.yml'
    if labs_workflow.exists():
        validate_wally_checkout(labs_workflow.read_text(),WALLY_REPOSITORY,WALLY_REVISION)
    if 'Python '+contracts['runner_python_min']+'+' not in (ROOT/'labs/run.py').read_text():
        raise ValueError('Runner Python minimum drift')
    if [name for name,data in LABS.items() if data['mode']=='automatic']!=contracts['automatic_labs']:
        raise ValueError('Automatic lab list changed; update recipe counts/contracts')
    for name in ['labs/requirements.txt','examples/cocotb/requirements.txt']:
        if 'cocotb=='+contracts['cocotb_version'] not in exact_path(ROOT,name).read_text():
            raise ValueError('cocotb dependency pin drift: '+name)
    validate_interfaces(ROOT,contracts)
    documents=[ROOT/'labs/README.md']
    if (ROOT/'README.md').exists():documents.append(ROOT/'README.md')
    documents+=list((ROOT/'chapters').rglob('*.qmd'))+list((ROOT/'appendices').glob('*.qmd'))
    documents += [p for p in (ROOT/'labs').rglob('README.md') if not any(x in {'build','work'} for x in p.relative_to(ROOT).parts)]
    errors=[];commands=0;links=0
    for path in documents:
        text=path.read_text(encoding='utf-8')
        for language,body,line in fences(text):
            normalized=body.replace('\\\n',' ').replace('`\n',' ')
            for command in normalized.splitlines():
                if not re.match(r'^(?:sudo\s+)?docker run ',command.strip()):continue
                commands+=1
                errors.extend(f'{path.relative_to(ROOT)}:{line}: {message}' for message in docker_errors(language,command,contracts))
        for target in re.findall(r'\]\(([^\n)]+)\)',text):
            url=target.strip('<> ')
            if urlsplit(url).scheme or url.startswith('#'):continue
            relative=unquote(url.split('#')[0])
            if relative.endswith('.html'):continue # rendered destinations, not source files
            destination=(path.parent/relative).resolve()
            if destination==ROOT/'downloads/hardware-design-labs.zip':continue # generated by pack
            if not destination.is_relative_to(ROOT):continue # explicitly external context
            try:exact_path(ROOT,destination.relative_to(ROOT));links+=1
            except ValueError as error:errors.append(f'{path.relative_to(ROOT)}: {error}')
    # CI folded run blocks are Bash. Check both folded and single-line commands.
    for workflow in [ROOT/'.github/workflows/labs.yml', ROOT/'.github/workflows/publish.yml']:
        if not workflow.exists():continue # workflows are omitted from the lab ZIP
        text=workflow.read_text()
        for m in re.finditer(r'run:\s*([|>])-?\s*\n((?:[ ]{10,}[^\n]*\n)+)',text):
            lines=[line.strip() for line in m.group(2).splitlines()]
            ci_commands=[' '.join(lines)] if m.group(1)=='>' else '\n'.join(lines).replace('\\\n',' ').splitlines()
            for command in ci_commands:
                if command.startswith('docker run '):
                    errors.extend('CI: '+e for e in docker_errors('bash',command,contracts))
        for command in re.findall(r'run: (docker run [^\n]+)',text):
            errors.extend('CI: '+e for e in docker_errors('bash',command,contracts))
    if errors:raise ValueError('\n'.join(errors))
    print(f'PASS recipe coherence: {commands} documented Docker invocations, {links} local links, two RTL interfaces, versions and output namespaces')

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,AttributeError,KeyError) as error:
        print(f'FAIL recipe coherence: {error}',file=sys.stderr);sys.exit(1)
