"""
generate.py

Equivalente ao generate.py de Shapiro & Huber (2021): gera uma sequência
de tokens a partir do Parser treinado e escreve um MIDI, com ordem n e
temperatura em vez do order=1 fixo de S&H.

Mesmos nomes de função de S&H: find_nearest_above, generate. Divergências
marcadas com [DATASET] ou [ASSIGNMENT].
"""

import argparse
import math
import random
import sys
from pathlib import Path

import numpy as np
from music21 import stream, tempo, meter
from music21 import instrument as m21instrument
from music21.note import Note, Rest

from parse_musicxml import Parser

# [DATASET] Tessitura MIDI do piano (21 = A0, 108 = C8).
PITCH_RANGE = (21, 108)

# [ASSIGNMENT] Velocity base e pico do envelope sinusoidal (S&H usa volume=100 fixo).
DYNAMICS = (40, 100)


# ---------------------------------------------------------------------------
# find_nearest_above: idêntico a S&H (crédito: Akavall / StackOverflow)
# ---------------------------------------------------------------------------

def find_nearest_above(my_array, target):
    """Retorna o índice do menor valor em my_array > target."""
    diff = my_array - target
    mask = np.ma.less(diff, 0)
    if np.all(mask):
        return None
    masked_diff = np.ma.masked_array(diff, mask)
    return masked_diff.argmin()


def _sample_initial_token(parser):
    """
    Sorteia um token pela CDF de initial_transition_dict. Retorna None se
    o valor sorteado não encontrar índice na CDF.

    [ASSIGNMENT] Reúne num só lugar a amostragem que generate() repete em
    três pontos: estado inicial, reinício por estado sem transições e
    reinício por excesso de rests. Papel parecido ao de check_null_index()
    em S&H, que só validava o índice sem encapsular a amostragem em si.
    """
    note_prob = random.uniform(0, 1)
    index = find_nearest_above(parser.normalized_initial_transition_matrix, note_prob)
    if index is None:
        return None
    return list(parser.initial_transition_dict.keys())[index]


# ---------------------------------------------------------------------------
# generate: mesmo nome de S&H, estendido com temperatura e ordem n
# ---------------------------------------------------------------------------

def generate(seq_len, parser, temperature=1.0):
    """
    Gera uma sequência de tokens a partir do Parser treinado.

    [ASSIGNMENT] temperature reescala os pesos por 1/T antes de amostrar:
                 T < 1 é mais conservador, T > 1 mais criativo. Em T=1 o
                 comportamento é igual ao de S&H.
    [ASSIGNMENT] order n: o estado é uma janela de n tokens (S&H usa order=1).
    [ASSIGNMENT] Reinício logo abaixo quando o estado não tem sucessor;
                 em S&H isso encerra o programa com sys.exit(1).
    [DATASET]    Amostragem via random.choices(), já que o dict esparso
                 não tem índice posicional fixo como a matriz numpy de S&H.
    """
    sequence = []
    order = parser.order

    # Estado inicial via CDF (mesmo fluxo de S&H)
    init_token = _sample_initial_token(parser)
    if init_token is None:
        print("ERRO: estado inicial não encontrado na CDF inicial.")
        sys.exit(1)

    window = [init_token] * order
    sequence.extend(window)
    curr_index = order

    while curr_index < seq_len:
        state = tuple(window) if order > 1 else window[0]

        if state not in parser.transition_probability_dict:
            # Estado sem transições: reinicia a partir do dict inicial.
            # S&H encerra com sys.exit(1) via check_null_index(); aqui
            # reiniciamos para não interromper a geração em estados raros.
            init_token = _sample_initial_token(parser)
            if init_token is None:
                break
            window = [init_token] * order
            sequence.append(init_token)
        else:
            nexts = parser.transition_probability_dict[state]
            next_tokens = list(nexts.keys())
            weights = list(nexts.values())

            if temperature != 1.0:
                weights = [w ** (1.0 / temperature) for w in weights]

            next_token = random.choices(next_tokens, weights=weights, k=1)[0]

            sequence.append(next_token)
            window.pop(0)
            window.append(next_token)

        curr_index += 1

    return sequence


