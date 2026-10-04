"""
parse_musicxml.py

Mesmo nome e mesma ideia do parse_musicxml.py original de Shapiro & Huber
(2021), mas lendo partituras com music21 em vez de MusicXML na mão, e
treinando uma Cadeia de Markov de ordem n sobre todo o dataset de corais
de Bach, em vez de uma música só.

Divergências marcadas com [DATASET] (decisão ligada ao dataset de corais)
ou [ASSIGNMENT] (extensão pedida no TP, como a ordem n).
"""

import collections
import pickle
from pathlib import Path

import numpy as np
from music21 import corpus, interval
from music21 import pitch as m21pitch
from music21.chord import Chord
from music21.note import Note, Rest

# [DATASET] Voz treinada nos corais a quatro vozes (SATB) de Bach.
CHORALE_VOICE = 'BASS'

# [DATASET] Cache pickle para evitar reprocessar os 371 corais a cada execução.
_CACHE_FILE = Path('.parse_chorale_cache.pkl')

# [ASSIGNMENT] Pausa usada para fechar o ciclo de cada música em Parser._close_loop,
# equivalente ao ('R', 'quarter') de wraparound do parse_musicxml.py original de S&H.
_CLOSE_REST_TOKEN = 'R:1.0'


# ---------------------------------------------------------------------------
# Funções auxiliares internas
# ---------------------------------------------------------------------------

def _quantize_duration(dur, grid=0.25):
    """
    [DATASET] No S&H a duração é um texto fixo ("quarter", "eighth"...).
    Aqui o music21 já devolve um número, mas a duração real às vezes não
    cai certinho na grade (0.2483 em vez de 0.25). Arredondar evita que
    notas do mesmo tamanho virem estados diferentes na cadeia.
    """
    if dur <= 0:
        return grid
    return round(round(dur / grid) * grid, 4)


def _normalize_to_c(score):
    """
    [DATASET] Detecta a tonalidade e transpõe pelo caminho mais curto até
    Dó maior (ou Lá menor, se for modo menor). Assim todos os corais do
    dataset usam o mesmo vocabulário de notas, independente da tonalidade
    original.
    """
    try:
        key = score.analyze('key')
        target = m21pitch.Pitch('C') if key.mode == 'major' else m21pitch.Pitch('A')
        semitones = interval.Interval(key.tonic, target).semitones
        if semitones > 6:
            semitones -= 12
        elif semitones < -6:
            semitones += 12
        return score.transpose(semitones)
    except Exception:
        return score


def _track_name_from_part(part):
    """
    [DATASET] Lê o nome da voz (ex: 'Soprano', 'Alto') de uma Part de
    coral, usado depois para decidir se ela entra no treino.
    """
    try:
        name = (part.partName or part.id or '').strip().upper()
        return name
    except Exception:
        return ''


def _part_to_sound_objects(part):
    """
    Converte uma Part do music21 (uma voz) em tokens para a cadeia de
    Markov.

    [DATASET] Cada nota vira "G4:1.0" (pitch:duração), em vez da tupla
    ("G4", "quarter") de S&H. Acordes viram só a nota mais aguda; na
    prática quase não acontecem na voz treinada, que é só uma linha.
    [ASSIGNMENT] O token 'BAR' marca o início de cada compasso.
    """
    tokens = []
    for measure in part.getElementsByClass('Measure'):
        tokens.append('BAR')
        for el in measure.notesAndRests:
            dur = _quantize_duration(el.duration.quarterLength)
            if dur < 0.125:
                continue
            if isinstance(el, Rest):
                tokens.append(f"R:{dur}")
            elif isinstance(el, Note):
                tokens.append(f"{el.nameWithOctave}:{dur}")
            elif isinstance(el, Chord):
                top = sorted(el.notes, key=lambda n: n.pitch.midi)[-1]
                tokens.append(f"{top.nameWithOctave}:{dur}")
    return tokens


