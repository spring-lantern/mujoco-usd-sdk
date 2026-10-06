#!/usr/bin/env python3
"""Validate a release binary without ROS: USD load, seven vehicles and one takeoff."""
import argparse
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('binary', type=Path)
parser.add_argument('--scene', default='forest', choices=['forest', 'empty'])
args = parser.parse_args()
with socket.socket() as reserve:
    reserve.bind(('127.0.0.1', 0))
    port = reserve.getsockname()[1]
with tempfile.TemporaryFile(mode='w+') as output:
    process = subprocess.Popen([str(args.binary.resolve()), '--scene', args.scene, '--headless',
                                '--count', '7', '--columns', '6', '--ros-port', str(port)],
                               stdout=output, stderr=subprocess.STDOUT, cwd='/tmp')
    client = None
    try:
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline and process.poll() is None:
            try:
                client = socket.create_connection(('127.0.0.1', port), timeout=1)
                break
            except OSError:
                time.sleep(0.2)
        if client is None:
            raise RuntimeError('Simulation did not open its TCP port')
        client.settimeout(2)
        stream = client.makefile('rb')
        assert stream.readline().decode().strip() == 'H 1 7'
        client.sendall(b'A 1 1 2\n')
        acknowledged = False
        states = {}
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            fields = stream.readline().decode().split()
            if not fields:
                raise RuntimeError('Simulation closed its connection')
            if fields[0] == 'R':
                assert fields == ['R', '1', '1'], fields
                acknowledged = True
            elif fields[0] == 'S':
                assert all(math.isfinite(float(v)) for v in fields[2:]), fields
                states[int(fields[1])] = [float(v) for v in fields[4:7]]
            if acknowledged and len(states) == 7 and states[1][2] > 1.8:
                assert all(states[n][2] < 0.3 for n in range(2, 8)), states
                # First six occupy one row, final aircraft is centered in another.
                assert abs(states[2][1]-states[6][1]) < 0.02, states
                assert abs(states[7][0]) < 0.02, states
                print(json.dumps({'result': 'pass', 'scene': args.scene, 'vehicles': 7,
                                  'takeoff_z': states[1][2], 'other_vehicles_grounded': True}))
                break
        else:
            raise RuntimeError('Aircraft did not reach takeoff height')
    except Exception:
        output.seek(0)
        print(output.read())
        raise
    finally:
        if client:
            client.close()
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
