import hashlib,json,os,subprocess
from pathlib import Path

def snapshot():
 root=Path('/cvw');files={};gitlinks={}
 for item in subprocess.check_output(['git','-C',str(root),'ls-files','--stage','-z']).decode().split('\0'):
  if not item:continue
  meta,name=item.split('\t',1);mode,oid,stage=meta.split();assert stage=='0'
  p=root/name
  if mode=='160000':gitlinks[name]=oid
  elif mode=='120000':files[name]=dict(kind='symlink',target=os.readlink(p))
  else:files[name]=dict(kind='file',sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 return dict(revision=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),files=files,
 gitlinks=gitlinks,gitlink_scope='Unpopulated submodules are recorded by commit only; Wally RTL export does not use them.')
