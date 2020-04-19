#!/usr/bin/env python

from fractions import Fraction
from reader import Measure

# enable some Features
ISBASS = False
ISCHORD = False

# define the bass part is at the 3rd line
BASS_PART = 3
CHORD_PART = 4
PAGE_PER_COLUMN = 4
MAX_MEASURES_PER_LINE = 5
IS_FLAT_TO_SHARP = True

accidentList = [[['']*8 for i in range(8)]]

crossMeasureTie = False
preNoteGrace = ""
graceFlag = False

STEP_TO_NUMBER = {
    'C': 1,
    'D': 2,
    'E': 3,
    'F': 4,
    'G': 5,
    'A': 6,
    'B': 7
}

def stepToNumber(step):
    return str(STEP_TO_NUMBER[step])

def stepToNumberFlat(step):
    if STEP_TO_NUMBER[step] == 1:
        return "7"
    return str(STEP_TO_NUMBER[step] - 1)

def generateOctaveMark(octave):
    global ISBASS
    if ISBASS:
        center_C = 4
    else:
        center_C = 5

    if octave >= center_C:
        return "'" * (octave - center_C)
    else:
        return "," * (center_C - octave)

def generateTimeSuffix(duration, divisions):
    note_length = Fraction(duration, divisions)
    if duration < divisions: # less than quarter notes: add / and continue
        return generateTimeSuffix(duration*2, divisions) + "/"
    elif duration == divisions: # quarter notes
        return ""
    elif duration * 2 == divisions * 3: # syncopated notes
        return "."
    else: # sustained more than 1.5 quarter notes: add - and continue
        return " -" + generateTimeSuffix(duration - divisions, divisions)

def generateHeader(reader):
    title = reader.getWorkTitle()
    key = reader.getInitialKeySignature().replace('b', '$') # flat is represented by '$' in this format
    time = reader.getInitialTimeSignature()

    header = "V: 1.0\n" # jianpu99 version number
    if title:
        header += "B: %s\n" % title
    header += "D: %s\n" % key
    header += "P: %s\n" % time

    composer = reader.getComposer()
    if composer:
        header += "Z: %s\n" % composer
    return header

def getNoteDisplayedDuration(note):
    if note.isTuplet():
        return note.getDisplayedDuration()
    else:
        return note.getDuration()

NOTE_DEGREE_TABLE = {
    'C': 0, 'B#': 0,
    'C#': 1, 'Db': 1,
    'D': 2,
    'D#': 3, 'Eb': 3,
    'E': 4, 'Fb': 4,
    'F': 5, 'E#': 5,
    'F#': 6, 'Gb': 6,
    'G': 7,
    'G#': 8, 'Ab': 8,
    'A': 9,
    'A#': 10, 'Bb': 10,
    'B': 11, 'Cb': 11
}


ACCIDENTAL_TABLE = {
    'C':  ('#', []),
    'G':  ('#', ['F']),
    'D':  ('#', ['F', 'C']),
    'A':  ('#', ['F', 'C', 'G']),
    'E':  ('#', ['F', 'C', 'G', 'D']),
    'B':  ('#', ['F', 'C', 'G', 'D', 'A']),
    'F#': ('#', ['F', 'C', 'G', 'D', 'A', 'E']),
    'F':  ('b', ['B']),
    'Bb': ('b', ['B', 'E']),
    'Eb': ('b', ['B', 'E', 'A']),
    'Ab': ('b', ['B', 'E', 'A', 'D']),
    'Db': ('b', ['B', 'E', 'A', 'D', 'G']),
    'Gb': ('b', ['B', 'E', 'A', 'D', 'G', 'C']),
}

DEGREE_NOTE_TABLE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def getTransposedPitch(note_name, octave, offset):
    degree = NOTE_DEGREE_TABLE[note_name]
    transposed_degree = degree + offset
    transposed_octave = octave + transposed_degree // 12
    transposed_degree %= 12
    return (DEGREE_NOTE_TABLE[transposed_degree], transposed_octave)

def getTransposeOffsetToC(key):
    degree = NOTE_DEGREE_TABLE[key]
    if degree <= 6:
        return -degree
    else:
        return 12 - degree

def generateBasicNote(note, isGrace):
    global accidentList
    time_suffix = ""
    if not isGrace:
        (duration, divisions) = getNoteDisplayedDuration(note)
        time_suffix = generateTimeSuffix(duration, divisions)

    # Turn flat into all sharp
    if note.isRest():
        return "0" + time_suffix
    elif ISCHORD:
        if note.isNoteChord():
            return ""
        return "9" + time_suffix
    else:
        pitch = note.getPitch()
        (note_name, octave) = note.getPitch()

        keysig = note.getAttributes().getKeySignature()

        step = note_name[0:1] # C, D, E, F, G, A, B
        accidental = note_name[1:2] # sharp (#) and flat (b)
        force_accidental = note_name[2:3] # additonal sharp and flat and natural

        key_accidental_char, key_accidental_list = ACCIDENTAL_TABLE[keysig]

        if step in key_accidental_list:
            if force_accidental != "":
                accidentList[STEP_TO_NUMBER[step]][octave] = accidental
            elif accidentList[STEP_TO_NUMBER[step]][octave] == '=':
                accidental = '='
            accidentList[STEP_TO_NUMBER[step]][octave] = accidental

        elif accidental == "":
            preNote = STEP_TO_NUMBER[step] + 1
            if preNote == 8:
                preNote = 1
            if accidentList[preNote][octave] == 'b' and IS_FLAT_TO_SHARP and accidentList[STEP_TO_NUMBER[step]][octave] == '':
                accidental = '='
                accidentList[STEP_TO_NUMBER[step]][octave] = accidental
            else:
                accidental = accidentList[STEP_TO_NUMBER[step]][octave]
        else:
            accidentList[STEP_TO_NUMBER[step]][octave] = accidental

        if accidental == 'b' and IS_FLAT_TO_SHARP:
            if step == 'C':
                return stepToNumberFlat(step) + generateOctaveMark(octave - 1) + time_suffix
            elif step == 'F':
                return stepToNumberFlat(step) + generateOctaveMark(octave) + time_suffix
            accidental = '#'
            return stepToNumberFlat(step) + accidental + generateOctaveMark(octave) + time_suffix
        else:
            return stepToNumber(step) + accidental + generateOctaveMark(octave) + time_suffix

