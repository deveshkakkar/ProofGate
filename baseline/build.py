#!/usr/bin/env python3
import pathlib,shutil,subprocess
src=pathlib.Path('/src');out=pathlib.Path('/out')
# No candidate-controlled script executes during build. Copy the exact app source
# and use the pinned compiler on the formal implementation proved by PROOF.bend.
subprocess.run(['/toolchains/bend/bin/bend','/src/formal/Admission.bend','-o','/out/admission.mjs'],check=True)
shutil.copyfile(src/'app/server.ts',out/'server.ts')
print('BUILD_COMPLETE')
