import subprocess,sys
for script in ['tools/book/test_build.py','tools/book/test_publish.py','tools/book/test_reference.py',
 'tools/book/test_learning_paths.py','labs/run.py']:
 args=[sys.executable,script]+(['check'] if script=='labs/run.py' else [])
 subprocess.run(args,check=True)
