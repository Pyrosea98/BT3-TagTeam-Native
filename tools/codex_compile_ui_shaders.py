"""Build embedded SPIR-V with the repository's bundled glslang compiler."""
from pathlib import Path
import subprocess
import struct
HERE=Path(__file__).resolve().parent
compiler=HERE/'repo/ps2xRuntime/third_party/parallel-gs/Granite/third_party/fsr2/tools/sc/glslangValidator.exe'
folder=HERE/'repo/ps2xRuntime/src/lib/seamvk'
for stage in ('vert','frag'):
    source=folder/f'ui_text.{stage}'
    binary=HERE/'power-scale-trial'/f'ui_text.{stage}.spv'
    subprocess.run([str(compiler),'-V',str(source),'-o',str(binary)],check=True)
    data=binary.read_bytes()
    words=struct.unpack('<'+'I'*(len(data)//4),data)
    (folder/f'ui_text.{stage}.inc').write_text(',\n'.join('0x%08xu'%w for w in words)+'\n')