def generateNote(note):
    global crossMeasureTie
    global preNoteGrace
    global graceFlag
    isGrace = False

    if note.isGrace():
        isGrace = True

    result = generateBasicNote(note, isGrace)
    if graceFlag:
        if '-' in result:
            idx = result.index('-')
            result = result[:idx - 1] + preNoteGrace + result[idx:]
        else:
            result = result + preNoteGrace
        graceFlag = False
    if note.isGrace():
        preNoteGrace = " [" + result + "] "
        graceFlag = True
        result = ""
    if note.isTieStart():
        result = "( " + result
        crossMeasureTie = True
    if note.isTupletStart():
        result = "(y" + result
    if note.isTupletStop():
        result = result + ")"
    if note.isTieStop():
        accidentList = [['']*8 for i in range(8)]
        crossMeasureTie = False
        if '-' in result: # put ending tie before the first -
            idx = result.index('-')
            result = result[:idx] + ") " + result[idx:]
        else:
            result = result + " )"
    return result

def generateMeasure(measure):
    global accidentList
    global crossMeasureTie

    if not crossMeasureTie:
        accidentList = [['']*8 for i in range(8)]
    
    pieces = []
    harmonyArr = []
    noteNum = 0
    
    for note in measure:
        if note.getElemTag() == "harmony":
            harmonyArr.append(note.getHarmony() + [noteNum])
            continue
        if not note.isNoteChord():
            noteNum += 1
        pieces.append(generateNote(note))
    return ' '.join(pieces), noteNum, harmonyArr

def generateRightBarline(measure):
    if measure.getRightBarlineType() == Measure.BARLINE_REPEAT:
        return ":|"
    elif measure.getRightBarlineType() == Measure.BARLINE_DOUBLE:
        return "||/"
    elif measure.getRightBarlineType() == Measure.BARLINE_FINAL:
        return "||"
    else:
        return "|"

def generateMeasures(measureList):
    pieces = []
    noteNumList = []
    harmonyArrList = []
    for i, measure in enumerate(measureList):
        if measure.getLeftBarlineType() == Measure.BARLINE_REPEAT:  # see left
            if i == 0:
                # pieces.append("|:")
                pieces.append(":")
            else:
                pieces.append(":")
        line, noteNum, harmonyArr = generateMeasure(measure)
        harmonyArrList.append(harmonyArr)
        noteNumList.append(noteNum)

        pieces.append(" ")                              
        pieces.append(line)             # see content
        pieces.append(" ")
        pieces.append(generateRightBarline(measure))                # see right

    return ''.join(pieces), noteNumList, harmonyArrList

def generateChordHarmony(noteNumList, harmonyArrList):
    pieces = []
    last_space = 0
    for idx, measure in enumerate(harmonyArrList):
        pre_idx = -1
        if measure == []:
            pieces.append("@")
        else:
            for note in measure:
                last_space = note[1]
                pieces.append('@' * (note[1] - pre_idx - 1))
                pieces.append(note[0])
                pre_idx = note[1]
        pieces.append('@' * (noteNumList[idx] - last_space - 1))

    return "".join(pieces)

def generateBody(reader):

    global accidentList
    parts = reader.getPartIdList()

    part_measures = dict()
    for part in parts:
        part_measures[part] = list(reader.iterMeasures(part))

    lines = []
    column_now = 0

    measure_count = max(len(measures) for measures in part_measures.values())
    for i in range(0, measure_count, MAX_MEASURES_PER_LINE):
        begin = i
        end = min(i + MAX_MEASURES_PER_LINE, measure_count)
        for part_index, part in enumerate(parts):
            accidentList = [['']*8 for i in range(8)]
            if part_index + 1 == BASS_PART:
                global ISBASS
                ISBASS = True
                line = "Q%d: |" % (part_index + 1)
                line += generateMeasures(part_measures[part][begin:end])[0]   # enter bass part
                ISBASS = False
            elif part_index + 1 == CHORD_PART: 
                global ISCHORD
                ISCHORD = True
                line = "Q%d: |" % (part_index + 1)
                return_line, noteNumList, harmonyArrList = generateMeasures(part_measures[part][begin:end])
                line += return_line + "\n"
                line += "C: "
                line += generateChordHarmony(noteNumList, harmonyArrList)
                ISCHORD = False
            else:
                line = "Q%d: |" % (part_index + 1)
                line += generateMeasures(part_measures[part][begin:end])[0]   # other part
            lines.append(line)
        lines.append('') # empty line
        column_now = column_now + 1

        if column_now == PAGE_PER_COLUMN:       # per page column
            lines.append('[fenye]')
            lines.append('')
            column_now = 0

    return '\n'.join(lines)

class WriterError(Exception):
    pass

class Jianpu99Writer:

    def generate(self, reader):
        return generateHeader(reader) + "\n" + generateBody(reader)