# ---------------------------------------------------------------------------
# Helpers de leitura do dataset de corais (usados por Parser.parse)
# ---------------------------------------------------------------------------

def _bach_chorale_ids():
    """
    [DATASET] Lista os identificadores dos 371 corais a quatro vozes de
    Bach já embutidos no music21 (ex: 'bach/bwv269').
    """
    return sorted(corpus.chorales.Iterator(returnType='filename'))


def _parse_bach_chorale(chorale_id):
    """
    [DATASET] Abre um coral pelo identificador do dataset, normaliza a
    tonalidade e devolve os tokens da voz do baixo.
    """
    try:
        score = corpus.parse(chorale_id)
        if not score.parts:
            return []
        score = _normalize_to_c(score)

        voice = None
        for part in score.parts:
            if _track_name_from_part(part).startswith(CHORALE_VOICE):
                voice = part
                break
        if voice is None and len(score.parts) == 4:
            voice = score.parts[-1]
        if voice is None:
            return []

        tokens = _part_to_sound_objects(voice)
        return [tokens] if len(tokens) > 4 else []
    except Exception as e:
        print(f"    [ERRO] {chorale_id}: {e}")
        return []


# ---------------------------------------------------------------------------
# Classe Parser: análoga direta de parse_musicxml.Parser (S&H)
# ---------------------------------------------------------------------------

