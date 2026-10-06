#!/usr/bin/env python3
"""Package a relocatable Linux SDK; run only in the SDK build repository."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile


def run(*args):
    return subprocess.check_output([str(a) for a in args], text=True).strip()


def copytree(src, dst):
    shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=Path('build'))
    parser.add_argument('--output', type=Path, default=Path('dist'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    build = args.build.resolve()
    engine = build / 'engine'
    cache = dict(line.split('=', 1) for line in (build / 'CMakeCache.txt').read_text().splitlines()
                 if line and not line.startswith(('#', '//')) and '=' in line)
    usd = Path(cache['SWARM_USD_ROOT:PATH'])
    patchelf = shutil.which('patchelf')
    if not patchelf:
        raise SystemExit('SDK packaging requires patchelf (sudo apt install patchelf).')
    os_info = platform.freedesktop_os_release()
    name = f'mujoco-3.15.0-usd-25.11-{os_info["ID"]}{os_info["VERSION_ID"]}-{platform.machine()}-r1'
    out = args.output.resolve() / name
    if out.exists():
        raise SystemExit(f'Refusing to overwrite {out}; choose a fresh --output directory.')
    (out / 'lib').mkdir(parents=True)
    copytree(root / 'third_party/mujoco/include', out / 'include')
    copytree(usd / 'include', out / 'include')
    copytree(engine / '_deps/glfw3-src/include/GLFW', out / 'include/GLFW')
    (out / 'include/simulate').mkdir()
    for header in (root / 'third_party/mujoco/simulate').glob('*.h'):
        shutil.copy2(header, out / 'include/simulate' / header.name)
    for src in (usd / 'lib', engine / 'lib'):
        for entry in src.iterdir():
            if '.so' in entry.name and '_debug' not in entry.name:
                # Resolve source symlinks to avoid retaining absolute cache paths.
                shutil.copy2(entry.resolve(), out / 'lib' / entry.name)
    for filename in ('libsimulate.a',):
        shutil.copy2(engine / 'lib' / filename, out / 'lib' / filename)
    shutil.copy2(engine / 'lib/libglfw3.a', out / 'lib/libglfw3.a')
    copytree(usd / 'lib/usd', out / 'lib/usd')
    copytree(engine / 'lib/mujoco-usd-resources', out / 'lib/mujoco-usd-resources')
    # Every shared object resolves its own sibling dependencies, independent of the app.
    for library in (out / 'lib').glob('*.so*'):
        if library.read_bytes()[:4] != b'\x7fELF':
            continue  # TBB also supplies text linker scripts.
        subprocess.run(['strip', '--strip-unneeded', str(library)], check=True)
        subprocess.run([patchelf, '--set-rpath', '$ORIGIN', str(library)], check=True)
    for library in (out / 'lib').glob('*.a'):
        subprocess.run(['strip', '--strip-debug', str(library)], check=True)
    # Coalesce ABI aliases after patching; Git stores these as small relative symlinks.
    seen = {}
    for library in sorted((out / 'lib').glob('*.so*'), key=lambda p: (-len(p.name), p.name)):
        digest = hashlib.sha256(library.read_bytes()).hexdigest()
        if digest in seen:
            library.unlink()
            library.symlink_to(seen[digest])
        else:
            seen[digest] = library.name
    cmake = out / 'lib/cmake/SwarmMuJoCoSDK'
    cmake.mkdir(parents=True)
    shutil.copy2(root / 'cmake/SwarmMuJoCoSDKConfig.cmake', cmake)
    licenses = out / 'licenses'
    sources = [root / 'third_party/mujoco', root / 'third_party/openusd']
    sources += list((engine / '_deps').glob('*-src')) + list((usd / 'src').glob('*'))
    for source in sources:
        if not source.is_dir():
            continue
        for pattern in ('LICENSE*', 'NOTICE*', 'COPYING*', 'license*', 'copyright*'):
            for item in source.glob(pattern):
                if item.is_file():
                    target = licenses / source.name / item.name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target)
    metadata = {
        'name': name, 'mujoco': '3.15.0', 'openusd': '25.11',
        'mujoco_commit': run('git', '-C', root / 'third_party/mujoco', 'rev-parse', 'HEAD'),
        'openusd_commit': run('git', '-C', root / 'third_party/openusd', 'rev-parse', 'HEAD'),
        'platform': os_info['PRETTY_NAME'], 'architecture': platform.machine(), 'cpu_requirement': 'AVX', 'lto': False,
        'compiler': run('c++', '--version').splitlines()[0],
        'libc': run('getconf', 'GNU_LIBC_VERSION'),
        'features': ['USD decoder', 'official simulate UI', 'GLFW X11', 'no Python runtime'],
        'system_runtime': ['glibc', 'libstdc++', 'libgcc', 'X11/GL libraries and graphics driver'],
        'dependency_commits': {p.name: run('git', '-C', p, 'rev-parse', 'HEAD')
                               for p in (engine / '_deps').glob('*-src') if (p / '.git').exists()},
    }
    (out / 'VERSION.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    (out / 'README.md').write_text('''# MuJoCo USD SDK

Self-built SDK, not an official binary release. See VERSION.json for platform and versions.
MuJoCo/OpenUSD licenses and bundled dependency notices are under licenses/.
Keep the complete directory together; libraries and USD resources use relative paths.
Use find_package(SwarmMuJoCoSDK CONFIG REQUIRED) with this directory in CMAKE_PREFIX_PATH.
System compiler, CMake, C/C++ runtime and graphics driver are not bundled.
This build targets Ubuntu 24.04 x86_64 with AVX; Ubuntu 20.04/22.04 compatibility is not claimed.
''')
    # Check dependencies in the completed package, with no LD_LIBRARY_PATH override.
    env = dict(os.environ)
    env.pop('LD_LIBRARY_PATH', None)
    for library in (out / 'lib').glob('*.so*'):
        if library.read_bytes()[:4] != b'\x7fELF':
            continue  # TBB also supplies text linker scripts.
        result = subprocess.check_output(['ldd', str(library)], env=env, text=True)
        if 'not found' in result or '/home/' in result.replace(str(out), ''):
            raise RuntimeError(f'Unresolved or nonportable dependencies in {library}:\n{result}')
    entries = []
    for file in sorted(out.rglob('*')):
        if file.is_file():
            entries.append(f'{hashlib.sha256(file.read_bytes()).hexdigest()}  {file.relative_to(out)}')
    (out / 'SHA256SUMS').write_text('\n'.join(entries) + '\n')
    archive = out.parent / (name + '.tar.gz')
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(out, arcname=name)
    (archive.parent / (archive.name + '.sha256')).write_text(
        hashlib.sha256(archive.read_bytes()).hexdigest() + '  ' + archive.name + '\n')
    print(out)
    print(archive)


if __name__ == '__main__':
    main()
