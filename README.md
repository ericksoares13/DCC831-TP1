# DCC831-TP1 – Composição Musical Algorítmica

**Disciplina:** DCC831 – IA Generativa para Música (2026/2)  
**Aluno:** Erick Soares de Souza  
**Instituição:** Universidade Federal de Minas Gerais (UFMG)  
**Entrega:** 09/10/2026

---

## Descrição

Implementação de um sistema de geração musical simbólica baseado em **Cadeias de Markov**, treinado sobre um corpus de músicas de Taylor Swift. O sistema aprende progressões de acordes características do estilo da artista e gera novas sequências harmônicas, produzindo arquivos MIDI reproduzíveis.

A restrição estilística adotada é o **estilo de Taylor Swift**, usando sua discografia (2006–2023) como corpus de treinamento.

---

## Instalação

**Requisitos:** Python 3.9+

```bash
pip install -r requirements.txt
```

---

## Reprodução dos resultados

N/A

---

## Dataset

Os arquivos MIDI do corpus **não estão incluídos** neste repositório por questões de direitos autorais. As transcrições foram obtidas manualmente em: https://freemidi.org/artist-1599-taylor-swift

Para reproduzir os resultados, baixe os arquivos abaixo e coloque-os na pasta `dataset/`:

| Arquivo | Álbum |
|---|---|
| 22.mid | Red (2012) |
| BackToDecember.mid | Speak Now (2010) |
| BadBlood.mid | 1989 (2014) |
| BeginAgain.mid | Red (2012) |
| BetterThanRevenge(TaylorsVersion).mid | Speak Now (TV) (2023) |
| BlankSpace.mid | 1989 (2014) |
| Fearless.mid | Fearless (2008) |
| Fifteen.mid | Fearless (2008) |
| IsItOverNow.mid | 1989 (TV) (2023) |
| Knewyouweretrouble.mid | Red (2012) |
| LongLive.mid | Speak Now (2010) |
| LookWhatYouMadeMeDo.mid | Reputation (2017) |
| LoveStory.mid | Fearless (2008) |
| MarysSong.mid | Taylor Swift (2006) |
| mean.mid | Speak Now (2010) |
| Mine.mid | Speak Now (2010) |
| NeverGrowUp.mid | Speak Now (2010) |
| Opalite.mid | The Life of a Showgirl (2025) |
| OurSong.mid | Taylor Swift (2006) |
| picturetoburn.mid | Taylor Swift (2006) |
| Red.mid | Red (2012) |
| SafeandSound.mid | The Hunger Games (2012) |
| ShakeItOff.mid | 1989 (2014) |
| sparksfly.mid | Speak Now (2010) |
| SpeakNow.mid | Speak Now (2010) |
| Style.mid | 1989 (2014) |
| TeardropsOnMyGuitar.mid | Taylor Swift (2006) |
| TheFateofOphelia.mid | The Life of a Showgirl (2025) |
| TimMcGraw.mid | Taylor Swift (2006) |
| Weareneverevergettingbacktogether.mid | Red (2012) |
| WhiteHorse.mid | Fearless (2008) |
| YouBelongWithMe.mid | Fearless (2008) |
| YoureNotSorry.mid | Fearless (2008) |

---

## Uso de IA

Ferramentas de IA foram utilizadas como apoio neste trabalho, conforme permitido pelo enunciado:

N/A

---

## Estrutura do repositório

```
.
├── dataset/                  # Arquivos MIDI do corpus (não versionados – ver Dataset acima)
├── paper_templates-2026v1/   # Template LaTeX ISMIR
├── requirements.txt          # Dependências Python
└── README.md
```