class Parser:
    """
    Equivalente ao parse_musicxml.Parser de Shapiro & Huber (2021): lê
    música, conta transições nota a nota e normaliza tudo em probabilidades.

    Atributos com os mesmos nomes de S&H: states, initial_transition_dict,
    normalized_initial_transition_matrix, transition_probability_dict.

    [ASSIGNMENT] order: ordem da cadeia (S&H é sempre ordem 1; único
                 parâmetro que este TP varia de verdade).
    [DATASET]    S&H recebe um filename e treina sobre uma única música;
                 Parser() já nasce treinado sobre os 371 corais de Bach,
                 sempre com normalização tonal e cache em disco.
    """

    def __init__(self, order=1):
        self.initial_transition_dict = collections.OrderedDict()
        self.normalized_initial_transition_matrix = None

        self.transition_probability_dict = collections.OrderedDict()

        self.states = []

        self.order = order              # [ASSIGNMENT]
        self.parse()

    def parse(self):
        """
        Lê o dataset de corais inteiro e alimenta transition_probability_dict/states.

        [DATASET] S&H parseia um arquivo só, direto. Aqui agregamos os
        371 corais, com cache em pickle para não reabrir tudo a cada
        execução. build_matrices() roda uma vez só, ao final, sobre o
        total acumulado.
        """
        chorale_ids = _bach_chorale_ids()

        cache: dict = {}
        if _CACHE_FILE.exists():
            try:
                with open(_CACHE_FILE, 'rb') as f:
                    cache = pickle.load(f)
            except Exception:
                cache = {}

        new_entries = 0
        for i, chorale_id in enumerate(chorale_ids):
            if chorale_id in cache:
                all_tokens = cache[chorale_id]
            else:
                if i % 25 == 0:
                    print(f"  Processando {i+1}/{len(chorale_ids)}...", flush=True)
                all_tokens = _parse_bach_chorale(chorale_id)
                cache[chorale_id] = all_tokens
                new_entries += 1

            for tokens in all_tokens:
                self._feed(tokens)
                self._close_loop(tokens)

        if new_entries > 0:
            with open(_CACHE_FILE, 'wb') as f:
                pickle.dump(cache, f)

        self.build_matrices()

        print(f"  Parser [Baixo]: {len(self.states)} estados | "
              f"{len(self.transition_probability_dict)} chaves de transição")

    def handle_insertion(self, prev_state, curr_state):
        """
        Registra curr_state em states/initial_transition_dict e, se houver
        um estado anterior, chama insert() pra contar a transição
        prev_state -> curr_state.

        [ASSIGNMENT] Pra ordem > 1, prev_state é uma tupla com os últimos
        `order` tokens, não um token só.
        """
        if curr_state is None:
            return

        if curr_state not in self.states:
            self.states.append(curr_state)

        if curr_state in self.initial_transition_dict:
            self.initial_transition_dict[curr_state] += 1
        else:
            self.initial_transition_dict[curr_state] = 1

        if prev_state is not None:
            self.insert(self.transition_probability_dict, prev_state, curr_state)

    def insert(self, d, value1, value2):
        """Soma 1 na contagem da transição value1 -> value2 dentro do dicionário d."""
        if value1 in d:
            if value2 in d[value1]:
                d[value1][value2] += 1
            else:
                d[value1][value2] = 1
        else:
            d[value1] = {value2: 1}

    def build_matrices(self):
        """Normaliza as contagens acumuladas: primeiro as transições, depois os estados iniciais."""
        self.build_normalized_transition_probability_matrix()
        self.build_normalized_initial_transition_matrix()

    def build_normalized_initial_transition_matrix(self):
        """Transforma as contagens de initial_transition_dict numa CDF, usada em generate() para sortear o primeiro token."""
        arr = np.array(list(self.initial_transition_dict.values()), dtype=float)
        arr /= arr.sum()
        self.normalized_initial_transition_matrix = np.cumsum(arr)

    def build_normalized_transition_probability_matrix(self):
        """
        Transforma as contagens de transition_probability_dict em
        probabilidades: cada estado passa a somar 1 entre seus sucessores.

        [DATASET] S&H guarda isso como matriz NxN densa, viável com ~50
        estados. Aqui mantemos o mesmo dict esparso independente da
        escala do dataset (a cadeia tem algumas centenas de estados em
        ordem 1, e alguns milhares em ordem 3). A amostragem,
        que em S&H usa find_nearest_above() sobre a matriz, vira
        random.choices() em generate(), equivalente para T=1.
        """
        for state in self.transition_probability_dict:
            nexts = self.transition_probability_dict[state]
            total = sum(nexts.values())
            self.transition_probability_dict[state] = {
                k: v / total for k, v in nexts.items()
            }

    def _feed(self, sound_objects):
        """
        Percorre os tokens de uma música e chama handle_insertion() pra
        cada par (estado anterior -> token atual), construindo as
        contagens de transição internas dela.

        [ASSIGNMENT] Pra ordem 1, o estado anterior é só o token anterior;
        pra ordem n > 1, é uma janela com os últimos n tokens.
        """
        for i, so in enumerate(sound_objects):
            if self.order == 1:
                prev_state = sound_objects[i - 1] if i > 0 else None
            else:
                prev_state = (tuple(sound_objects[i - self.order:i])
                              if i >= self.order else None)
            self.handle_insertion(prev_state, so)

    def _close_loop(self, sound_objects):
        """
        Fecha o ciclo da música: a última janela de `order` tokens aponta
        pra uma pausa de fechamento, que por sua vez aponta de volta pro
        primeiro token da música.

        [ASSIGNMENT] É a generalização pra ordem n do wraparound final do
        parse_musicxml.py original de S&H (última nota -> pausa -> primeiro
        som da peça). Garante que o último estado de cada música sempre
        tenha uma transição de saída, em vez de depender do reinício em
        generate() quando um estado não tem sucessor.
        """
        if not sound_objects:
            return

        extended = sound_objects + [_CLOSE_REST_TOKEN, sound_objects[0]]
        for i in (len(sound_objects), len(sound_objects) + 1):
            curr = extended[i]
            if self.order == 1:
                prev_state = extended[i - 1]
            else:
                prev_state = (tuple(extended[i - self.order:i])
                              if i >= self.order else None)
            self.handle_insertion(prev_state, curr)
