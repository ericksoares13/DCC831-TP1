# DCC831-TP1 – Composição Musical Algorítmica

**Disciplina:** DCC831 – IA Generativa para Música (2026/2)  
**Aluno:** Erick Soares de Souza  
**Instituição:** Universidade Federal de Minas Gerais (UFMG)  
**Entrega:** 09/10/2026

---

## Descrição

Implementação de um sistema de geração musical simbólica baseado em **Cadeias de Markov de ordem n**, treinado sobre a voz do baixo dos **371 corais a quatro vozes (SATB) de J.S. Bach** distribuídos com a biblioteca `music21`. O sistema aprende os padrões de pitch e duração dessa voz e gera novas linhas em formato MIDI (instrumento Piano).

A restrição estilística adotada é o **estilo coral de Bach**: todas as peças de treino são normalizadas para Dó maior/Lá menor antes do aprendizado, concentrando o modelo nos contornos melódicos relativos do estilo, independente da tonalidade original de cada coral.

---

## Instalação

**Requisitos:** Python 3.9+

```bash
pip install -r requirements.txt
```

---

## Reprodução dos resultados

O dataset de corais já vem embutido no `music21` (ver seção Dataset abaixo), sem necessidade de download. Gere uma música com:

```bash
python generate.py --order 2 --temperature 1.0 --seed 42
```

O arquivo MIDI gerado vai para `output/bach_ord{order}_T{temperature}.mid`.

Principais opções (ver `python generate.py --help`):

| Flag | Padrão | Descrição |
|---|---|---|
| `--order` | 2 | Ordem da cadeia de Markov |
| `--temperature` | 1.0 | Temperatura de amostragem |
| `--seed` | — | Semente aleatória, para reprodutibilidade |
| `--length` | 200 | Número de tokens da sequência gerada |
| `--bpm` | 80 | Tempo do MIDI de saída |

A primeira execução processa os 371 corais com `music21`; um cache é salvo em `.parse_chorale_cache.pkl` e reaproveitado nas execuções seguintes.

---

## Dataset

O dataset utilizado é o conjunto de **371 corais a quatro vozes (SATB) de J.S. Bach** distribuído junto com a biblioteca `music21`, acessado via `music21.corpus`.

**Conteúdo:** cada coral tem quatro vozes anotadas (Soprano, Alto, Tenor, Baixo). Este trabalho treina apenas sobre a voz do **Baixo**, escolhida por ser a mais ativa das quatro vozes (maior salto melódico médio e maior densidade rítmica, medido sobre o dataset inteiro).

---

## Uso de IA

Ferramentas de IA foram utilizadas como apoio neste trabalho, conforme permitido pelo enunciado:

- **Claude (Anthropic)**, via **Claude for Scientists**: me ajudou a implementar o código Python (`parse_musicxml.py`, `generate.py`), a fazer a análise quantitativa dos resultados (comparação estatística entre as músicas geradas e os 371 corais reais de Bach: entropia, divergência KL, z-score) e a revisar o texto do resumo em LaTeX. As decisões de método, de projeto e a interpretação final dos resultados são minhas.
- O Claude for Scientists não deixa compartilhar conversa publicamente. Por isso, o artefato de análise (o dashboard com as métricas comparativas) está disponível aqui: https://claude.ai/artifact/2pk1nFwHq3xb6TXEDQH6Xg?sk=O5Kk39MaRL1C989ZzDShyA. Também mandei o convite de acesso pro e-mail do professor, **lferreira@dcc.ufmg.br**. Se o link expirar, é só me chamar que eu reenvio, ou a gente combina uma reunião com tela compartilhada pra ver a conversa inteira.

---

## Estrutura do repositório

```
.
├── output/                   # MIDIs gerados por generate.py (não versionado)
├── paper_templates-2026v1/   # Resumo em formato ISMIR (.tex/.pdf)
├── parse_musicxml.py         # Parser: carrega o dataset e treina a cadeia de Markov
├── generate.py               # Geração da sequência e escrita do MIDI de saída
├── requirements.txt          # Dependências Python
└── README.md
```
