"""Strict reader/writer for the SGF YMD subset used by the supplied Yo-kai.

Little endian, expanded triangle streams, skin-weight palette, SRT nodes,
sampled SRT motion channels. No game/server process is required.
"""
import math
import struct

VERSION = 20150817


class Reader:
    def __init__(self, data):
        self.data, self.pos = data, 0

    def take(self, size):
        if size < 0 or self.pos + size > len(self.data):
            raise ValueError(f"YMD tronqué à l'octet {self.pos}.")
        value = self.data[self.pos:self.pos + size]
        self.pos += size
        return value

    def u(self):
        return struct.unpack('<I', self.take(4))[0]

    def count(self, limit=1000000):
        value = self.u()
        if value > limit:
            raise ValueError(f"Compteur YMD excessif : {value}.")
        return value

    def s(self):
        return self.take(self.count(4096)).decode('utf-8')

    def f(self, n=1):
        values = list(struct.unpack('<' + 'f' * n, self.take(n * 4)))
        if not all(math.isfinite(x) for x in values):
            raise ValueError('Valeur non finie dans le YMD.')
        return values


def loads(data):
    r = Reader(data)
    version = r.u()
    if version not in (1, VERSION):
        raise ValueError(f'Révision YMD non prise en charge : {version}.')
    scene = dict(version=version, materials=[], meshes=[], skins=[], nodes=[], clips=[])
    for _ in range(r.count(4096)):
        mat = dict(name=r.s(), version=r.u(), texture=r.s())
        if mat['version'] != 1 or r.u() != 0:
            raise ValueError('Paramètres de matériau YMD non pris en charge.')
        scene['materials'].append(mat)
    for _ in range(r.count(4096)):
        mesh = dict(name=r.s(), primitives=[])
        for _ in range(r.count(4096)):
            primitive = dict(kind=r.u(), flags=r.u(), material=r.s())
            stride, count = r.u(), r.count(2000000)
            if stride not in (20, 32):
                raise ValueError(f'Format de sommet non pris en charge : {stride} octets.')
            primitive.update(stride=stride, vertices=[r.f(stride // 4) for i in range(count)])
            primitive['indices'] = [r.u() for i in range(r.count(2000000))]
            mesh['primitives'].append(primitive)
        scene['meshes'].append(mesh)
    for _ in range(r.count(4096)):
        skin = dict(name=r.s(), bones=[], weights=[])
        for i in range(r.count(512)):
            skin['bones'].append(dict(name=r.s(), inverse=r.f(16)))
        for i in range(r.count(2000000)):
            skin['weights'].append([[r.u(), r.f()[0]] for j in range(r.count(4))])
        scene['skins'].append(skin)
    for _ in range(r.count(10000)):
        scene['nodes'].append(dict(name=r.s(), parent=r.s(), meshes=[r.s() for i in range(r.count(4096))], srt=r.f(10)))
    for _ in range(r.count(4096)):
        clip = dict(name=r.s(), duration=r.f()[0], tracks=[])
        for i in range(r.count(10000)):
            track = dict(node=r.s(), keys=[])
            for j in range(r.count(100000)):
                key = r.f(11) + [r.u()] + r.f(4)
                track['keys'].append(key)
            clip['tracks'].append(track)
        if r.u() != 0:
            raise ValueError('Pistes de caméra/matériau supplémentaires non prises en charge.')
        scene['clips'].append(clip)
    if r.pos != len(data):
        raise ValueError(f'{len(data) - r.pos} octets YMD non interprétés.')
    validate(scene)
    return scene


def validate(scene):
    def unique(rows, key='name'):
        values = [v[key] for v in rows]
        if len(set(values)) != len(values):
            raise ValueError(f'Noms {key} dupliqués.')
        return set(values)
    mats = unique(scene['materials'])
    meshes = unique(scene['meshes'])
    nodes = unique(scene['nodes'])
    unique(scene['clips']); unique(scene['skins'])
    parents = {v['name']: v['parent'] for v in scene['nodes']}
    for node in scene['nodes']:
        if len(node['srt']) != 10 or not all(math.isfinite(x) for x in node['srt']):
            raise ValueError('Transformation SRT invalide.')
        if node['parent'] and node['parent'] not in nodes:
            raise ValueError('Parent de nœud absent : ' + node['parent'])
        if not set(node['meshes']) <= meshes:
            raise ValueError('Géométrie référencée absente.')
        visited = set(); cursor = node['name']
        while cursor:
            if cursor in visited:
                raise ValueError('Cycle dans le squelette.')
            visited.add(cursor); cursor = parents[cursor]
        q = node['srt'][3:7]
        if abs(sum(x*x for x in q) - 1) > .002:
            raise ValueError('Quaternion de nœud non normalisé.')
    skins = {s['name']: s for s in scene['skins']}
    for skin in scene['skins']:
        if skin['name'] not in meshes:
            raise ValueError('Skin sans géométrie.')
        if not {b['name'] for b in skin['bones']} <= nodes:
            raise ValueError('Os de skin absent du squelette.')
        for weights in skin['weights']:
            if any(b >= len(skin['bones']) or w < 0 for b, w in weights):
                raise ValueError('Influence de skin invalide.')
            if abs(sum(w for _, w in weights) - 1) > .002:
                raise ValueError('Poids de skin non normalisés.')
    for mesh in scene['meshes']:
        for p in mesh['primitives']:
            if p['stride'] not in (20,32) or any(len(v)*4 != p['stride'] or not all(math.isfinite(x) for x in v) for v in p['vertices']):
                raise ValueError('Données de sommets invalides.')
            if p['material'] not in mats or len(p['vertices']) % 3:
                raise ValueError('Matériau absent ou triangles incomplets.')
            if len(p['indices']) != len(p['vertices']):
                raise ValueError('Palette de sommets de taille incorrecte.')
            if mesh['name'] in skins and any(i >= len(skins[mesh['name']]['weights']) for i in p['indices']):
                raise ValueError('Index de poids hors limites.')
    for clip in scene['clips']:
        if not math.isfinite(clip['duration']) or clip['duration'] < 0:
            raise ValueError('Durée négative.')
        unique(clip['tracks'], 'node')
        for track in clip['tracks']:
            if track['node'] not in nodes or not track['keys']:
                raise ValueError('Piste vide ou nœud absent.')
            times = [k[0] for k in track['keys']]
            if times != sorted(times) or times[0] < 0 or times[-1] > clip['duration'] + .001:
                raise ValueError('Temps de piste incohérents.')
            for key in track['keys']:
                if len(key) != 16 or not all(math.isfinite(x) for x in key):
                    raise ValueError('Clé d’animation invalide.')
                if abs(sum(x*x for x in key[4:8])-1) > .002:
                    raise ValueError('Quaternion d’animation non normalisé.')


def dumps(scene):
    validate(scene)
    out = bytearray()
    def u(x): out.extend(struct.pack('<I', int(x)))
    def f(xs):
        if not all(math.isfinite(x) for x in xs): raise ValueError('Valeur non finie.')
        out.extend(struct.pack('<' + 'f' * len(xs), *xs))
    def s(x):
        b = x.encode('utf-8'); u(len(b)); out.extend(b)
    u(scene.get('version', VERSION)); u(len(scene['materials']))
    for mat in scene['materials']: s(mat['name']); u(1); s(mat['texture']); u(0)
    u(len(scene['meshes']))
    for mesh in scene['meshes']:
        s(mesh['name']); u(len(mesh['primitives']))
        for p in mesh['primitives']:
            u(p.get('kind', 1)); u(p.get('flags', 0)); s(p['material']); u(p['stride']); u(len(p['vertices']))
            for v in p['vertices']: f(v)
            u(len(p['indices']))
            for i in p['indices']: u(i)
    u(len(scene['skins']))
    for skin in scene['skins']:
        s(skin['name']); u(len(skin['bones']))
        for b in skin['bones']: s(b['name']); f(b['inverse'])
        u(len(skin['weights']))
        for weights in skin['weights']:
            u(len(weights))
            for bone, weight in weights: u(bone); f([weight])
    u(len(scene['nodes']))
    for node in scene['nodes']:
        s(node['name']); s(node['parent']); u(len(node['meshes']))
        for mesh in node['meshes']: s(mesh)
        f(node['srt'])
    u(len(scene['clips']))
    for clip in scene['clips']:
        s(clip['name']); f([clip['duration']]); u(len(clip['tracks']))
        for track in clip['tracks']:
            s(track['node']); u(len(track['keys']))
            for key in track['keys']: f(key[:11]); u(key[11]); f(key[12:])
        u(0)
    return bytes(out)


def summary(scene):
    vertices = [v for m in scene['meshes'] for p in m['primitives'] for v in p['vertices']]
    return dict(meshes=len(scene['meshes']), triangles=len(vertices)//3,
                vertices=len(vertices), bones=len({b['name'] for s in scene['skins'] for b in s['bones']}),
                nodes=len(scene['nodes']), materials=len(scene['materials']),
                clips=[dict(name=c['name'], duration=c['duration'], tracks=len(c['tracks'])) for c in scene['clips']],
                bounds=[[min(v[i] for v in vertices), max(v[i] for v in vertices)] for i in range(3)] if vertices else [])