# ---------------------------------------------------------------------------
# Saída MIDI: usa music21 em vez de midiutil (biblioteca de S&H)
# [DATASET] midiutil suporta apenas trilha única com offsets manuais;
#           music21.stream facilita escrita e export MIDI.
# ---------------------------------------------------------------------------

def _velocity_envelope(i, total, phrase_len=8, base=40, peak=100):
    """
    [ASSIGNMENT] Envelope de dinâmica sinusoidal por frase de 8 notas
    com decaimento global de 10%. S&H usa volume=100 fixo.
    """
    phrase_pos = i % phrase_len
    phase = math.pi * phrase_pos / max(phrase_len - 1, 1)
    decay = 1.0 - 0.10 * (i / max(total - 1, 1))
    return max(30, min(127, int(base + (peak - base) * math.sin(phase) * decay)))


def _clamp_pitch(note_el, low_midi=21, high_midi=108):
    """[DATASET] Restringe o pitch à tessitura do piano, transpondo por oitavas."""
    while note_el.pitch.midi > high_midi:
        note_el.pitch.midi -= 12
    while note_el.pitch.midi < low_midi:
        note_el.pitch.midi += 12


def _token_to_element(token):
    """Converte token string em Note ou Rest do music21. 'BAR' → None."""
    if token == 'BAR':
        return None
    try:
        pitch_str, dur_str = token.rsplit(':', 1)
        dur = min(float(dur_str), 4.0) or 0.25
        if pitch_str == 'R':
            r = Rest()
            r.duration.quarterLength = dur
            return r
        n = Note(pitch_str)
        n.duration.quarterLength = dur
        return n
    except Exception:
        return None


def write_midi(sequence, output_path, bpm=120, time_sig='4/4'):
    """
    Escreve o arquivo MIDI a partir de uma sequência de tokens.

    [DATASET] Usa music21.stream.Part em vez de midiutil.MIDIFile.
    [ASSIGNMENT] Adiciona envelope de dinâmica e clamping de pitch.
    """
    low, high = PITCH_RANGE
    base, peak = DYNAMICS

    part = stream.Part()
    part.insert(0, m21instrument.Piano())
    part.insert(0, meter.TimeSignature(time_sig))

    elements = [_token_to_element(t) for t in sequence]
    elements = [e for e in elements if e is not None]

    total_notes = sum(1 for e in elements if isinstance(e, Note))
    note_i = 0
    for el in elements:
        if isinstance(el, Note):
            _clamp_pitch(el, low, high)
            el.volume.velocity = _velocity_envelope(note_i, total_notes,
                                                     base=base, peak=peak)
            note_i += 1
        part.append(el)

    s = stream.Score()
    s.insert(0, tempo.MetronomeMark(number=bpm))
    s.append(part)
    s.write('midi', fp=str(output_path))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description='Gerador de melodias no estilo coral de Bach com Markov de ordem n')
    p.add_argument('--order',       type=int,   default=2)
    p.add_argument('--length',      type=int,   default=200)
    p.add_argument('--bpm',         type=int,   default=80)
    p.add_argument('--temperature', type=float, default=1.0,
                   help='[ASSIGNMENT] Temperatura de amostragem (1.0 = sem alteração)')
    p.add_argument('--seed',        type=int,   default=None)
    return p.parse_args()


def main():
    args = parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    print(f"\n=== Carregando dataset de corais de Bach ===")
    parser = Parser(order=args.order)

    if not parser.states:
        print("Nenhuma sequência carregada.")
        sys.exit(1)

    tag = f"bach_ord{args.order}_T{args.temperature}"
    print(f"\n=== Gerando música (ordem={args.order}, T={args.temperature}) ===")

    sequence = generate(args.length, parser, temperature=args.temperature)
    fname = output_dir / f"{tag}.mid"
    write_midi(sequence, fname, bpm=args.bpm)
    print(f"  {fname.name}")

    print("\nPronto!")


if __name__ == '__main__':
    main()
